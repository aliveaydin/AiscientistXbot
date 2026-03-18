from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces


class RemoteEnv(gym.Env):
    """Gymnasium-compatible wrapper for remote RLForge environments."""

    metadata = {"render_modes": []}

    def __init__(self, client: Any, session_id: str, env_info: Dict[str, Any]):
        super().__init__()
        self.client = client
        self.session_id = session_id
        self.env_info = env_info

        self.observation_space = self._parse_space(
            env_info.get("observation_space", "")
        )
        self.action_space = self._parse_space(
            env_info.get("action_space", ""),
            fallback_discrete=True,
        )

    # ── Gymnasium API ─────────────────────────────────────

    def step(self, action: Any) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        serializable_action = self._action_to_json(action)
        resp = self.client.session_step(self.session_id, serializable_action)

        obs = self._to_numpy(resp.get("observation", resp.get("obs")))
        reward = float(resp.get("reward", 0.0))
        terminated = bool(resp.get("terminated", False))
        truncated = bool(resp.get("truncated", False))
        info = resp.get("info", {})

        return obs, reward, terminated, truncated, info

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        resp = self.client.session_reset(self.session_id, seed=seed)

        obs = self._to_numpy(resp.get("observation", resp.get("obs")))
        info = resp.get("info", {})

        return obs, info

    def close(self) -> None:
        try:
            self.client.session_close(self.session_id)
        except Exception:
            pass

    # ── Space parsing ─────────────────────────────────────

    def _parse_space(
        self,
        space_desc: str,
        fallback_discrete: bool = False,
    ) -> gym.Space:
        """Parse a space description string into a gymnasium.Space.

        Handles formats like:
          - "Box((4,), float32, -inf, inf)"
          - "Box(shape=[30], low=-1, high=1)"
          - "Box(104)"  /  "Box((104,))"
          - "Discrete(4)"
          - "MultiDiscrete([3, 3, 2])"
          - "MultiBinary(8)"
        Falls back to a reasonable default when parsing fails.
        """
        if not space_desc or not isinstance(space_desc, str):
            if fallback_discrete:
                return spaces.Discrete(4)
            return spaces.Box(low=-1.0, high=1.0, shape=(10,), dtype=np.float32)

        text = space_desc.strip()

        # --- Discrete ---
        m = re.match(r"Discrete\((\d+)\)", text)
        if m:
            return spaces.Discrete(int(m.group(1)))

        # --- MultiDiscrete ---
        m = re.match(r"MultiDiscrete\(\[([0-9,\s]+)\]\)", text)
        if m:
            vals = [int(v.strip()) for v in m.group(1).split(",") if v.strip()]
            return spaces.MultiDiscrete(np.array(vals, dtype=np.int64))

        # --- MultiBinary ---
        m = re.match(r"MultiBinary\((\d+)\)", text)
        if m:
            return spaces.MultiBinary(int(m.group(1)))

        # --- Box with full spec: Box((4,), float32, -inf, inf) ---
        m = re.match(
            r"Box\(\(([0-9,\s]+)\),?\s*(?:float\d+)?,?\s*([0-9.eE+\-inf]+)?,?\s*([0-9.eE+\-inf]+)?\)",
            text,
        )
        if m:
            shape = tuple(int(d.strip()) for d in m.group(1).split(",") if d.strip())
            low = self._parse_float(m.group(2), default=-np.inf)
            high = self._parse_float(m.group(3), default=np.inf)
            return spaces.Box(low=low, high=high, shape=shape, dtype=np.float32)

        # --- Box with shape kwarg: Box(shape=[30], low=-1, high=1) ---
        shape_m = re.search(r"shape\s*=\s*\[?([0-9,\s]+)\]?", text)
        if shape_m and text.startswith("Box"):
            shape = tuple(int(d.strip()) for d in shape_m.group(1).split(",") if d.strip())
            low_m = re.search(r"low\s*=\s*([0-9.eE+\-inf]+)", text)
            high_m = re.search(r"high\s*=\s*([0-9.eE+\-inf]+)", text)
            low = self._parse_float(low_m.group(1) if low_m else None, default=-np.inf)
            high = self._parse_float(high_m.group(1) if high_m else None, default=np.inf)
            return spaces.Box(low=low, high=high, shape=shape, dtype=np.float32)

        # --- Box with single int: Box(104) or Box((104,)) ---
        m = re.match(r"Box\(\(?(\d+),?\)?\)", text)
        if m:
            dim = int(m.group(1))
            return spaces.Box(low=-np.inf, high=np.inf, shape=(dim,), dtype=np.float32)

        # --- Fallback ---
        if fallback_discrete:
            return spaces.Discrete(4)
        return spaces.Box(low=-1.0, high=1.0, shape=(10,), dtype=np.float32)

    @staticmethod
    def _parse_float(val: Optional[str], default: float) -> float:
        if val is None:
            return default
        val = val.strip()
        if val in ("inf", "+inf"):
            return np.inf
        if val == "-inf":
            return -np.inf
        try:
            return float(val)
        except ValueError:
            return default

    # ── Serialization helpers ─────────────────────────────

    @staticmethod
    def _action_to_json(action: Any) -> Any:
        """Convert a numpy/gym action into a JSON-serializable value."""
        if isinstance(action, np.ndarray):
            return action.tolist()
        if isinstance(action, (np.integer,)):
            return int(action)
        if isinstance(action, (np.floating,)):
            return float(action)
        return action

    @staticmethod
    def _to_numpy(obs: Any) -> np.ndarray:
        """Convert an observation payload (list, scalar, etc.) to a numpy array."""
        if obs is None:
            return np.zeros(1, dtype=np.float32)
        if isinstance(obs, np.ndarray):
            return obs.astype(np.float32)
        return np.asarray(obs, dtype=np.float32)

    # ── Repr ──────────────────────────────────────────────

    def __repr__(self) -> str:
        name = self.env_info.get("name", self.env_info.get("slug", "unknown"))
        return f"<RemoteEnv name={name!r} session={self.session_id!r}>"
