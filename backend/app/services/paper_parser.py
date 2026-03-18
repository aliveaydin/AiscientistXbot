import logging
from typing import Optional, Dict, Any

from app.services.ai_service import ai_service
from app.services.architect_service import architect_service
from app.services.sandbox_runner import sandbox_runner
from app.config import settings

logger = logging.getLogger("paper_parser")

ENV_EXTRACTION_PROMPT = """You are an expert at reading reinforcement learning papers and extracting the environment specification described or implied in them.

Given the text of a research paper (or its relevant sections), extract the following as a structured JSON object:

{
  "name": "short env class name, e.g. DroneNavigationEnv",
  "description": "1-2 sentence description of the environment",
  "domain": "one of: finance, game, control, optimization, robotics, custom",
  "observation_space": {
    "type": "Box or Discrete or Dict",
    "shape": [dim1, dim2, ...],
    "description": "what each dimension represents"
  },
  "action_space": {
    "type": "Box or Discrete",
    "shape": [dim1, ...] or "n_actions for Discrete",
    "description": "what each action represents"
  },
  "reward_function": {
    "type": "dense or sparse",
    "components": ["list of reward components"],
    "description": "how reward is computed"
  },
  "dynamics": "brief description of environment dynamics/physics",
  "termination_conditions": ["list of termination conditions"],
  "max_episode_steps": 1000,
  "difficulty": "easy, medium, or hard"
}

If the paper does not describe a specific RL environment, infer a reasonable one from the problem domain discussed. Always produce valid JSON.

Output ONLY the JSON object, nothing else."""


class PaperParser:
    """Extracts RL environment specifications from research papers."""

    async def parse_paper_text(self, text: str) -> str:
        """Extract text from raw paper content (already parsed PDF text or abstract)."""
        if len(text) > 12000:
            text = text[:6000] + "\n...[truncated]...\n" + text[-4000:]
        return text

    async def extract_env_spec(self, paper_text: str) -> dict:
        """Extract environment specification from paper text using LLM."""
        truncated = await self.parse_paper_text(paper_text)

        try:
            if settings.kimi_api_key:
                response = await ai_service._call_kimi(
                    ENV_EXTRACTION_PROMPT,
                    f"Paper text:\n\n{truncated}",
                    max_tokens=2048,
                )
            elif settings.anthropic_api_key:
                response = await ai_service._call_claude(
                    ENV_EXTRACTION_PROMPT,
                    f"Paper text:\n\n{truncated}",
                )
            else:
                response = await ai_service._call_openai(
                    ENV_EXTRACTION_PROMPT,
                    f"Paper text:\n\n{truncated}",
                )
        except Exception as e:
            logger.error("Failed to extract env spec from paper: %s", e)
            return {}

        return architect_service._extract_json(response)

    async def generate_from_paper(self, paper_text: str) -> Dict[str, Any]:
        """Full pipeline: paper text -> env spec -> code -> test.

        Returns dict with: name, description, domain, code, env_spec,
        test_results, observation_space, action_space, reward_description.
        """
        env_spec = await self.extract_env_spec(paper_text)
        if not env_spec:
            return {"error": "Could not extract environment specification from paper"}

        description = env_spec.get("description", "Environment from paper")
        domain = env_spec.get("domain", "custom")

        gen = await architect_service.generate_env_code(
            description, domain=domain,
            difficulty=env_spec.get("difficulty", "medium"),
        )

        code = gen.get("code", "")
        test_results = await sandbox_runner.run_all_tests(code)

        attempts = 0
        import json
        spec_json = json.dumps(env_spec)
        while test_results["failed"] > 0 and attempts < 3:
            attempts += 1
            fixed = await architect_service.fix_env_code(code, spec_json, json.dumps(test_results))
            if fixed and fixed != code:
                code = fixed
                test_results = await sandbox_runner.run_all_tests(code)
            else:
                break

        return {
            "name": env_spec.get("name", gen.get("name", "PaperEnv")),
            "description": description,
            "domain": domain,
            "code": code,
            "env_spec": env_spec,
            "test_results": test_results,
            "observation_space": gen.get("observation_space", ""),
            "action_space": gen.get("action_space", ""),
            "reward_description": gen.get("reward_description", ""),
        }

    async def parse_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes using PyPDF2."""
        import io
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error("PDF parsing failed: %s", e)
            return ""


paper_parser = PaperParser()
