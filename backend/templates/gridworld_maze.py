"""Grid-World Maze Navigation Environment.

A 10x10 grid where an agent must navigate from a start position to a goal
while avoiding randomly placed walls. Walls are generated with 30 % density
and a BFS check guarantees a valid path exists.

Difficulty : easy
Domain     : game
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GRID_SIZE: int = 10
WALL_DENSITY: float = 0.30
MAX_STEPS: int = 200

REWARD_GOAL: float = 1.0
REWARD_STEP: float = -0.01
REWARD_WALL: float = -0.1

CELL_EMPTY: float = 0.0
CELL_WALL: float = -1.0
CELL_AGENT: float = 0.5
CELL_GOAL: float = 1.0

# Actions: up, right, down, left
ACTION_DELTAS: Dict[int, Tuple[int, int]] = {
    0: (-1, 0),
    1: (0, 1),
    2: (1, 0),
    3: (0, -1),
}


def _bfs_path_exists(
    grid: np.ndarray,
    start: Tuple[int, int],
    goal: Tuple[int, int],
) -> bool:
    """Return *True* if a path from *start* to *goal* exists on *grid*."""
    rows, cols = grid.shape
    visited = set()
    queue: deque[Tuple[int, int]] = deque([start])
    visited.add(start)
    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            return True
        for dr, dc in ACTION_DELTAS.values():
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited and grid[nr, nc] != CELL_WALL:
                visited.add((nr, nc))
                queue.append((nr, nc))
    return False


class GridWorldMazeEnv(gym.Env):
    """10x10 grid-world maze with random walls.

    Observation
        Flattened grid of shape ``(100,)`` with float32 values encoding
        empty cells, walls, agent position, and goal position.

    Actions
        ``Discrete(4)`` – 0: up, 1: right, 2: down, 3: left.
    """

    metadata: dict = {"render_modes": ["human", "ansi"], "render_fps": 10}

    def __init__(self, render_mode: Optional[str] = None) -> None:
        super().__init__()
        self.render_mode = render_mode

        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(GRID_SIZE * GRID_SIZE,),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(4)

        self._grid: np.ndarray = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
        self._agent_pos: Tuple[int, int] = (0, 0)
        self._goal_pos: Tuple[int, int] = (GRID_SIZE - 1, GRID_SIZE - 1)
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

        self._agent_pos = (0, 0)
        self._goal_pos = (GRID_SIZE - 1, GRID_SIZE - 1)
        self._step_count = 0

        self._grid = self._generate_maze()
        obs = self._get_obs()
        info: Dict[str, Any] = {"agent_pos": self._agent_pos, "goal_pos": self._goal_pos}
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        assert self.action_space.contains(action), f"Invalid action {action}"

        self._step_count += 1

        dr, dc = ACTION_DELTAS[action]
        new_r = self._agent_pos[0] + dr
        new_c = self._agent_pos[1] + dc

        reward_components: Dict[str, float] = {"step": REWARD_STEP, "goal": 0.0, "wall": 0.0}
        hit_wall = False

        if 0 <= new_r < GRID_SIZE and 0 <= new_c < GRID_SIZE:
            if self._grid[new_r, new_c] == CELL_WALL:
                hit_wall = True
                reward_components["wall"] = REWARD_WALL
            else:
                self._agent_pos = (new_r, new_c)
        else:
            hit_wall = True
            reward_components["wall"] = REWARD_WALL

        terminated = self._agent_pos == self._goal_pos
        if terminated:
            reward_components["goal"] = REWARD_GOAL

        truncated = self._step_count >= MAX_STEPS

        raw_reward = sum(reward_components.values())
        reward = float(np.clip(raw_reward, -10.0, 10.0))

        obs = self._get_obs()
        info: Dict[str, Any] = {
            "agent_pos": self._agent_pos,
            "goal_pos": self._goal_pos,
            "hit_wall": hit_wall,
            "reward_components": reward_components,
        }
        return obs, reward, terminated, truncated, info

    def render(self) -> Optional[str]:
        if self.render_mode == "ansi":
            return self._render_ansi()
        return None

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate_maze(self) -> np.ndarray:
        """Generate a random maze ensuring a path from agent to goal."""
        while True:
            grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)
            wall_mask = self.np_random.random((GRID_SIZE, GRID_SIZE)) < WALL_DENSITY
            grid[wall_mask] = CELL_WALL
            grid[self._agent_pos[0], self._agent_pos[1]] = CELL_EMPTY
            grid[self._goal_pos[0], self._goal_pos[1]] = CELL_EMPTY
            if _bfs_path_exists(grid, self._agent_pos, self._goal_pos):
                return grid

    def _get_obs(self) -> np.ndarray:
        obs = self._grid.copy()
        obs[self._agent_pos[0], self._agent_pos[1]] = CELL_AGENT
        obs[self._goal_pos[0], self._goal_pos[1]] = CELL_GOAL
        return obs.flatten().astype(np.float32)

    def _render_ansi(self) -> str:
        symbols = {CELL_EMPTY: ".", CELL_WALL: "#", CELL_AGENT: "A", CELL_GOAL: "G"}
        obs_grid = self._grid.copy()
        obs_grid[self._agent_pos[0], self._agent_pos[1]] = CELL_AGENT
        obs_grid[self._goal_pos[0], self._goal_pos[1]] = CELL_GOAL
        lines: list[str] = []
        for row in obs_grid:
            lines.append(" ".join(symbols.get(float(c), "?") for c in row))
        return "\n".join(lines)
