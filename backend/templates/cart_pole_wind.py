"""CartPole with Wind Disturbance Environment.

Classic CartPole control with an added stochastic wind force applied to the
cart at every step. Observations are normalised to ``[-1, 1]``.

Difficulty : easy
Domain     : control
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

# ---------------------------------------------------------------------------
# Physics constants
# ---------------------------------------------------------------------------
GRAVITY: float = 9.8
CART_MASS: float = 1.0
POLE_MASS: float = 0.1
TOTAL_MASS: float = CART_MASS + POLE_MASS
POLE_HALF_LENGTH: float = 0.5
POLE_MASS_LENGTH: float = POLE_MASS * POLE_HALF_LENGTH
FORCE_MAG: float = 10.0
TAU: float = 0.02  # seconds between state updates

# Termination thresholds
CART_X_THRESHOLD: float = 2.4
POLE_ANGLE_THRESHOLD_DEG: float = 12.0
POLE_ANGLE_THRESHOLD_RAD: float = math.radians(POLE_ANGLE_THRESHOLD_DEG)

MAX_STEPS: int = 500
WIND_MAX_MAG: float = 5.0

# Normalisation bounds (used to map raw state to [-1, 1])
NORM_BOUNDS: np.ndarray = np.array(
    [CART_X_THRESHOLD, 3.0, POLE_ANGLE_THRESHOLD_RAD, math.radians(50.0)],
    dtype=np.float64,
)

REWARD_ALIVE: float = 1.0
REWARD_FAIL: float = -10.0


class CartPoleWindEnv(gym.Env):
    """CartPole variant with random wind disturbance.

    Observation
        ``Box((4,), float32)`` – normalised cart position, cart velocity,
        pole angle, and pole angular velocity.

    Actions
        ``Discrete(2)`` – 0: push left, 1: push right.
    """

    metadata: dict = {"render_modes": ["human"], "render_fps": 50}

    def __init__(self, render_mode: Optional[str] = None) -> None:
        super().__init__()
        self.render_mode = render_mode

        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(4,),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(2)

        self._state: np.ndarray = np.zeros(4, dtype=np.float64)
        self._step_count: int = 0

    # ------------------------------------------------------------------
    # Gym API
    # ------------------------------------------------------------------
    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)

        self._state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,)).astype(np.float64)
        self._step_count = 0

        obs = self._get_obs()
        info: Dict[str, Any] = {"wind_force": 0.0}
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        assert self.action_space.contains(action), f"Invalid action {action}"

        x, x_dot, theta, theta_dot = self._state

        # Agent force
        force = FORCE_MAG if action == 1 else -FORCE_MAG

        # Wind disturbance
        wind_force = float(self.np_random.uniform(-WIND_MAX_MAG, WIND_MAX_MAG))
        total_force = force + wind_force

        # Semi-implicit Euler integration
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)

        temp = (total_force + POLE_MASS_LENGTH * theta_dot ** 2 * sin_theta) / TOTAL_MASS
        theta_acc = (GRAVITY * sin_theta - cos_theta * temp) / (
            POLE_HALF_LENGTH * (4.0 / 3.0 - POLE_MASS * cos_theta ** 2 / TOTAL_MASS)
        )
        x_acc = temp - POLE_MASS_LENGTH * theta_acc * cos_theta / TOTAL_MASS

        x = x + TAU * x_dot
        x_dot = x_dot + TAU * x_acc
        theta = theta + TAU * theta_dot
        theta_dot = theta_dot + TAU * theta_acc

        self._state = np.array([x, x_dot, theta, theta_dot], dtype=np.float64)
        self._step_count += 1

        # Termination check
        failed = abs(x) > CART_X_THRESHOLD or abs(theta) > POLE_ANGLE_THRESHOLD_RAD
        terminated = bool(failed)
        truncated = self._step_count >= MAX_STEPS

        reward_components: Dict[str, float] = {"alive": 0.0, "fail": 0.0}
        if failed:
            reward_components["fail"] = REWARD_FAIL
        else:
            reward_components["alive"] = REWARD_ALIVE

        raw_reward = sum(reward_components.values())
        reward = float(np.clip(raw_reward, -10.0, 10.0))

        obs = self._get_obs()
        info: Dict[str, Any] = {
            "wind_force": wind_force,
            "raw_state": self._state.copy(),
            "reward_components": reward_components,
        }
        return obs, reward, terminated, truncated, info

    def render(self) -> None:
        if self.render_mode == "human":
            x, x_dot, theta, theta_dot = self._state
            print(
                f"Step {self._step_count:3d} | "
                f"x={x:+.3f} v={x_dot:+.3f} θ={math.degrees(theta):+.2f}° ω={theta_dot:+.3f}"
            )

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_obs(self) -> np.ndarray:
        normalised = self._state / NORM_BOUNDS
        return np.clip(normalised, -1.0, 1.0).astype(np.float32)
