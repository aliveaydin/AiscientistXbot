"""5-Stock Portfolio Trading Environment.

Simulates one trading year (252 days) with five synthetic stocks whose prices
follow Geometric Brownian Motion. The agent decides target portfolio weight
changes each day.

Difficulty : medium
Domain     : finance
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NUM_STOCKS: int = 5
NUM_FEATURES_PER_STOCK: int = 5  # OHLCV
EPISODE_LENGTH: int = 252
TRANSACTION_COST: float = 0.001

# GBM parameters per stock (mu, sigma, initial_price)
GBM_PARAMS: list[Tuple[float, float, float]] = [
    (0.08, 0.20, 100.0),
    (0.05, 0.15, 50.0),
    (0.12, 0.30, 200.0),
    (0.03, 0.10, 75.0),
    (0.10, 0.25, 150.0),
]

OBS_DIM: int = NUM_STOCKS * NUM_FEATURES_PER_STOCK + NUM_STOCKS + 1  # 31


class StockTrading5Env(gym.Env):
    """5-stock portfolio trading with synthetic GBM prices.

    Observation
        ``Box((31,), float32)`` – 5 stocks × 5 normalised OHLCV features,
        current portfolio weights (5), and cash ratio (1).

    Actions
        ``Box((5,), float32)`` in ``[-1, 1]`` – target weight changes,
        softmax-normalised internally to obtain target allocation.
    """

    metadata: dict = {"render_modes": ["human"], "render_fps": 4}

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
            shape=(NUM_STOCKS,),
            dtype=np.float32,
        )

        self._prices: np.ndarray = np.zeros((EPISODE_LENGTH + 1, NUM_STOCKS), dtype=np.float64)
        self._ohlcv: np.ndarray = np.zeros((EPISODE_LENGTH, NUM_STOCKS, NUM_FEATURES_PER_STOCK), dtype=np.float64)
        self._weights: np.ndarray = np.zeros(NUM_STOCKS, dtype=np.float64)
        self._cash: float = 1.0
        self._portfolio_value: float = 1.0
        self._step_idx: int = 0

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

        self._generate_prices()
        self._weights = np.zeros(NUM_STOCKS, dtype=np.float64)
        self._cash = 1.0
        self._portfolio_value = 1.0
        self._step_idx = 0

        obs = self._get_obs()
        info: Dict[str, Any] = {"portfolio_value": self._portfolio_value}
        return obs, info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        action = np.asarray(action, dtype=np.float64).flatten()[:NUM_STOCKS]

        # Softmax to get target weights (always positive, sum to 1)
        exp_a = np.exp(action - np.max(action))
        target_weights = exp_a / (exp_a.sum() + 1e-8)

        turnover = float(np.sum(np.abs(target_weights - self._weights)))

        old_weights = self._weights.copy()
        self._weights = target_weights
        self._cash = 0.0  # fully invested after rebalance

        # Price change
        day = self._step_idx
        if day + 1 < self._prices.shape[0]:
            price_returns = self._prices[day + 1] / (self._prices[day] + 1e-12) - 1.0
        else:
            price_returns = np.zeros(NUM_STOCKS, dtype=np.float64)

        portfolio_return = float(np.dot(self._weights, price_returns))
        self._portfolio_value *= (1.0 + portfolio_return)

        # Reward: log return minus transaction cost
        log_return = float(np.log(max(1.0 + portfolio_return, 1e-12)))
        transaction_penalty = TRANSACTION_COST * turnover
        reward_components: Dict[str, float] = {
            "log_return": log_return,
            "transaction_cost": -transaction_penalty,
        }
        raw_reward = log_return - transaction_penalty
        reward = float(np.clip(raw_reward, -10.0, 10.0))

        self._step_idx += 1

        terminated = self._portfolio_value <= 0.0
        truncated = self._step_idx >= EPISODE_LENGTH

        obs = self._get_obs()
        info: Dict[str, Any] = {
            "portfolio_value": self._portfolio_value,
            "weights": self._weights.copy(),
            "turnover": turnover,
            "reward_components": reward_components,
        }
        return obs, reward, terminated, truncated, info

    def render(self) -> None:
        if self.render_mode == "human":
            print(
                f"Day {self._step_idx:3d} | "
                f"Value: {self._portfolio_value:.4f} | "
                f"Weights: {np.round(self._weights, 3)}"
            )

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate_prices(self) -> None:
        """Generate synthetic OHLCV data via Geometric Brownian Motion."""
        dt = 1.0 / 252.0
        n_days = EPISODE_LENGTH + 1

        prices = np.zeros((n_days, NUM_STOCKS), dtype=np.float64)
        for i, (mu, sigma, s0) in enumerate(GBM_PARAMS):
            prices[0, i] = s0
            z = self.np_random.standard_normal(n_days - 1)
            for t in range(1, n_days):
                prices[t, i] = prices[t - 1, i] * np.exp(
                    (mu - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * z[t - 1]
                )
        self._prices = prices

        ohlcv = np.zeros((EPISODE_LENGTH, NUM_STOCKS, NUM_FEATURES_PER_STOCK), dtype=np.float64)
        for t in range(EPISODE_LENGTH):
            for i in range(NUM_STOCKS):
                open_p = prices[t, i]
                close_p = prices[t + 1, i]
                high_p = max(open_p, close_p) * (1.0 + abs(self.np_random.standard_normal()) * 0.005)
                low_p = min(open_p, close_p) * (1.0 - abs(self.np_random.standard_normal()) * 0.005)
                volume = abs(self.np_random.standard_normal()) * 1e6 + 1e5
                ohlcv[t, i] = [open_p, high_p, low_p, close_p, volume]
        self._ohlcv = ohlcv

    def _get_obs(self) -> np.ndarray:
        day = min(self._step_idx, EPISODE_LENGTH - 1)
        features = self._ohlcv[day].copy()  # (5, 5)

        # Normalise each feature column to [0, 1] over the episode so far
        window_start = max(0, day - 20)
        window = self._ohlcv[window_start : day + 1]
        if window.shape[0] > 0:
            mins = window.min(axis=0)
            maxs = window.max(axis=0)
            ranges = maxs - mins
            ranges[ranges < 1e-12] = 1.0
            features = (features - mins) / ranges
            features = features * 2.0 - 1.0  # scale to [-1, 1]

        flat_features = features.flatten()  # (25,)
        weights = self._weights.astype(np.float64)  # (5,)
        cash = np.array([self._cash], dtype=np.float64)  # (1,)

        obs = np.concatenate([flat_features, weights, cash]).astype(np.float32)
        obs = np.clip(obs, -1.0, 1.0)
        return obs
