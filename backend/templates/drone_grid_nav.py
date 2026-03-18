"""Drone 3D Grid Navigation Environment.

A drone must navigate a 3D space (10×10×10) from its start position to a goal
while avoiding 10 randomly placed spherical obstacles. Physics are simplified
with velocity-based control and basic collision detection.

Difficulty : hard
Domain     : robotics
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WORLD_SIZE: float = 10.0
NUM_OBSTACLES: int = 10
OBSTACLE_RADIUS: float = 0.5
GOAL_RADIUS: float = 0.5
MAX_SPEED: float = 1.0
MAX_STEPS: int = 500
OBS_DIM: int = 15  # pos(3) + vel(3) + goal(3) + 2*nearest_obstacle_rel(6)
NEAREST_K: int = 2

REWARD_GOAL: float = 1.0
COLLISION_PENALTY: float = -5.0
ACTION_PENALTY_COEFF: float = 0.01
DISTANCE_PENALTY_COEFF: float = 0.1

DT: float = 0.1  # simulation timestep
DRAG: float = 0.95


class DroneGridNavEnv(gym.Env):
    """Drone obstacle avoidance on a 3D grid.

    Observation
        ``Box((15,), float32)`` – normalised drone position (3),
        velocity (3), goal position (3), and relative positions of
        the 2 nearest obstacles (6).

    Actions
        ``Box((3,), float32)`` in ``[-1, 1]`` – thrust in x, y, z axes.
    """

    metadata: dict = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, render_mode: Optional[str] = None) -> None:
        super().__init__()
        self.render_mode = render_mode

        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(OBS_DIM,),
            dtype=np.float32,
        )
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(3,),
            dtype=np.float32,
        )

        self._pos: np.ndarray = np.zeros(3, dtype=np.float64)
        self._vel: np.ndarray = np.zeros(3, dtype=np.float64)
        self._goal: np.ndarray = np.zeros(3, dtype=np.float64)
        self._obstacles: np.ndarray = np.zeros((NUM_OBSTACLES, 3), dtype=np.float64)
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

        self._pos = self.np_random.uniform(0.5, 1.5, size=3).astype(np.float64)
        self._vel = np.zeros(3, dtype=np.float64)
        self._goal = self.np_random.uniform(WORLD_SIZE - 1.5, WORLD_SIZE - 0.5, size=3).astype(np.float64)

        self._obstacles = self._place_obstacles()
        self._step_count = 0

        obs = self._get_obs()
        info: Dict[str, Any] = {
            "distance_to_goal": self._distance_to_goal(),
        }
        return obs, info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        action = np.clip(np.asarray(action, dtype=np.float64).flatten()[:3], -1.0, 1.0)

        # Apply thrust
        self._vel += action * MAX_SPEED * DT
        self._vel *= DRAG
        speed = np.linalg.norm(self._vel)
        if speed > MAX_SPEED:
            self._vel = self._vel / speed * MAX_SPEED

        self._pos += self._vel * DT

        # Clamp to world bounds
        self._pos = np.clip(self._pos, 0.0, WORLD_SIZE)

        self._step_count += 1

        # Check collisions
        collided = self._check_collision()
        reached_goal = self._distance_to_goal() < GOAL_RADIUS

        # Reward computation
        dist = self._distance_to_goal()
        action_norm_sq = float(np.sum(action ** 2))

        reward_components: Dict[str, float] = {
            "distance": -dist * DISTANCE_PENALTY_COEFF,
            "goal": REWARD_GOAL if reached_goal else 0.0,
            "collision": COLLISION_PENALTY if collided else 0.0,
            "action_penalty": -ACTION_PENALTY_COEFF * action_norm_sq,
        }

        raw_reward = sum(reward_components.values())
        reward = float(np.clip(raw_reward, -10.0, 10.0))

        terminated = reached_goal or collided
        truncated = self._step_count >= MAX_STEPS

        obs = self._get_obs()
        info: Dict[str, Any] = {
            "distance_to_goal": dist,
            "collided": collided,
            "reached_goal": reached_goal,
            "reward_components": reward_components,
        }
        return obs, reward, terminated, truncated, info

    def render(self) -> None:
        if self.render_mode == "human":
            dist = self._distance_to_goal()
            print(
                f"Step {self._step_count:3d} | "
                f"Pos: ({self._pos[0]:.2f}, {self._pos[1]:.2f}, {self._pos[2]:.2f}) | "
                f"Dist: {dist:.2f}"
            )

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _place_obstacles(self) -> np.ndarray:
        """Place obstacles ensuring none overlap with start or goal."""
        obstacles: List[np.ndarray] = []
        min_clearance = OBSTACLE_RADIUS + 1.0

        attempts = 0
        while len(obstacles) < NUM_OBSTACLES and attempts < NUM_OBSTACLES * 50:
            candidate = self.np_random.uniform(1.0, WORLD_SIZE - 1.0, size=3).astype(np.float64)
            dist_start = float(np.linalg.norm(candidate - self._pos))
            dist_goal = float(np.linalg.norm(candidate - self._goal))

            if dist_start > min_clearance and dist_goal > min_clearance:
                too_close = False
                for obs in obstacles:
                    if float(np.linalg.norm(candidate - obs)) < OBSTACLE_RADIUS * 3.0:
                        too_close = True
                        break
                if not too_close:
                    obstacles.append(candidate)
            attempts += 1

        while len(obstacles) < NUM_OBSTACLES:
            obstacles.append(self.np_random.uniform(1.0, WORLD_SIZE - 1.0, size=3).astype(np.float64))

        return np.array(obstacles, dtype=np.float64)

    def _distance_to_goal(self) -> float:
        return float(np.linalg.norm(self._pos - self._goal))

    def _check_collision(self) -> bool:
        distances = np.linalg.norm(self._obstacles - self._pos, axis=1)
        return bool(np.any(distances < OBSTACLE_RADIUS))

    def _nearest_obstacles_relative(self) -> np.ndarray:
        """Return relative positions of the K nearest obstacles, normalised."""
        diff = self._obstacles - self._pos  # (N, 3)
        distances = np.linalg.norm(diff, axis=1)
        indices = np.argsort(distances)[:NEAREST_K]
        nearest_rel = diff[indices]  # (K, 3)

        # Normalise to [-1, 1] using world size
        normalised = nearest_rel / (WORLD_SIZE / 2.0)
        return np.clip(normalised.flatten(), -1.0, 1.0).astype(np.float64)

    def _get_obs(self) -> np.ndarray:
        half_world = WORLD_SIZE / 2.0

        pos_norm = (self._pos - half_world) / half_world
        vel_norm = self._vel / MAX_SPEED
        goal_norm = (self._goal - half_world) / half_world
        nearest = self._nearest_obstacles_relative()

        obs = np.concatenate([pos_norm, vel_norm, goal_norm, nearest]).astype(np.float32)
        return np.clip(obs, -1.0, 1.0)
