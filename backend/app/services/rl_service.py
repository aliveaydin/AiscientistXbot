import logging
from app.services.ai_service import ai_service
from app.config import settings

logger = logging.getLogger("rl_service")

RL_ENV_SYSTEM_PROMPT = """You are an expert reinforcement learning engineer designing custom RL environments for robotics research.

Given a topic or task description, design a complete RL environment specification. Be technically precise and practical.

Output format (use exactly these section headers):

NAME: [concise environment name, e.g. "BipedBalanceEnv"]

DESCRIPTION: [2-3 sentence description of the environment and its purpose]

OBSERVATION_SPACE: [describe the observation vector, e.g. "Box(14,): joint angles (6), joint velocities (6), torso orientation (2)"]

ACTION_SPACE: [describe the action vector, e.g. "Box(6,): torque commands for 6 joints, range [-1, 1]"]

REWARD: [describe the reward function in detail, including components and weights]

CODE:
```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CustomEnv(gym.Env):
    # ... full implementation
```

Requirements for the code:
- Use gymnasium (gym) API
- Include __init__, reset, step, render methods
- Define observation_space and action_space in __init__
- Implement realistic physics or dynamics (simplified is fine)
- Include comments explaining key design decisions
- The environment should be functional and runnable"""


class RLService:
    async def generate_environment(self, topic: str, category: str = "custom", difficulty: str = "medium") -> dict:
        user_prompt = f"""Design an RL environment for the following:

Topic: {topic}
Category: {category}
Difficulty: {difficulty}

Create a complete, functional gymnasium environment with realistic dynamics. The environment should be challenging enough for the {difficulty} difficulty level."""

        try:
            if settings.kimi_api_key:
                result = await ai_service._call_kimi(RL_ENV_SYSTEM_PROMPT, user_prompt, max_tokens=4096)
                model = settings.kimi_model
            elif settings.anthropic_api_key:
                result = await ai_service._call_claude(RL_ENV_SYSTEM_PROMPT, user_prompt)
                model = "claude-sonnet-4-20250514"
            else:
                result = await ai_service._call_openai(RL_ENV_SYSTEM_PROMPT, user_prompt)
                model = "gpt-4"
        except Exception as e:
            logger.error(f"Failed to generate RL environment: {e}")
            raise

        parsed = self._parse_env_response(result)
        parsed["model"] = model
        return parsed

    def _parse_env_response(self, text: str) -> dict:
        sections = {
            "name": "",
            "description": "",
            "observation_space": "",
            "action_space": "",
            "reward_description": "",
            "code": "",
        }

        lines = text.split("\n")
        current_section = None
        current_content = []

        for line in lines:
            upper = line.strip().upper()
            if upper.startswith("NAME:"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "name"
                current_content = [line.split(":", 1)[1].strip() if ":" in line else ""]
            elif upper.startswith("DESCRIPTION:"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "description"
                current_content = [line.split(":", 1)[1].strip() if ":" in line else ""]
            elif upper.startswith("OBSERVATION_SPACE:"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "observation_space"
                current_content = [line.split(":", 1)[1].strip() if ":" in line else ""]
            elif upper.startswith("ACTION_SPACE:"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "action_space"
                current_content = [line.split(":", 1)[1].strip() if ":" in line else ""]
            elif upper.startswith("REWARD:"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "reward_description"
                current_content = [line.split(":", 1)[1].strip() if ":" in line else ""]
            elif upper.startswith("CODE:"):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "code"
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        code = sections["code"]
        if code.startswith("```python"):
            code = code[len("```python"):].strip()
        if code.startswith("```"):
            code = code[3:].strip()
        if code.endswith("```"):
            code = code[:-3].strip()
        sections["code"] = code

        if not sections["name"]:
            sections["name"] = "Generated Environment"

        return sections


rl_service = RLService()
