import logging
import json
import re
from typing import Optional, Dict, List, Any

from app.services.ai_service import ai_service
from app.config import settings

logger = logging.getLogger("architect")

# ---------------------------------------------------------------------------
# SYSTEM PROMPT — Core rules for every LLM call
# ---------------------------------------------------------------------------

ARCHITECT_SYSTEM_PROMPT = """You are the Architect Agent of the RLForge platform.
Your sole purpose is to generate, fix, and iterate on Reinforcement Learning
environments that are fully compatible with Gymnasium v0.29+.

=== GYMNASIUM COMPATIBILITY RULES ===
1. Every environment MUST subclass gymnasium.Env.
2. Required imports: gymnasium, numpy. Use `import gymnasium as gym` and
   `import numpy as np`.
3. Required methods with EXACT signatures:
   - __init__(self, render_mode: str | None = None)
   - step(self, action) -> tuple[np.ndarray, float, bool, bool, dict]
   - reset(self, *, seed: int | None = None, options: dict | None = None) -> tuple[np.ndarray, dict]
   - close(self) -> None
4. step() MUST return exactly five values: (observation, reward, terminated, truncated, info).
   - observation: np.ndarray matching self.observation_space
   - reward: float (np.float32)
   - terminated: bool — episode ended due to environment rules (goal, failure)
   - truncated: bool — episode ended due to time limit
   - info: dict with at least reward component breakdown
5. reset() MUST:
   - Accept seed as keyword-only argument
   - Call super().reset(seed=seed) FIRST
   - Initialise self.np_random via super().reset (do NOT create your own Generator
     unless you seed it from self.np_random)
   - Return (observation, info)
6. observation_space and action_space MUST be set in __init__ using gymnasium.spaces
   (Box, Discrete, MultiDiscrete, MultiBinary, Dict, Tuple).
7. render_mode should be stored and respected. render() is optional but recommended.

=== NUMPY / RANDOMNESS RULES ===
1. ALL numeric arrays MUST be np.float32.
2. Use self.np_random (np.random.Generator) for ALL stochastic operations.
   NEVER use np.random.seed, np.random.rand, random.random, or any legacy API.
3. self.np_random is automatically set by super().reset(seed=seed).

=== CODE QUALITY RULES ===
1. Add type hints to every method signature.
2. Write a class-level docstring describing the environment, its observation space,
   action space, and reward structure.
3. Define ALL constants as class-level attributes (no magic numbers in methods).
4. Handle edge cases: clip NaN/Inf to finite bounds, clamp out-of-bounds actions,
   guard against division by zero.
5. The environment MUST be deterministic given the same seed.

=== REWARD FUNCTION RULES ===
1. Clip final reward to the range [-10.0, 10.0].
2. Prefer dense rewards over sparse rewards.
3. Negative rewards should be proportional to positive rewards in magnitude.
4. Include reward-hacking countermeasures where applicable (e.g. action penalties,
   novelty bonuses, curriculum bounds).
5. Write every reward component into the info dict for debugging:
   info["reward_components"] = {"goal": 1.0, "penalty": -0.2, ...}

=== OBSERVATION SPACE RULES ===
1. Normalise ALL observation values to [-1, 1] or [0, 1].
2. Include ONLY information the agent needs for decision-making.
3. Use gymnasium.spaces.Box with explicit low, high, shape, and dtype=np.float32.

=== ACTION SPACE RULES ===
1. Discrete: finite choices (e.g. buy/sell/hold).
2. Box: continuous values (e.g. portfolio weights, torques).
3. Internally clamp or project invalid actions to valid range — never raise on
   out-of-bounds actions.

=== OUTPUT FORMAT ===
Output ONLY valid Python source code.
Do NOT include markdown fences, explanations, or commentary.
The code must be runnable as-is with `import gymnasium` and `import numpy`.
Include all necessary imports at the top of the file.
"""

# ---------------------------------------------------------------------------
# LAYER 1 — Built-in domain skill prompts
# ---------------------------------------------------------------------------

DOMAIN_SKILLS: Dict[str, str] = {
    "finance": """=== FINANCE DOMAIN SKILL ===

OBSERVATION SPACE:
- Include OHLCV (Open, High, Low, Close, Volume) for each asset, normalised
  to [0, 1] via min-max over a rolling window.
- Include portfolio weights (current allocation per asset), cash ratio.
- Include technical indicators when specified: RSI, MACD, Bollinger %B,
  all normalised to [-1, 1].
- Shape hint: (n_assets * n_features + n_assets + 1,)

ACTION SPACE:
- Continuous Box [-1, 1] with shape (n_assets,). Values represent target
  portfolio weight deltas. Internally softmax or clip to ensure weights
  sum to <= 1.0 and each weight is in [0, 1].
- Alternative Discrete(3) per asset: 0=hold, 1=buy, 2=sell (for simple envs).

REWARD FUNCTION:
- Primary: portfolio log-return at each step.
- Penalise transaction costs: -commission * turnover.
- Penalise risk: optional Sharpe-ratio component or drawdown penalty.
- Clip to [-10, 10]. Provide info["reward_components"] with keys:
  "return", "commission_cost", "risk_penalty".

EPISODE CONFIGURATION:
- Default max_steps = 252 (one trading year).
- terminated = True if portfolio value <= 0 (bankruptcy).
- truncated = True if step >= max_steps.
- Reset: randomise start date within historical window if data-driven,
  or re-sample synthetic price paths.

EDGE CASES:
- Clamp portfolio weights so no single asset exceeds 1.0 and total <= 1.0.
- Guard against zero-volume days (skip or impute).
- Handle NaN in price data by forward-filling or raising early termination.
""",

    "game": """=== GAME / GRID-WORLD DOMAIN SKILL ===

OBSERVATION SPACE:
- Grid-based: flatten or use 2D Box. Include agent position, goal position,
  obstacle map. Normalise coordinates to [0, 1] by dividing by grid_size.
- Full observability: provide entire grid state.
- Partial observability: provide local window around agent.
- Shape hint: (grid_h * grid_w * n_channels,) for flat, or use Dict space.

ACTION SPACE:
- Discrete(4) for cardinal movement: 0=up, 1=right, 2=down, 3=left.
- Discrete(8) for 8-directional (add diagonals).
- Discrete(5) or more if actions include stay/interact.
- Invalid moves (wall collision) should be no-ops, not errors.

REWARD FUNCTION:
- Sparse: +1.0 for reaching goal, 0 otherwise.
- Dense alternative: -step_cost per step + distance_reduction bonus.
- Collision penalty: -0.5 for hitting wall/obstacle.
- Provide info["reward_components"]: "goal", "step_cost", "collision".

EPISODE CONFIGURATION:
- Default max_steps = grid_h * grid_w * 2 (enough to traverse).
- terminated = True when agent reaches goal or falls into trap.
- truncated = True when step >= max_steps.
- Reset: randomise agent start, goal, and obstacles with seed.

EDGE CASES:
- Boundary wrapping vs blocking: decide and document.
- Ensure goal is always reachable (BFS check in reset, or guarantee by
  construction).
- Handle simultaneous multi-agent if needed (future).
""",

    "control": """=== CONTROL / CONTINUOUS-CONTROL DOMAIN SKILL ===

OBSERVATION SPACE:
- Include joint angles, joint angular velocities, end-effector position,
  target position. All normalised to [-1, 1].
- For vehicles: position (x, y), heading angle (sin, cos), velocity,
  angular velocity.
- Shape hint: (2 * n_joints + n_target_dims,)

ACTION SPACE:
- Continuous Box [-1, 1] with shape (n_actuators,). Map to actual torque
  range internally: torque = action * max_torque.
- Clamp actions that exceed [-1, 1] silently.

REWARD FUNCTION:
- Primary: negative distance to target (dense).
- Control cost: -alpha * sum(action^2) to penalise excessive torque.
- Stability bonus: +beta if angular velocity stays below threshold.
- Alive bonus: small positive reward per step if not fallen/failed.
- Clip to [-10, 10]. info["reward_components"]: "distance", "control_cost",
  "stability", "alive".

EPISODE CONFIGURATION:
- Physics dt = 0.02 (50 Hz). max_steps = 1000 (20 seconds).
- terminated = True if system falls, diverges, or reaches goal.
- truncated = True if step >= max_steps.

EDGE CASES:
- Detect NaN/Inf in state after dynamics step; terminate early.
- Clamp state to physical bounds after integration.
- Use semi-implicit Euler or RK4 for stability; avoid explicit Euler alone.
""",

    "optimization": """=== OPTIMIZATION / RESOURCE-ALLOCATION DOMAIN SKILL ===

OBSERVATION SPACE:
- Current resource levels (inventory, capacity, queue lengths),
  normalised to [0, 1] by max capacity.
- Demand forecast or recent demand history.
- Time features: step / max_steps, day-of-week encoding.
- Constraint utilisation ratios: current_usage / max_capacity.

ACTION SPACE:
- Continuous Box [0, 1] shape (n_resources,). Represents allocation
  fractions. Internally scale to actual quantities.
- Alternative Discrete(n_options) for combinatorial choices.
- Clamp total allocation to available budget/capacity.

REWARD FUNCTION:
- Primary: throughput, revenue, or objective function value.
- Penalty: constraint violations * large multiplier (soft constraint).
- Penalty: waste or idle resources * small multiplier.
- info["reward_components"]: "throughput", "violation_penalty",
  "waste_penalty".

EPISODE CONFIGURATION:
- max_steps depends on horizon (e.g. 365 for yearly planning, 100 for
  scheduling).
- terminated = True if hard constraint violated (system failure).
- truncated = True if step >= max_steps.

EDGE CASES:
- Ensure resource levels never go negative (clamp to 0).
- Handle demand spikes that exceed all capacity gracefully.
- Guard against degenerate solutions (all-zero allocation).
""",

    "robotics": """=== ROBOTICS DOMAIN SKILL ===

OBSERVATION SPACE:
- Proprioceptive: joint positions, velocities, accelerations.
- Exteroceptive: LIDAR distances, camera features, contact booleans.
- Task-specific: target position, object pose.
- All normalised to [-1, 1]. dtype=np.float32.
- Shape hint: (n_joints * 2 + n_sensors + n_task_dims,)

ACTION SPACE:
- Continuous Box [-1, 1] shape (n_motors,). Map to torque or velocity
  commands: cmd = action * max_cmd.
- Consider action rate limiting: delta_action = clip(action - prev_action,
  -max_delta, max_delta) for smoother control.

REWARD FUNCTION:
- Task completion: large bonus when objective achieved.
- Progress: dense reward proportional to distance reduction to target.
- Energy efficiency: -gamma * sum(action^2).
- Safety: -large_penalty for collisions, joint limit violations, or
  excessive force.
- info["reward_components"]: "task", "progress", "energy", "safety".

EPISODE CONFIGURATION:
- Physics dt = 0.01 to 0.02. max_steps = 500 to 2000.
- terminated = True on task success, collision, or joint-limit violation.
- truncated = True if step >= max_steps.

EDGE CASES:
- Self-collision detection if applicable.
- Joint position and velocity limits must be enforced every step.
- Detect and handle singularities in kinematics.
- Gravity and friction must be physically plausible.
""",
}

# ---------------------------------------------------------------------------
# LAYER 2 — Dynamic skill generation prompt
# ---------------------------------------------------------------------------

DYNAMIC_SKILL_PROMPT = """You are an RL environment design expert.
A user wants to build a Gymnasium environment for the following domain:

DOMAIN DESCRIPTION: {description}

List the domain-specific rules an engineer must follow when coding this
environment. Cover ALL of the following:

1. OBSERVATION SPACE: What should the agent observe? Which values and
   metrics are critical for decision-making? What normalisation range?

2. ACTION SPACE: What can the agent do? Discrete or continuous? How many
   dimensions? What are valid bounds?

3. REWARD FUNCTION: How is success measured? Which metrics should be
   rewarded, which penalised? What magnitude range? How to prevent
   reward hacking?

4. TRANSITION DYNAMICS: How does the world evolve? Deterministic or
   stochastic? What are the physics / rules?

5. TERMINATION CONDITIONS: When does an episode end? Success condition?
   Failure condition? Time limit?

6. EDGE CASES: Domain-specific boundary conditions and pitfalls to watch
   for.

7. TYPICAL PARAMETERS: Sensible default values for this domain (step
   limits, grid sizes, physical constants, etc.).

Output ONLY the numbered rules. Do NOT write any code."""

# ---------------------------------------------------------------------------
# NL -> Env Spec JSON prompt
# ---------------------------------------------------------------------------

SPEC_GENERATION_PROMPT = """You are the RLForge Architect Agent. Given the user's
natural-language description of a Reinforcement Learning environment, produce a
structured JSON specification.

Output ONLY a valid JSON object with these keys:
{{
  "name": "kebab-case-name",
  "domain": "finance|game|control|optimization|robotics|custom",
  "description": "One-paragraph summary",
  "observation_space": {{
    "type": "Box|Discrete|MultiDiscrete",
    "shape": [N],
    "low": -1.0,
    "high": 1.0,
    "components": ["component1", "component2"]
  }},
  "action_space": {{
    "type": "Box|Discrete",
    "shape": [M],
    "low": -1.0,
    "high": 1.0,
    "components": ["action1", "action2"]
  }},
  "reward_function": {{
    "type": "description of reward",
    "components": ["reward_comp1", "reward_comp2"],
    "range": [-10, 10]
  }},
  "episode": {{
    "max_steps": 1000,
    "termination_conditions": ["condition1"],
    "truncation_conditions": ["step >= max_steps"]
  }},
  "parameters": {{}}
}}

Do NOT include any text before or after the JSON. Output ONLY the JSON object."""

# ---------------------------------------------------------------------------
# Error-fix prompt template
# ---------------------------------------------------------------------------

FIX_PROMPT_TEMPLATE = """The previously generated environment code FAILED the
following tests:

{test_results}

ORIGINAL ENVIRONMENT SPEC:
{env_spec}

PREVIOUS CODE:
{original_code}

Fix ALL failing tests and regenerate the COMPLETE environment code.
Do NOT omit any part of the code — output the full, corrected file.
Output ONLY Python code. No markdown, no explanations."""

# ---------------------------------------------------------------------------
# Conversation / iterate mode prompt
# ---------------------------------------------------------------------------

CONVERSATION_MODE_PROMPT = """You are an expert RL environment and training assistant.
You are part of the kualia.ai platform. The user is building and iterating on a
Gymnasium environment and training RL agents on it.

You have FULL CONTEXT about the project: environment code, spec, training results,
agent replay data, and experiment history. Use all of this to give informed answers.

The user may either:
A) Ask a QUESTION — about the environment, training results, agent behavior, metrics,
   replay episodes, experiment comparisons, or anything related to the project.
B) Request a CODE CHANGE to the environment.

CURRENT ENVIRONMENT CODE:
{current_code}

CURRENT ENVIRONMENT SPEC:
{current_spec}

{project_state}

USER MESSAGE:
{user_message}

STEP 1 — Decide the MODE:
- If the user is asking a question, seeking explanation, analysis, or interpretation
  (e.g. "what are the actions?", "explain the reward", "how did training go?",
  "interpret ep1 results", "why is success rate low?", "compare run 1 vs run 2"),
  set MODE to "question".
- If the user wants to change, add, remove, or modify anything in the environment,
  set MODE to "change".

STEP 2 — Respond accordingly.
- For QUESTIONS: Give a thorough, expert-level answer. Reference specific numbers
  from the training data, replay episodes, or environment code. Provide insights
  and actionable suggestions when relevant (e.g. "the low success rate suggests
  the reward shaping might need adjustment" or "episode 2 failed because the
  agent accumulated negative reward after step 150").
- For CHANGES: Implement the requested modification.

OUTPUT FORMAT — respond with EXACTLY this structure (keep the markers):

===MODE===
question OR change

===CHANGE_SUMMARY===
If MODE is "question": Your detailed answer to the user's question.
If MODE is "change": One sentence describing what changed and why.

===BREAKING_CHANGES===
If MODE is "question": NONE
If MODE is "change": List each breaking change on its own line, or write NONE.

===UPDATED_SPEC===
If MODE is "question": SKIP
If MODE is "change": Full updated JSON spec.

===UPDATED_CODE===
If MODE is "question": SKIP
If MODE is "change": Full updated Python code (complete file, all imports included).

RULES FOR CHANGES:
1. Make ONLY the requested change. Do not refactor unrelated code.
2. Preserve existing observation_space and action_space dimensions unless
   the user explicitly asks to change them.
3. ALL tests must still pass after your change.
4. If the change is a BREAKING CHANGE (observation or action space shape
   changed), you MUST note it.
5. Maintain all existing class-level constants, docstrings, and type hints.
"""

# ---------------------------------------------------------------------------
# Keyword sets for fast domain classification
# ---------------------------------------------------------------------------

_DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "finance": [
        "trading", "trade", "stock", "portfolio", "asset", "forex", "crypto",
        "cryptocurrency", "market", "hedge", "option", "futures", "bond",
        "sharpe", "ohlcv", "candlestick", "finance", "financial", "invest",
        "return", "dividend", "equity", "commodity", "exchange", "price",
        "borsa", "hisse", "yatirim", "finans", "komisyon",
    ],
    "game": [
        "grid", "gridworld", "maze", "game", "board", "puzzle", "tile",
        "pacman", "sokoban", "snake", "tetris", "chess", "atari", "pixel",
        "dungeon", "rpg", "platformer", "arcade", "level", "map", "cell",
        "oyun", "labirent", "bulmaca", "tahta",
    ],
    "control": [
        "pendulum", "cartpole", "cart-pole", "balance", "swing", "inverted",
        "pid", "lqr", "joint", "angle", "velocity", "torque", "acrobot",
        "mountain", "car", "helicopter", "quadrotor", "vehicle", "lane",
        "steering", "throttle", "control", "stabilize", "regulate",
        "denge", "arac", "kontrol", "hiz",
    ],
    "optimization": [
        "optimize", "optimization", "schedule", "scheduling", "allocat",
        "resource", "inventory", "supply", "chain", "logistics", "warehouse",
        "routing", "tsp", "knapsack", "bin", "packing", "queue", "throughput",
        "capacity", "demand", "production", "factory", "job", "shop",
        "lojistik", "optimizasyon", "kaynak", "depo", "uretim",
    ],
    "robotics": [
        "robot", "robotic", "arm", "manipulator", "gripper", "reach",
        "grasp", "pick", "place", "drone", "uav", "quadcopter", "walker",
        "humanoid", "legged", "locomotion", "lidar", "sensor", "motor",
        "actuator", "end-effector", "kinematics", "dynamics", "navigation",
        "obstacle", "collision", "path", "slam",
        "robot", "kol", "drone", "engel", "navigasyon",
    ],
}

# ---------------------------------------------------------------------------
# Difficulty modifiers
# ---------------------------------------------------------------------------

_DIFFICULTY_MODIFIERS: Dict[str, str] = {
    "easy": (
        "Generate a SIMPLE environment suitable for beginners. "
        "Use small observation and action spaces. Keep dynamics straightforward "
        "with mostly deterministic transitions. Dense reward only. "
        "max_steps should be short (100-200)."
    ),
    "medium": (
        "Generate a MEDIUM-complexity environment. "
        "Balanced observation/action spaces. Include some stochasticity. "
        "Mix of dense and shaped rewards. Standard episode length."
    ),
    "hard": (
        "Generate a CHALLENGING environment for experienced researchers. "
        "Large observation space with partial observability where appropriate. "
        "Complex dynamics, stochastic transitions, sparse reward components. "
        "Long episodes. Include at least two reward-hacking countermeasures."
    ),
}


class ArchitectService:
    """Core Architect Agent for the RLForge platform.

    Generates, fixes, and iterates on Gymnasium-compatible RL environments
    from natural-language descriptions using a two-layer skill system.
    """

    def __init__(self) -> None:
        self._skill_cache: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # LLM routing
    # ------------------------------------------------------------------

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> str:
        """Call an LLM with Kimi-first, Claude-fallback, OpenAI-last strategy."""
        try:
            if settings.kimi_api_key:
                return await ai_service._call_kimi(
                    system_prompt, user_prompt, max_tokens=max_tokens,
                )
        except Exception as e:
            logger.warning("Kimi call failed, trying Claude: %s", e)

        try:
            if settings.anthropic_api_key:
                return await ai_service._call_claude(system_prompt, user_prompt)
        except Exception as e:
            logger.warning("Claude call failed, trying OpenAI: %s", e)

        return await ai_service._call_openai(system_prompt, user_prompt)

    # ------------------------------------------------------------------
    # Domain classification
    # ------------------------------------------------------------------

    async def classify_domain(self, description: str) -> str:
        """Classify the domain of an environment description.

        Uses fast keyword matching first; falls back to LLM classification
        when no keyword matches strongly enough.
        """
        text = description.lower()
        scores: Dict[str, int] = {d: 0 for d in _DOMAIN_KEYWORDS}

        for domain, keywords in _DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    scores[domain] += 1

        best_domain = max(scores, key=scores.get)  # type: ignore[arg-type]
        if scores[best_domain] >= 2:
            logger.info("Domain classified via keywords: %s (score=%d)", best_domain, scores[best_domain])
            return best_domain

        if scores[best_domain] == 1:
            logger.info("Weak keyword match for %s, using as hint", best_domain)
            return best_domain

        logger.info("No keyword match, falling back to LLM classification")
        llm_prompt = (
            "Classify the following RL environment description into EXACTLY ONE "
            "of these domains: finance, game, control, optimization, robotics, custom.\n\n"
            f"Description: {description}\n\n"
            "Reply with ONLY the single domain word, nothing else."
        )
        try:
            result = await self._call_llm(
                "You are a domain classifier. Reply with a single word.",
                llm_prompt,
                max_tokens=20,
            )
            domain = result.strip().lower().rstrip(".")
            if domain in _DOMAIN_KEYWORDS or domain == "custom":
                return domain
        except Exception as e:
            logger.warning("LLM domain classification failed: %s", e)

        return "custom"

    # ------------------------------------------------------------------
    # Skill system (Layer 1 + Layer 2)
    # ------------------------------------------------------------------

    async def _get_skill_prompt(self, domain: str, description: str) -> str:
        """Return domain-specific skill prompt.

        Layer 1: return built-in skill if the domain is known.
        Layer 2: generate and cache a dynamic skill for unknown domains.
        """
        if domain in DOMAIN_SKILLS:
            logger.info("Using built-in skill for domain: %s", domain)
            return DOMAIN_SKILLS[domain]

        if domain in self._skill_cache:
            logger.info("Using cached dynamic skill for domain: %s", domain)
            return self._skill_cache[domain]

        logger.info("Generating dynamic skill for domain: %s", domain)
        try:
            skill_text = await self._call_llm(
                "You are an RL environment design expert.",
                DYNAMIC_SKILL_PROMPT.format(description=description),
                max_tokens=2048,
            )
            header = f"=== DYNAMIC SKILL: {domain.upper()} ===\n"
            full_skill = header + skill_text
            self._skill_cache[domain] = full_skill
            return full_skill
        except Exception as e:
            logger.error("Dynamic skill generation failed: %s", e)
            return ""

    # ------------------------------------------------------------------
    # NL -> Environment Spec
    # ------------------------------------------------------------------

    async def generate_env_spec(
        self,
        description: str,
        domain: Optional[str] = None,
    ) -> dict:
        """Convert a natural-language description into a structured env spec JSON."""
        if domain is None:
            domain = await self.classify_domain(description)

        skill_prompt = await self._get_skill_prompt(domain, description)

        system = ARCHITECT_SYSTEM_PROMPT + "\n\n" + skill_prompt + "\n\n" + SPEC_GENERATION_PROMPT
        user_prompt = (
            f"Domain: {domain}\n\n"
            f"User description:\n{description}\n\n"
            "Generate the environment specification JSON."
        )

        logger.info("Generating env spec for domain=%s", domain)
        response = await self._call_llm(system, user_prompt, max_tokens=2048)
        spec = self._extract_json(response)
        spec.setdefault("domain", domain)
        return spec

    # ------------------------------------------------------------------
    # NL / Spec -> Environment Code
    # ------------------------------------------------------------------

    async def generate_env_code(
        self,
        description: str,
        domain: Optional[str] = None,
        difficulty: str = "medium",
    ) -> Dict[str, Any]:
        """Generate complete Gymnasium environment code from a description.

        Single LLM call: produces both spec JSON and full code together.
        """
        if domain is None:
            domain = await self.classify_domain(description)

        skill_prompt = await self._get_skill_prompt(domain, description)
        difficulty_hint = _DIFFICULTY_MODIFIERS.get(difficulty, _DIFFICULTY_MODIFIERS["medium"])

        combined_prompt = f"""Generate a complete Gymnasium v0.29+ environment.

DOMAIN: {domain}
DIFFICULTY: {difficulty}
{difficulty_hint}

USER DESCRIPTION:
{description}

You MUST output EXACTLY two sections with these markers:

===ENV_SPEC===
A valid JSON object with keys: name (kebab-case), domain, description,
observation_space (type, shape, low, high, components),
action_space (type, shape, low, high, components),
reward_function (type, components, range),
episode (max_steps, termination_conditions, truncation_conditions),
parameters.

===ENV_CODE===
The complete Python file implementing the environment. Include ALL imports.
The file must be directly importable and the environment class must be
instantiable without arguments. Output ONLY valid Python code in this section."""

        system = ARCHITECT_SYSTEM_PROMPT + "\n\n" + skill_prompt

        logger.info("Generating env spec+code in single call: domain=%s, difficulty=%s", domain, difficulty)
        response = await self._call_llm(system, combined_prompt, max_tokens=8192)

        spec_raw = self._extract_section(response, "ENV_SPEC")
        code_raw = self._extract_section(response, "ENV_CODE")

        if spec_raw:
            env_spec = self._extract_json(spec_raw)
        else:
            env_spec = self._extract_json(response)

        if code_raw:
            code = self._extract_code(code_raw)
        else:
            code = self._extract_code(response)

        env_spec.setdefault("domain", domain)

        obs_space = env_spec.get("observation_space", {})
        act_space = env_spec.get("action_space", {})
        reward_fn = env_spec.get("reward_function", {})

        return {
            "name": env_spec.get("name", "custom-env"),
            "description": env_spec.get("description", description),
            "observation_space": (
                f"{obs_space.get('type', 'Box')}"
                f"(shape={obs_space.get('shape', '?')})"
            ),
            "action_space": (
                f"{act_space.get('type', 'Discrete')}"
                f"(shape={act_space.get('shape', '?')})"
            ),
            "reward_description": reward_fn.get("type", "see spec"),
            "code": code,
            "env_spec": env_spec,
        }

    # ------------------------------------------------------------------
    # Error-fix loop (single attempt; caller retries up to 3x)
    # ------------------------------------------------------------------

    async def fix_env_code(
        self,
        original_code: str,
        env_spec: str,
        test_results: str,
    ) -> str:
        """Attempt to fix environment code that failed tests.

        Parameters
        ----------
        original_code : str
            The Python source that failed.
        env_spec : str
            JSON string of the environment spec.
        test_results : str
            Human-readable summary of failing tests.

        Returns
        -------
        str
            Corrected Python source code.
        """
        system = ARCHITECT_SYSTEM_PROMPT
        user_prompt = FIX_PROMPT_TEMPLATE.format(
            test_results=test_results,
            env_spec=env_spec,
            original_code=original_code,
        )

        logger.info("Attempting to fix env code based on test failures")
        response = await self._call_llm(system, user_prompt, max_tokens=8192)
        return self._extract_code(response)

    # ------------------------------------------------------------------
    # Conversation / iterate mode (Environment Builder)
    # ------------------------------------------------------------------

    def _build_project_state(self, project_context: Optional[Dict[str, Any]] = None) -> str:
        """Build a formatted string with current project state for the LLM."""
        if not project_context:
            return ""

        parts = []

        # Latest training run
        if project_context.get("latest_training"):
            t = project_context["latest_training"]
            parts.append("=== LATEST TRAINING RUN ===")
            parts.append(f"Run ID: {t.get('id', '?')}")
            parts.append(f"Algorithm: {t.get('algorithm', '?')}")
            parts.append(f"Status: {t.get('status', '?')}")
            parts.append(f"Total Timesteps: {t.get('total_timesteps', '?')}")
            if t.get("results"):
                r = t["results"]
                parts.append(f"Mean Reward: {r.get('mean_reward', '?')}")
                parts.append(f"Std Reward: {r.get('std_reward', '?')}")
                parts.append(f"Mean Episode Length: {r.get('mean_ep_length', '?')}")
                parts.append(f"Success Rate: {r.get('success_rate', '?')}")
                parts.append(f"Episodes Trained: {r.get('episodes_trained', '?')}")
                parts.append(f"Training Time: {r.get('training_time_sec', '?')}s")
                if r.get("eval_rewards"):
                    parts.append(f"Eval Rewards (per episode): {r['eval_rewards']}")
                if r.get("eval_lengths"):
                    parts.append(f"Eval Lengths (per episode): {r['eval_lengths']}")
                if r.get("hyperparameters"):
                    parts.append(f"Hyperparameters: {json.dumps(r['hyperparameters'])}")

        # Replay data (condensed)
        if project_context.get("replay"):
            replay = project_context["replay"]
            episodes = replay if isinstance(replay, list) else replay.get("episodes", [])
            if episodes:
                parts.append(f"\n=== AGENT REPLAY ({len(episodes)} evaluation episodes) ===")
                for i, ep in enumerate(episodes):
                    steps = ep.get("steps", [])
                    total_reward = ep.get("total_reward", sum(s.get("reward", 0) for s in steps))
                    success = ep.get("success", False)
                    parts.append(f"Episode {i+1}: {len(steps)} steps, total_reward={total_reward:.4f}, success={success}")
                    if steps:
                        first = steps[0]
                        last = steps[-1]
                        parts.append(f"  First step — action: {first.get('action')}, obs: {first.get('obs')}, reward: {first.get('reward')}")
                        parts.append(f"  Last step  — action: {last.get('action')}, obs: {last.get('obs')}, reward: {last.get('reward')}")

        # Training history
        if project_context.get("history"):
            runs = project_context["history"]
            if runs:
                parts.append(f"\n=== TRAINING HISTORY ({len(runs)} runs) ===")
                for run in runs[:10]:
                    parts.append(
                        f"Run #{run.get('id')}: {run.get('algorithm')} "
                        f"{run.get('total_timesteps', '?')} steps, "
                        f"status={run.get('status')}, "
                        f"reward={run.get('mean_reward', '?')}, "
                        f"success={run.get('success_rate', '?')}, "
                        f"env_v{run.get('env_version', '?')}"
                    )

        if not parts:
            return ""
        return "PROJECT STATE (training results, replay, history):\n" + "\n".join(parts)

    async def iterate_env(
        self,
        current_code: str,
        current_spec_json: str,
        user_message: str,
        project_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Apply a conversational change or answer a question about an environment.

        Returns dict with keys: mode, change_summary, updated_code,
        updated_spec, breaking_changes.
        mode is "question" or "change".
        """
        system = ARCHITECT_SYSTEM_PROMPT
        project_state = self._build_project_state(project_context)
        user_prompt = CONVERSATION_MODE_PROMPT.format(
            current_code=current_code,
            current_spec=current_spec_json,
            project_state=project_state,
            user_message=user_message,
        )

        logger.info("Iterating env with user message: %.80s...", user_message)
        response = await self._call_llm(system, user_prompt, max_tokens=8192)

        mode_raw = (self._extract_section(response, "MODE") or "change").strip().lower()
        is_question = mode_raw.startswith("question")

        change_summary = self._extract_section(response, "CHANGE_SUMMARY") or "Change applied."

        if is_question:
            logger.info("Question mode detected, no code changes.")
            return {
                "mode": "question",
                "change_summary": change_summary.strip(),
                "updated_code": current_code,
                "updated_spec": json.loads(current_spec_json) if current_spec_json else {},
                "breaking_changes": [],
            }

        breaking_raw = self._extract_section(response, "BREAKING_CHANGES") or "NONE"
        spec_raw = self._extract_section(response, "UPDATED_SPEC") or current_spec_json
        code_raw = self._extract_section(response, "UPDATED_CODE") or current_code

        breaking_changes: List[str] = []
        if breaking_raw.strip().upper() != "NONE":
            breaking_changes = [
                line.strip() for line in breaking_raw.strip().splitlines()
                if line.strip()
            ]

        updated_spec: dict
        try:
            updated_spec = json.loads(spec_raw)
        except json.JSONDecodeError:
            updated_spec = self._extract_json(spec_raw)

        updated_code = self._extract_code(code_raw)

        return {
            "mode": "change",
            "change_summary": change_summary.strip(),
            "updated_code": updated_code,
            "updated_spec": updated_spec,
            "breaking_changes": breaking_changes,
        }

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _extract_code(self, text: str) -> str:
        """Extract Python code from an LLM response.

        Handles ```python fenced blocks, bare ``` blocks, and raw code.
        """
        fenced = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
        if fenced:
            return fenced[0].strip()

        lines = text.strip().splitlines()
        code_lines: list[str] = []
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code or stripped.startswith(("import ", "from ", "class ", "def ")):
                in_code = True
                code_lines.append(line)
            elif in_code:
                code_lines.append(line)

        if code_lines:
            return "\n".join(code_lines).strip()

        return text.strip()

    def _extract_json(self, text: str) -> dict:
        """Extract a JSON object from an LLM response.

        Tries direct parse first, then searches for the outermost { ... }.
        """
        cleaned = text.strip()
        if cleaned.startswith("```"):
            inner = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
            inner = re.sub(r"\n?```\s*$", "", inner)
            cleaned = inner.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{", cleaned)
        if match:
            start = match.start()
            depth = 0
            for i in range(start, len(cleaned)):
                if cleaned[i] == "{":
                    depth += 1
                elif cleaned[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(cleaned[start : i + 1])
                        except json.JSONDecodeError:
                            break

        logger.warning("Could not extract JSON from LLM response, returning empty dict")
        return {}

    @staticmethod
    def _extract_section(text: str, marker: str) -> Optional[str]:
        """Extract content between ===MARKER=== delimiters."""
        pattern = rf"==={re.escape(marker)}===\s*\n(.*?)(?====\w|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None


architect_service = ArchitectService()
