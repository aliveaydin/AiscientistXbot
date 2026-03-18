"""Warehouse Inventory Management Environment.

Optimises ordering decisions for 3 products over a 30-day horizon with
stochastic Poisson demand, holding costs, stockout penalties, and ordering
costs.

Difficulty : medium
Domain     : optimisation
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
NUM_PRODUCTS: int = 3
EPISODE_DAYS: int = 30
OBS_DIM: int = NUM_PRODUCTS * 3  # stock (3) + demand_forecast (3) + days_until_restock (3)

MAX_STOCK: float = 200.0
MAX_ORDER: float = 100.0
RESTOCK_LEAD_DAYS: int = 2

# Per-product parameters: (unit_revenue, holding_cost_per_unit, stockout_penalty, order_cost_per_unit, mean_demand)
PRODUCT_PARAMS: list[Tuple[float, float, float, float, float]] = [
    (10.0, 0.5, 5.0, 3.0, 15.0),
    (20.0, 1.0, 10.0, 6.0, 8.0),
    (5.0, 0.2, 3.0, 1.5, 25.0),
]


class InventoryMgmtEnv(gym.Env):
    """Warehouse inventory optimisation for 3 products.

    Observation
        ``Box((9,), float32)`` – normalised stock levels (3), demand
        forecasts (3), and days until next restock (3).

    Actions
        ``Box((3,), float32)`` in ``[0, 1]`` – order quantity fraction for
        each product, scaled internally to ``MAX_ORDER``.
    """

    metadata: dict = {"render_modes": ["human"], "render_fps": 2}

    def __init__(self, render_mode: Optional[str] = None) -> None:
        super().__init__()
        self.render_mode = render_mode

        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(OBS_DIM,),
            dtype=np.float32,
        )
        self.action_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(NUM_PRODUCTS,),
            dtype=np.float32,
        )

        self._stock: np.ndarray = np.zeros(NUM_PRODUCTS, dtype=np.float64)
        self._pending_orders: list[list[Tuple[int, float]]] = [[] for _ in range(NUM_PRODUCTS)]
        self._day: int = 0
        self._demand_forecast: np.ndarray = np.zeros(NUM_PRODUCTS, dtype=np.float64)

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

        self._stock = np.array([MAX_STOCK * 0.5] * NUM_PRODUCTS, dtype=np.float64)
        self._pending_orders = [[] for _ in range(NUM_PRODUCTS)]
        self._day = 0
        self._update_demand_forecast()

        obs = self._get_obs()
        info: Dict[str, Any] = {"day": self._day, "stock": self._stock.copy()}
        return obs, info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        action = np.clip(np.asarray(action, dtype=np.float64).flatten()[:NUM_PRODUCTS], 0.0, 1.0)

        order_quantities = action * MAX_ORDER

        # Place orders (arrive after lead time)
        for i in range(NUM_PRODUCTS):
            if order_quantities[i] > 0.5:
                arrival_day = self._day + RESTOCK_LEAD_DAYS
                self._pending_orders[i].append((arrival_day, float(order_quantities[i])))

        # Receive arriving orders
        for i in range(NUM_PRODUCTS):
            arrived = [qty for (d, qty) in self._pending_orders[i] if d <= self._day]
            self._pending_orders[i] = [(d, qty) for (d, qty) in self._pending_orders[i] if d > self._day]
            self._stock[i] = min(self._stock[i] + sum(arrived), MAX_STOCK)

        # Realise demand (Poisson)
        reward_components: Dict[str, float] = {
            "revenue": 0.0,
            "holding_cost": 0.0,
            "stockout_penalty": 0.0,
            "ordering_cost": 0.0,
        }

        for i, (rev, hold, sout, ocost, lam) in enumerate(PRODUCT_PARAMS):
            demand = float(self.np_random.poisson(lam))
            sold = min(self._stock[i], demand)
            stockout = max(demand - self._stock[i], 0.0)
            self._stock[i] = max(self._stock[i] - sold, 0.0)

            reward_components["revenue"] += rev * sold
            reward_components["holding_cost"] -= hold * self._stock[i]
            reward_components["stockout_penalty"] -= sout * stockout
            reward_components["ordering_cost"] -= ocost * order_quantities[i]

        self._day += 1
        self._update_demand_forecast()

        terminated = False
        truncated = self._day >= EPISODE_DAYS

        raw_reward = sum(reward_components.values())
        # Scale reward to a reasonable range
        scaled_reward = raw_reward / 100.0
        reward = float(np.clip(scaled_reward, -10.0, 10.0))

        obs = self._get_obs()
        info: Dict[str, Any] = {
            "day": self._day,
            "stock": self._stock.copy(),
            "order_quantities": order_quantities.copy(),
            "reward_components": reward_components,
        }
        return obs, reward, terminated, truncated, info

    def render(self) -> None:
        if self.render_mode == "human":
            print(
                f"Day {self._day:2d}/{EPISODE_DAYS} | "
                f"Stock: {np.round(self._stock, 1)} | "
                f"Forecast: {np.round(self._demand_forecast, 1)}"
            )

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _update_demand_forecast(self) -> None:
        """Simple noisy forecast based on true mean demand."""
        for i, (_, _, _, _, lam) in enumerate(PRODUCT_PARAMS):
            noise = self.np_random.standard_normal() * lam * 0.2
            self._demand_forecast[i] = max(lam + noise, 0.0)

    def _days_until_restock(self) -> np.ndarray:
        result = np.zeros(NUM_PRODUCTS, dtype=np.float64)
        for i in range(NUM_PRODUCTS):
            if self._pending_orders[i]:
                result[i] = min(d - self._day for d, _ in self._pending_orders[i])
            else:
                result[i] = float(RESTOCK_LEAD_DAYS)
        return result

    def _get_obs(self) -> np.ndarray:
        stock_norm = self._stock / MAX_STOCK
        max_demand = max(p[4] for p in PRODUCT_PARAMS)
        forecast_norm = self._demand_forecast / (max_demand * 2.0)
        restock_norm = self._days_until_restock() / float(RESTOCK_LEAD_DAYS + 1)

        obs = np.concatenate([stock_norm, forecast_norm, restock_norm]).astype(np.float32)
        return np.clip(obs, 0.0, 1.0)
