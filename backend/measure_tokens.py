"""Measure actual Kimi K2.5 token usage for a single env generation pipeline."""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from openai import AsyncOpenAI

KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")
KIMI_MODEL = os.getenv("KIMI_MODEL", "kimi-k2.5")

client = AsyncOpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)

SYSTEM_PROMPT_SAMPLE = """You are the Architect Agent of the RLForge platform.
Your sole purpose is to generate, fix, and iterate on Reinforcement Learning
environments that are fully compatible with Gymnasium v0.29+.

=== GYMNASIUM COMPATIBILITY RULES ===
1. Every environment MUST subclass gymnasium.Env.
2. Required imports: gymnasium, numpy.
3. Required methods: __init__, step, reset, close.
4. step() returns (obs, reward, terminated, truncated, info).
5. reset() returns (obs, info).
6. observation_space and action_space MUST be set in __init__.

=== DESIGN PHILOSOPHY ===
Generate high-quality, working Gymnasium environments from descriptions.
"""

async def measure_call(label, system, user, max_tokens):
    print(f"\n--- {label} ---")
    resp = await client.chat.completions.create(
        model=KIMI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=1,
    )
    usage = resp.usage
    prompt_t = usage.prompt_tokens if usage else 0
    completion_t = usage.completion_tokens if usage else 0
    total_t = usage.total_tokens if usage else 0
    
    input_cost = prompt_t * 0.60 / 1_000_000
    output_cost = completion_t * 2.40 / 1_000_000
    total_cost = input_cost + output_cost

    print(f"  Prompt tokens:     {prompt_t:,}")
    print(f"  Completion tokens: {completion_t:,}")
    print(f"  Total tokens:      {total_t:,}")
    print(f"  Cost (Kimi):       ${total_cost:.4f}")
    print(f"  Cost (10x):        ${total_cost * 10:.4f}")
    
    return {
        "label": label,
        "prompt_tokens": prompt_t,
        "completion_tokens": completion_t,
        "total_tokens": total_t,
        "cost_actual": total_cost,
        "cost_10x": total_cost * 10,
        "content_length": len(resp.choices[0].message.content),
    }


async def main():
    results = []

    # 1) ENV GENERATION (main call)
    r = await measure_call(
        "ENV GENERATION (spec + code)",
        SYSTEM_PROMPT_SAMPLE,
        """Generate a complete Gymnasium v0.29+ environment.

DOMAIN: game
DIFFICULTY: medium

USER DESCRIPTION:
A grid-based puzzle game where an agent must navigate through a maze, collect keys to unlock doors, and reach the exit. The maze has random wall placement, multiple key-door pairs, and enemies that move in patterns. The agent can move in 4 directions and has limited visibility.

You MUST output EXACTLY two sections:
===ENV_SPEC===
A valid JSON object with keys: name, domain, description, observation_space, action_space, reward_function, episode, parameters.

===ENV_CODE===
Complete Python file implementing the environment. Include ALL imports.""",
        8192,
    )
    results.append(r)

    # 2) BUILDER CHAT (iterate message)
    r = await measure_call(
        "BUILDER CHAT (iterate)",
        SYSTEM_PROMPT_SAMPLE,
        """Current environment code:
```python
import gymnasium as gym
import numpy as np

class MazeEnv(gym.Env):
    def __init__(self, render_mode=None):
        super().__init__()
        self.grid_size = 10
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(10, 10, 3), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(4)
    def step(self, action):
        return self._get_obs(), 0.0, False, False, {}
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        return self._get_obs(), {}
    def _get_obs(self):
        return np.zeros((10, 10, 3), dtype=np.float32)
    def close(self):
        pass
```

User message: Add enemies that patrol in fixed patterns and damage the agent on contact. Also add a health system.

Provide updated code with the changes.""",
        8192,
    )
    results.append(r)

    # 3) FIX ENV CODE (error correction)
    r = await measure_call(
        "FIX ENV CODE (error correction)",
        SYSTEM_PROMPT_SAMPLE,
        """The following environment code FAILED tests. Fix it.

Test Results:
- reset() returned observation with shape (100,) but observation_space expects shape (10, 10, 3)
- step() raised TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'

Environment Spec:
{"name": "maze-puzzle", "observation_space": {"type": "Box", "shape": [10, 10, 3]}, "action_space": {"type": "Discrete", "n": 4}}

Original Code:
```python
import gymnasium as gym
import numpy as np

class MazePuzzleEnv(gym.Env):
    def __init__(self, render_mode=None):
        super().__init__()
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(10, 10, 3), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(4)
        self.position = None
    def step(self, action):
        self.position + action
        obs = np.zeros(100, dtype=np.float32)
        return obs, 0.0, False, False, {}
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.position = None
        return np.zeros(100, dtype=np.float32), {}
    def close(self):
        pass
```

Fix ALL issues and return the corrected complete code.""",
        8192,
    )
    results.append(r)

    # 4) DOMAIN CLASSIFICATION (small call)
    r = await measure_call(
        "DOMAIN CLASSIFICATION",
        "You are a domain classifier. Reply with a single word.",
        "Classify the following RL environment description into EXACTLY ONE of these domains: finance, game, control, optimization, robotics, custom.\n\nDescription: A simulation of a robotic arm that must pick and place objects on a conveyor belt.\n\nReply with ONLY the single domain word.",
        20,
    )
    results.append(r)

    # 5) RESEARCH LAB - Hypothesis generation (simulated)
    r = await measure_call(
        "RESEARCH LAB - Hypothesis",
        "You are Sage, a Research Strategist AI agent. Your role is to analyze research topics, formulate hypotheses, and guide experimental design.",
        """Research Topic: Dynamic Reinforcement Learning Environments with adaptive agent
Brief Description: environment that dynamically change in training, so the agent inside should adapt

Based on this topic, formulate a clear research hypothesis. Include:
1. The core research question
2. A testable hypothesis
3. Expected observations if hypothesis is true
4. Proposed environment characteristics
5. Agent behavior requirements""",
        4096,
    )
    results.append(r)

    # 6) RESEARCH LAB - Paper writing (simulated)
    r = await measure_call(
        "RESEARCH LAB - Paper Writing",
        "You are an academic paper writer. Write formal, structured research papers with proper academic language.",
        """Write the Introduction and Methodology sections of a research paper.

Title: Adaptive Learning in Dynamic RL Environments
Hypothesis: Agents with self-observation capabilities achieve 30% higher rewards in dynamic environments.

Training Results:
- PPO with standard obs: mean_reward=45.2, success_rate=0.23
- PPO with self-obs: mean_reward=67.8, success_rate=0.51

Write approximately 1500 words covering introduction, related work overview, and methodology.""",
        8192,
    )
    results.append(r)

    # SUMMARY
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total_actual = 0
    total_10x = 0
    total_prompt = 0
    total_completion = 0
    for r in results:
        total_actual += r["cost_actual"]
        total_10x += r["cost_10x"]
        total_prompt += r["prompt_tokens"]
        total_completion += r["completion_tokens"]
        print(f"  {r['label']:40s}  {r['total_tokens']:>7,} tok  ${r['cost_actual']:.4f}  (10x: ${r['cost_10x']:.4f})")

    print(f"\n  {'TOTAL':40s}  {total_prompt + total_completion:>7,} tok  ${total_actual:.4f}  (10x: ${total_10x:.4f})")
    print(f"  Total prompt tokens:     {total_prompt:,}")
    print(f"  Total completion tokens: {total_completion:,}")

    # Scenario costs
    print("\n" + "=" * 70)
    print("SCENARIO ESTIMATES (10x markup)")
    print("=" * 70)
    gen = results[0]
    fix = results[2]
    chat = results[1]
    hyp = results[4]
    paper = results[5]

    env_best = gen["cost_10x"]
    env_avg = gen["cost_10x"] + fix["cost_10x"]
    env_worst = gen["cost_10x"] + fix["cost_10x"] * 3

    print(f"  Env Generation (no fix):     ${env_best:.4f}")
    print(f"  Env Generation (1 fix):      ${env_avg:.4f}")
    print(f"  Env Generation (3 fixes):    ${env_worst:.4f}")
    print(f"  Builder Chat (1 message):    ${chat['cost_10x']:.4f}")
    print(f"  Research Lab (full est.):    ${(hyp['cost_10x'] + gen['cost_10x'] + paper['cost_10x']):.4f}")

    print(f"\n  How many env gens for $19 (avg): {19 / env_avg:.0f}")
    print(f"  How many env gens for $49 (avg): {49 / env_avg:.0f}")
    print(f"  How many env gens for $149 (avg): {149 / env_avg:.0f}")


if __name__ == "__main__":
    asyncio.run(main())
