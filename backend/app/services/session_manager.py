import logging
import time
import importlib
import importlib.util
import tempfile
import os
import json
import uuid
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from collections import OrderedDict
import threading

logger = logging.getLogger("session_mgr")


class EnvSession:
    """Wraps a single Gymnasium environment instance."""

    def __init__(self, session_id: str, env_instance, env_id: int):
        self.session_id = session_id
        self.env = env_instance
        self.env_id = env_id
        self.created_at = time.time()
        self.last_used = time.time()
        self.step_count = 0
        self.is_reset = False

    def touch(self):
        self.last_used = time.time()


class SessionManager:
    MAX_SESSIONS = 20
    IDLE_TIMEOUT = 900  # 15 minutes

    def __init__(self):
        self._sessions: OrderedDict[str, EnvSession] = OrderedDict()
        self._lock = threading.Lock()

    def create_session(self, env_code: str, env_id: int) -> str:
        """Create a new environment session from code. Returns session_id."""
        session_id = str(uuid.uuid4())

        with self._lock:
            self.cleanup_idle()
            if len(self._sessions) >= self.MAX_SESSIONS:
                self._evict_lru()

        env_instance = self._load_env(env_code)
        session = EnvSession(session_id, env_instance, env_id)

        with self._lock:
            self._sessions[session_id] = session
            self._sessions.move_to_end(session_id)

        logger.info("Session created: %s (env_id=%d, total=%d)",
                     session_id[:8], env_id, len(self._sessions))
        return session_id

    def step(self, session_id: str, action) -> Dict[str, Any]:
        """Step the environment. Returns {obs, reward, terminated, truncated, info}."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(f"Session not found: {session_id}")
            self._sessions.move_to_end(session_id)

        if not session.is_reset:
            logger.info("Auto-resetting session %s before first step", session_id[:8])
            seed = int(np.random.randint(0, 2**31))
            session.env.reset(seed=seed)
            session.is_reset = True

        action = self._convert_action(session.env, action)
        obs, reward, terminated, truncated, info = session.env.step(action)

        session.step_count += 1
        session.touch()

        return {
            "obs": self._numpy_to_json(obs),
            "reward": self._numpy_to_json(reward),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "info": self._numpy_to_json(info),
        }

    def reset(self, session_id: str, seed: Optional[int] = None) -> Dict[str, Any]:
        """Reset the environment. Returns {obs, info}."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(f"Session not found: {session_id}")
            self._sessions.move_to_end(session_id)

        kwargs: Dict[str, Any] = {}
        if seed is not None:
            kwargs["seed"] = seed

        obs, info = session.env.reset(**kwargs)
        session.is_reset = True
        session.step_count = 0
        session.touch()

        return {
            "obs": self._numpy_to_json(obs),
            "info": self._numpy_to_json(info),
        }

    def close(self, session_id: str):
        """Close and remove a session."""
        with self._lock:
            session = self._sessions.pop(session_id, None)

        if session is None:
            logger.warning("Attempted to close non-existent session: %s", session_id[:8])
            return

        try:
            session.env.close()
        except Exception:
            logger.exception("Error closing env for session %s", session_id[:8])

        logger.info("Session closed: %s (steps=%d)", session_id[:8], session.step_count)

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session metadata."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(f"Session not found: {session_id}")

        return {
            "session_id": session.session_id,
            "env_id": session.env_id,
            "created_at": session.created_at,
            "last_used": session.last_used,
            "step_count": session.step_count,
            "is_reset": session.is_reset,
            "idle_seconds": time.time() - session.last_used,
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        with self._lock:
            session_ids = list(self._sessions.keys())

        result = []
        for sid in session_ids:
            try:
                result.append(self.get_session_info(sid))
            except KeyError:
                pass
        return result

    def cleanup_idle(self):
        """Remove sessions that have been idle too long. Caller should hold _lock or call within lock."""
        now = time.time()
        to_remove = [
            sid for sid, s in self._sessions.items()
            if (now - s.last_used) > self.IDLE_TIMEOUT
        ]
        for sid in to_remove:
            session = self._sessions.pop(sid, None)
            if session:
                try:
                    session.env.close()
                except Exception:
                    logger.exception("Error closing idle session %s", sid[:8])
                logger.info("Evicted idle session: %s (idle %.0fs)",
                            sid[:8], now - session.last_used)

    def _evict_lru(self):
        """Remove least recently used session. Must be called under _lock."""
        if not self._sessions:
            return
        oldest_sid, oldest_session = next(iter(self._sessions.items()))
        self._sessions.pop(oldest_sid)
        try:
            oldest_session.env.close()
        except Exception:
            logger.exception("Error closing evicted session %s", oldest_sid[:8])
        logger.info("Evicted LRU session: %s (idle %.0fs)",
                     oldest_sid[:8], time.time() - oldest_session.last_used)

    def _load_env(self, env_code: str):
        """Load environment code and instantiate the Env subclass."""
        import gymnasium

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".py", prefix="rlforge_env_")
        try:
            with os.fdopen(tmp_fd, "w") as f:
                f.write(env_code)

            spec = importlib.util.spec_from_file_location("_rlforge_tmp_env", tmp_path)
            if spec is None or spec.loader is None:
                raise ImportError("Could not create module spec from env code")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        env_cls = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, gymnasium.Env)
                and attr is not gymnasium.Env
            ):
                env_cls = attr
                break

        if env_cls is None:
            raise ValueError("No gymnasium.Env subclass found in the provided code")

        return env_cls()

    @staticmethod
    def _convert_action(env, action):
        """Convert JSON-friendly action to the format expected by env.action_space."""
        import gymnasium.spaces as spaces

        action_space = env.action_space

        if isinstance(action_space, spaces.Discrete):
            return int(action)

        if isinstance(action_space, (spaces.Box, spaces.MultiDiscrete, spaces.MultiBinary)):
            if isinstance(action, list):
                return np.array(action, dtype=action_space.dtype)
            return action

        if isinstance(action_space, spaces.Tuple):
            if isinstance(action, (list, tuple)):
                return tuple(action)

        if isinstance(action_space, spaces.Dict):
            if isinstance(action, dict):
                return action

        return action

    @staticmethod
    def _numpy_to_json(obj) -> Any:
        """Convert numpy arrays/types to JSON-serializable Python types."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float32, np.float64, np.floating)):
            return float(obj)
        if isinstance(obj, (np.int32, np.int64, np.integer)):
            return int(obj)
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, dict):
            return {k: SessionManager._numpy_to_json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [SessionManager._numpy_to_json(item) for item in obj]
        if isinstance(obj, np.generic):
            return obj.item()
        return obj


session_manager = SessionManager()
