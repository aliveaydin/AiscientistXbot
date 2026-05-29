import json
import logging
import os
import subprocess
import sys
import tempfile
import asyncio
import shutil
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RLEnvironment, TrainingRun
from app.database import async_session
from app.config import settings

logger = logging.getLogger("training")


class TrainingService:
    # Per-run wall-clock limit. With the concurrency queue, runs no longer fight
    # for CPU, so allow longer single-run budgets (configurable via env).
    MAX_TRAINING_TIME = max(300, int(os.getenv("TRAINING_MAX_TIME", "3600")))  # default 60 min
    MODELS_DIR = os.path.join(os.getenv("DATA_DIR", "./data"), "trained_models")

    # Concurrency: this box has limited CPU/RAM. Run a small number of trainings
    # at a time and queue the rest, instead of spawning all subprocesses at once
    # (which thrashes the CPU and triggers the OOM killer).
    MAX_CONCURRENT = max(1, int(os.getenv("MAX_CONCURRENT_TRAININGS", "1")))
    # Threads each training process may use (PyTorch/BLAS). Keeping this small
    # prevents a single run from grabbing every core.
    THREADS_PER_RUN = max(1, int(os.getenv("TRAINING_THREADS_PER_RUN", "1")))

    def __init__(self):
        os.makedirs(self.MODELS_DIR, exist_ok=True)
        self._active_processes: Dict[int, subprocess.Popen] = {}
        self._queue: list[int] = []  # FIFO of run_ids waiting for a free slot
        self._queue_lock = asyncio.Lock()

    async def recover_orphan_runs(self):
        """On startup, fix any runs stuck in 'running' that actually finished."""
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(TrainingRun).where(TrainingRun.status.in_(["running", "queued"]))
                )
                stuck_runs = result.scalars().all()
                if not stuck_runs:
                    return

                for run in stuck_runs:
                    if run.id in self._active_processes:
                        continue

                    age = (datetime.utcnow() - run.started_at).total_seconds() if run.started_at else 9999
                    if age < 30:
                        logger.info("Skipping run %d (only %ds old, might still be starting)", run.id, age)
                        continue

                    output_dir = os.path.abspath(
                        os.path.join(self.MODELS_DIR, f"run_{run.id}")
                    )
                    results_path = os.path.join(output_dir, "results.json")
                    curve_path = os.path.join(output_dir, "curve.json")

                    if os.path.exists(results_path):
                        try:
                            with open(results_path) as f:
                                results = json.load(f)
                            curve = []
                            if os.path.exists(curve_path):
                                with open(curve_path) as f:
                                    curve = json.load(f)

                            run.status = results.get("status", "failed")
                            run.results_json = json.dumps(results)
                            run.training_curve_json = json.dumps(curve) if curve else None
                            run.model_path = results.get("model_path")
                            run.completed_at = datetime.utcnow()
                            logger.info("Recovered orphan run %d: %s", run.id, run.status)
                        except Exception as e:
                            logger.error("Failed to recover run %d: %s", run.id, e)
                            run.status = "failed"
                            run.results_json = json.dumps({"status": "failed", "error": f"Recovery failed: {e}"})
                            run.completed_at = datetime.utcnow()
                    else:
                        run.status = "failed"
                        run.results_json = json.dumps({"status": "failed", "error": "Server restarted before completion"})
                        run.completed_at = datetime.utcnow()
                        logger.info("Marked orphan run %d as failed (no results)", run.id)

                await db.commit()
                logger.info("Orphan run recovery complete: %d runs checked", len(stuck_runs))
        except Exception as e:
            logger.error("Orphan run recovery error: %s", e)

    async def start_training(self, env_id: int, config: dict, db: AsyncSession) -> TrainingRun:
        """Start a training run in a background subprocess."""
        result = await db.execute(
            select(RLEnvironment).where(RLEnvironment.id == env_id)
        )
        env = result.scalar_one_or_none()
        if not env:
            raise ValueError(f"Environment {env_id} not found")
        if not env.code:
            raise ValueError(f"Environment {env_id} has no code")

        algorithm = config.get("algorithm") or self._select_algorithm(env.code)

        # Find previous model for "continue training"
        continue_from_path: Optional[str] = None
        if config.get("continue_from"):
            prev_result = await db.execute(
                select(TrainingRun)
                .where(TrainingRun.env_id == env_id, TrainingRun.status == "completed")
                .order_by(TrainingRun.id.desc())
                .limit(1)
            )
            prev_run = prev_result.scalar_one_or_none()
            if prev_run and prev_run.model_path and os.path.exists(prev_run.model_path):
                continue_from_path = prev_run.model_path
                algorithm = prev_run.algorithm or algorithm

        config["continue_from_path"] = continue_from_path

        seed_value = config.get("seed")
        variant_role = config.get("variant_role")

        training_run = TrainingRun(
            env_id=env_id,
            algorithm=algorithm,
            status="running",
            config_json=json.dumps(config),
            seed=int(seed_value) if seed_value is not None else None,
            variant_role=variant_role,
            started_at=datetime.utcnow(),
        )
        db.add(training_run)
        await db.commit()
        await db.refresh(training_run)

        output_dir = os.path.abspath(os.path.join(self.MODELS_DIR, f"run_{training_run.id}"))
        os.makedirs(output_dir, exist_ok=True)

        script_content = self._build_training_script(
            env_code=env.code,
            algorithm=algorithm,
            config=config,
            output_dir=output_dir,
        )

        script_path = os.path.join(output_dir, "train_script.py")
        with open(script_path, "w") as f:
            f.write(script_content)

        # Fail fast on incompatible algorithm/action-space combos (e.g. SAC/TD3
        # on a Discrete env) instead of spawning a process that crashes anyway.
        action_kind = self._action_space_kind(env.code)
        if not self._algo_compatible(algorithm, action_kind):
            msg = (f"Algorithm {algorithm} is incompatible with a {action_kind} "
                   f"action space; skipped.")
            training_run.status = "failed"
            training_run.results_json = json.dumps({"status": "failed", "error": msg})
            training_run.completed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(training_run)
            logger.warning("Training run %d: %s", training_run.id, msg)
            return training_run

        # Respect the concurrency limit: spawn now if a slot is free, else queue.
        if len(self._active_processes) < self.MAX_CONCURRENT:
            process = self._spawn_process(training_run.id, script_path, output_dir)
            logger.info(
                "Training run %d started for env %d with algorithm %s (pid=%d, active=%d)",
                training_run.id, env_id, algorithm, process.pid, len(self._active_processes),
            )
        else:
            training_run.status = "queued"
            await db.commit()
            await db.refresh(training_run)
            async with self._queue_lock:
                self._queue.append(training_run.id)
            logger.info(
                "Training run %d queued for env %d (algorithm %s, active=%d/%d, queue=%d)",
                training_run.id, env_id, algorithm, len(self._active_processes),
                self.MAX_CONCURRENT, len(self._queue),
            )
        return training_run

    async def get_status(self, run_id: int, db: AsyncSession) -> dict:
        """Get training run status and results."""
        result = await db.execute(
            select(TrainingRun).where(TrainingRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            raise ValueError(f"Training run {run_id} not found")

        config = json.loads(run.config_json) if run.config_json else {}
        data: Dict[str, Any] = {
            "id": run.id,
            "env_id": run.env_id,
            "algorithm": run.algorithm,
            "status": run.status,
            "config": config,
            "total_timesteps": config.get("total_timesteps", 10000),
            "results": json.loads(run.results_json) if run.results_json else None,
            "model_path": run.model_path,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }

        if run.status == "running":
            output_dir = os.path.abspath(os.path.join(self.MODELS_DIR, f"run_{run.id}"))
            curve_path = os.path.join(output_dir, "curve.json")
            if os.path.exists(curve_path):
                try:
                    with open(curve_path) as f:
                        curve = json.load(f)
                    if curve:
                        data["latest_reward"] = curve[-1].get("mean_reward")
                        data["progress_steps"] = curve[-1].get("step", 0)
                except (json.JSONDecodeError, IOError):
                    pass

        return data

    async def get_curve(self, run_id: int, db: AsyncSession) -> list:
        """Get training reward curve data."""
        result = await db.execute(
            select(TrainingRun).where(TrainingRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            raise ValueError(f"Training run {run_id} not found")

        if run.training_curve_json:
            try:
                return json.loads(run.training_curve_json)
            except json.JSONDecodeError:
                return []

        # Fall back to live curve file if training is still running
        if run.status == "running":
            output_dir = os.path.abspath(os.path.join(self.MODELS_DIR, f"run_{run.id}"))
            curve_path = os.path.join(output_dir, "curve.json")
            if os.path.exists(curve_path):
                try:
                    with open(curve_path) as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

        return []

    def _action_space_kind(self, env_code: str) -> str:
        """Return 'discrete', 'continuous', or 'unknown' for the env action space."""
        has_discrete = False
        has_continuous = False
        for line in env_code.split("\n"):
            ll = line.lower()
            if "action_space" in ll:
                if "discrete" in ll:
                    has_discrete = True
                if "box" in ll:
                    has_continuous = True
        if has_discrete and not has_continuous:
            return "discrete"
        if has_continuous and not has_discrete:
            return "continuous"
        return "unknown"

    @staticmethod
    def _algo_compatible(algorithm: str, action_kind: str) -> bool:
        """Whether an SB3 algorithm supports the env's action space.

        SAC/TD3 require continuous (Box) actions; DQN/QRDQN require discrete
        actions. PPO/A2C support both. 'unknown' is treated as compatible so we
        don't block envs we can't statically classify.
        """
        algorithm = (algorithm or "").upper()
        if action_kind == "unknown":
            return True
        continuous_only = {"SAC", "TD3"}
        discrete_only = {"DQN", "QRDQN"}
        if action_kind == "discrete" and algorithm in continuous_only:
            return False
        if action_kind == "continuous" and algorithm in discrete_only:
            return False
        return True

    def _subprocess_env(self) -> dict:
        """Environment for training subprocesses with capped thread counts."""
        env = os.environ.copy()
        n = str(self.THREADS_PER_RUN)
        for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
            env[key] = n
        return env

    def _spawn_process(self, run_id: int, script_path: str, output_dir: str) -> subprocess.Popen:
        """Launch the training subprocess and start its monitor task."""
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=output_dir,
            env=self._subprocess_env(),
        )
        self._active_processes[run_id] = process
        asyncio.create_task(self._monitor_training(run_id, process, output_dir))
        return process

    async def _launch_queued(self, run_id: int):
        """Start a previously-queued run (its script was already written)."""
        output_dir = os.path.abspath(os.path.join(self.MODELS_DIR, f"run_{run_id}"))
        script_path = os.path.join(output_dir, "train_script.py")
        async with async_session() as db:
            run = (await db.execute(
                select(TrainingRun).where(TrainingRun.id == run_id)
            )).scalar_one_or_none()
            if not run or run.status != "queued":
                return
            if not os.path.exists(script_path):
                run.status = "failed"
                run.results_json = json.dumps({"status": "failed", "error": "Queued script missing"})
                run.completed_at = datetime.utcnow()
                await db.commit()
                return
            run.status = "running"
            run.started_at = datetime.utcnow()
            await db.commit()
        self._spawn_process(run_id, script_path, output_dir)
        logger.info("Dequeued training run %d -> running (active=%d, queued=%d)",
                    run_id, len(self._active_processes), len(self._queue))

    async def _drain_queue(self):
        """Start queued runs while there is free capacity."""
        while True:
            async with self._queue_lock:
                if not self._queue or len(self._active_processes) >= self.MAX_CONCURRENT:
                    return
                next_id = self._queue.pop(0)
            await self._launch_queued(next_id)

    def _select_algorithm(self, env_code: str) -> str:
        """Auto-select algorithm based on action space type."""
        code_lower = env_code.lower()

        discrete_indicators = [
            "discrete", "multidiscrete",
            "spaces.discrete", "spaces.multidiscrete",
        ]
        continuous_indicators = [
            "spaces.box",
        ]

        has_discrete_action = False
        has_continuous_action = False

        for line in env_code.split("\n"):
            line_lower = line.lower()
            if "action_space" in line_lower:
                for indicator in discrete_indicators:
                    if indicator in line_lower:
                        has_discrete_action = True
                        break
                for indicator in continuous_indicators:
                    if indicator in line_lower:
                        has_continuous_action = True
                        break

        if has_continuous_action and not has_discrete_action:
            return "SAC"
        if has_discrete_action:
            return "PPO"

        # Broader heuristic: look anywhere in the code
        for indicator in discrete_indicators:
            if indicator in code_lower:
                return "PPO"
        for indicator in continuous_indicators:
            if indicator in code_lower:
                return "SAC"

        return "PPO"

    def _build_training_script(self, env_code: str, algorithm: str, config: dict, output_dir: str) -> str:
        """Build a self-contained Python training script with rich metrics."""
        total_timesteps = config.get("total_timesteps", 10000)
        learning_rate = config.get("learning_rate")
        n_eval_episodes = config.get("n_eval_episodes", 5)
        eval_freq = max(total_timesteps // 20, 100)
        continue_from_path = config.get("continue_from_path")
        batch_size = config.get("batch_size")
        gamma = config.get("gamma")
        net_arch = config.get("net_arch")
        seed = config.get("seed")
        env_kwargs = config.get("env_kwargs") or {}

        extra_args = ""
        if learning_rate:
            extra_args += f", learning_rate={learning_rate}"
        if batch_size:
            extra_args += f", batch_size={int(batch_size)}"
        if gamma:
            extra_args += f", gamma={float(gamma)}"
        if seed is not None:
            extra_args += f", seed={int(seed)}"

        net_arch_map = {
            "small": [64, 64],
            "medium": [256, 256],
            "large": [512, 256, 128],
        }
        policy_kwargs_arg = ""
        if net_arch and net_arch in net_arch_map:
            policy_kwargs_arg = f", policy_kwargs=dict(net_arch={net_arch_map[net_arch]})"

        lr_arg = ""  # kept for backward compat but absorbed into extra_args

        env_code_escaped = json.dumps(env_code)
        output_dir_escaped = json.dumps(output_dir)
        continue_path_escaped = json.dumps(continue_from_path) if continue_from_path else "None"
        seed_repr = "None" if seed is None else str(int(seed))
        env_kwargs_repr = repr(dict(env_kwargs))

        script = f'''#!/usr/bin/env python3
"""Auto-generated SB3 training script with rich metrics."""
import json, os, sys, traceback, importlib, importlib.util, inspect, tempfile, time
import numpy as np

# Cap CPU threads so concurrent training runs don't oversubscribe the box.
try:
    _nthreads = max(1, int(os.getenv("OMP_NUM_THREADS", "1")))
    import torch as _torch
    _torch.set_num_threads(_nthreads)
except Exception:
    pass

OUTPUT_DIR = {output_dir_escaped}
os.makedirs(OUTPUT_DIR, exist_ok=True)
CURVE_PATH = os.path.join(OUTPUT_DIR, "curve.json")
RESULTS_PATH = os.path.join(OUTPUT_DIR, "results.json")
REPLAY_PATH = os.path.join(OUTPUT_DIR, "replay.json")
MODEL_PATH = os.path.join(OUTPUT_DIR, "best_model")

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)

try:
    import gymnasium as gym
    from stable_baselines3 import PPO, DQN, SAC, A2C, TD3
    from stable_baselines3.common.callbacks import BaseCallback
    try:
        from sb3_contrib import QRDQN  # optional dependency
    except Exception:
        QRDQN = None
    try:
        from sb3_contrib import RecurrentPPO  # PPO-LSTM, optional dependency
    except Exception:
        RecurrentPPO = None

    env_code = {env_code_escaped}
    env_module_dir = tempfile.mkdtemp(prefix="rlforge_env_")
    env_module_path = os.path.join(env_module_dir, "custom_env.py")
    with open(env_module_path, "w") as f:
        f.write(env_code)

    spec = importlib.util.spec_from_file_location("custom_env", env_module_path)
    env_module = importlib.util.module_from_spec(spec)
    sys.modules["custom_env"] = env_module
    spec.loader.exec_module(env_module)

    env_class = None
    for name, obj in inspect.getmembers(env_module, inspect.isclass):
        if issubclass(obj, gym.Env) and obj is not gym.Env:
            env_class = obj
            break

    if env_class is None:
        write_json(RESULTS_PATH, {{"status": "failed", "error": "No gymnasium.Env subclass found"}})
        sys.exit(1)

    class RichCallback(BaseCallback):
        def __init__(self, eval_freq=500):
            super().__init__()
            self.eval_freq = eval_freq
            self.curve = []
            self._ep_rewards = []
            self._ep_lengths = []
            self._ep_successes = []
            self._cur_reward = 0.0
            self._cur_length = 0
            self._start_time = time.time()

        def _on_step(self):
            rewards = self.locals.get("rewards", [])
            dones = self.locals.get("dones", [])
            infos = self.locals.get("infos", [{{}}])

            if rewards is not None and len(rewards) > 0:
                self._cur_reward += float(rewards[0])
                self._cur_length += 1

            if dones is not None and len(dones) > 0 and dones[0]:
                self._ep_rewards.append(self._cur_reward)
                self._ep_lengths.append(self._cur_length)
                info = infos[0] if infos else {{}}
                success = info.get("is_success", info.get("success", self._cur_reward > 0))
                self._ep_successes.append(bool(success))
                self._cur_reward = 0.0
                self._cur_length = 0

            if self.n_calls % self.eval_freq == 0 and self._ep_rewards:
                recent_r = self._ep_rewards[-50:]
                recent_l = self._ep_lengths[-50:]
                recent_s = self._ep_successes[-50:]
                elapsed = time.time() - self._start_time

                point = {{
                    "step": self.num_timesteps,
                    "mean_reward": round(float(np.mean(recent_r)), 4),
                    "min_reward": round(float(np.min(recent_r)), 4),
                    "max_reward": round(float(np.max(recent_r)), 4),
                    "mean_ep_length": round(float(np.mean(recent_l)), 1),
                    "success_rate": round(sum(recent_s) / len(recent_s), 4) if recent_s else 0,
                    "episodes": len(self._ep_rewards),
                    "elapsed_sec": round(elapsed, 1),
                    "fps": round(self.num_timesteps / max(elapsed, 0.1), 0),
                }}

                try:
                    logger = self.model.logger
                    if hasattr(logger, "name_to_value"):
                        all_loss_keys = [
                            "train/loss", "train/policy_gradient_loss",
                            "train/value_loss", "train/entropy_loss",
                            "train/actor_loss", "train/critic_loss",
                        ]
                        for key in all_loss_keys:
                            if key in logger.name_to_value:
                                point[key.split("/")[-1]] = round(float(logger.name_to_value[key]), 6)
                        # Always write a generic 'loss' key from best available
                        if "loss" not in point:
                            for fallback in ["policy_gradient_loss", "actor_loss", "critic_loss", "value_loss"]:
                                if fallback in point:
                                    point["loss"] = point[fallback]
                                    break
                except Exception:
                    pass

                self.curve.append(point)
                write_json(CURVE_PATH, self.curve)
            return True

    ENV_KWARGS = {env_kwargs_repr}
    try:
        env = env_class(**ENV_KWARGS) if ENV_KWARGS else env_class()
    except TypeError:
        # Env constructor doesn't accept these kwargs; fall back to defaults.
        env = env_class()
        ENV_KWARGS = {{}}

    algorithm = "{algorithm}".upper()
    algo_map = {{"PPO": PPO, "DQN": DQN, "SAC": SAC, "A2C": A2C, "TD3": TD3}}
    if QRDQN is not None:
        algo_map["QRDQN"] = QRDQN
    if RecurrentPPO is not None:
        algo_map["RECURRENTPPO"] = RecurrentPPO
    CONTINUE_FROM = {continue_path_escaped}

    if algorithm not in algo_map:
        write_json(RESULTS_PATH, {{"status": "failed", "error": f"Unknown algorithm: {{algorithm}} (available: {{list(algo_map.keys())}})"}})
        sys.exit(1)

    # RecurrentPPO (PPO-LSTM) needs the recurrent policy.
    IS_RECURRENT = algorithm == "RECURRENTPPO"
    POLICY = "MlpLstmPolicy" if IS_RECURRENT else "MlpPolicy"

    AlgoClass = algo_map[algorithm]
    if CONTINUE_FROM and os.path.exists(CONTINUE_FROM):
        try:
            model = AlgoClass.load(CONTINUE_FROM, env=env)
        except Exception:
            model = AlgoClass(POLICY, env, verbose=0{extra_args}{policy_kwargs_arg})
    else:
        try:
            model = AlgoClass(POLICY, env, verbose=0{extra_args}{policy_kwargs_arg})
        except Exception:
            model = PPO("MlpPolicy", env, verbose=0{extra_args}{policy_kwargs_arg})
            algorithm = "PPO"
            IS_RECURRENT = False

    callback = RichCallback(eval_freq={eval_freq})
    model.learn(total_timesteps={total_timesteps}, callback=callback, progress_bar=False)
    model.save(MODEL_PATH)

    # Signal evaluation phase via curve
    if callback.curve:
        callback.curve[-1]["phase"] = "evaluating"
        write_json(CURVE_PATH, callback.curve)

    # Final evaluation + replay capture
    eval_rewards = []
    eval_lengths = []
    eval_successes = []
    replay_episodes = []

    for ep in range({n_eval_episodes}):
        obs, info = env.reset(seed=ep)
        episode_reward = 0.0
        steps_list = []
        done = False
        truncated = False
        step_count = 0
        lstm_states = None
        episode_start = np.ones((1,), dtype=bool)

        while not (done or truncated) and step_count < 5000:
            action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_start, deterministic=True)
            episode_start = np.zeros((1,), dtype=bool)
            act_serializable = action.tolist() if hasattr(action, "tolist") else action
            obs, reward, done, truncated, info = env.step(action)
            steps_list.append({{
                "obs": obs.tolist()[:10],
                "action": act_serializable,
                "reward": round(float(reward), 4),
            }})
            episode_reward += float(reward)
            step_count += 1

        eval_rewards.append(episode_reward)
        eval_lengths.append(step_count)
        success = info.get("is_success", info.get("success", episode_reward > 0))
        eval_successes.append(bool(success))

        if ep < 3:
            replay_episodes.append({{
                "episode": ep,
                "reward": round(episode_reward, 4),
                "length": step_count,
                "success": bool(success),
                "steps": steps_list[:200],
            }})

    write_json(REPLAY_PATH, replay_episodes)
    write_json(CURVE_PATH, callback.curve)

    # Collect hyperparameters from model
    hyperparams = {{}}
    try:
        hp = model.__dict__
        for k in ["learning_rate", "gamma", "n_steps", "batch_size", "n_epochs",
                   "ent_coef", "vf_coef", "max_grad_norm", "gae_lambda",
                   "buffer_size", "tau", "train_freq"]:
            if k in hp:
                v = hp[k]
                if callable(v):
                    try: v = float(v(1.0))
                    except: v = str(v)
                hyperparams[k] = v
        if hasattr(model.policy, "net_arch"):
            hyperparams["net_arch"] = str(model.policy.net_arch)
    except Exception:
        pass

    sb3_version = "unknown"
    try:
        import stable_baselines3
        sb3_version = stable_baselines3.__version__
    except Exception:
        pass

    write_json(RESULTS_PATH, {{
        "status": "completed",
        "algorithm": algorithm,
        "total_timesteps": {total_timesteps},
        "mean_reward": round(float(np.mean(eval_rewards)), 4),
        "std_reward": round(float(np.std(eval_rewards)), 4),
        "mean_ep_length": round(float(np.mean(eval_lengths)), 1),
        "success_rate": round(sum(eval_successes) / len(eval_successes), 4),
        "episodes_trained": len(callback._ep_rewards),
        "eval_episodes": {n_eval_episodes},
        "eval_rewards": [round(r, 4) for r in eval_rewards],
        "eval_lengths": eval_lengths,
        "training_time_sec": round(time.time() - callback._start_time, 1),
        "model_path": MODEL_PATH + ".zip",
        "hyperparameters": hyperparams,
        "sb3_version": sb3_version,
        "gymnasium_version": gym.__version__,
        "random_seed": {seed_repr},
        "env_kwargs": ENV_KWARGS,
        "rho": ENV_KWARGS.get("rho"),
    }})

    env.close()

except Exception as e:
    tb = traceback.format_exc()
    write_json(RESULTS_PATH, {{"status": "failed", "error": str(e), "traceback": tb}})
    sys.exit(1)
'''
        return script

    async def _monitor_training(self, run_id: int, process: subprocess.Popen, output_dir: str):
        """Monitor a background training process and update DB on completion."""
        try:
            elapsed = 0
            poll_interval = 5

            while process.poll() is None:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                if elapsed >= self.MAX_TRAINING_TIME:
                    logger.warning("Training run %d exceeded max time (%ds), killing", run_id, self.MAX_TRAINING_TIME)
                    process.kill()
                    process.wait()
                    break

            exit_code = process.returncode
            stdout, stderr = process.communicate(timeout=10)

            results = {}
            curve = []

            results_path = os.path.join(output_dir, "results.json")
            curve_path = os.path.join(output_dir, "curve.json")

            if os.path.exists(results_path):
                try:
                    with open(results_path) as f:
                        results = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.error("Failed to read results for run %d: %s", run_id, e)

            if os.path.exists(curve_path):
                try:
                    with open(curve_path) as f:
                        curve = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.error("Failed to read curve for run %d: %s", run_id, e)

            status = results.get("status", "failed") if results else "failed"
            if exit_code != 0 and status != "failed":
                status = "failed"
            if elapsed >= self.MAX_TRAINING_TIME and status != "failed":
                status = "failed"
                results["error"] = f"Training exceeded maximum time limit of {self.MAX_TRAINING_TIME}s"

            if status == "failed" and not results.get("error"):
                stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""
                results["error"] = stderr_text[:2000] or f"Process exited with code {exit_code}"

            model_path = None
            best_model_zip = os.path.join(output_dir, "best_model.zip")
            if os.path.exists(best_model_zip):
                model_path = best_model_zip

            async with async_session() as db:
                result = await db.execute(
                    select(TrainingRun).where(TrainingRun.id == run_id)
                )
                run = result.scalar_one_or_none()
                if run:
                    run.status = status
                    run.results_json = json.dumps(results)
                    run.training_curve_json = json.dumps(curve) if curve else None
                    run.model_path = model_path
                    run.completed_at = datetime.utcnow()
                    await db.commit()

            logger.info(
                "Training run %d finished: status=%s, exit_code=%d",
                run_id, status, exit_code or 0,
            )

            # Email notification on training completion
            if status == "completed":
                try:
                    from app.services.email_service import email_service
                    async with async_session() as _db:
                        run_obj = (await _db.execute(
                            select(TrainingRun).where(TrainingRun.id == run_id)
                        )).scalar_one_or_none()
                        if run_obj and run_obj.env_id:
                            from app.models import RLEnvironment, User
                            env_obj = (await _db.execute(
                                select(RLEnvironment).where(RLEnvironment.id == run_obj.env_id)
                            )).scalar_one_or_none()
                            user_obj = None
                            if env_obj and env_obj.user_id:
                                user_obj = (await _db.execute(
                                    select(User).where(User.id == env_obj.user_id)
                                )).scalar_one_or_none()
                            if user_obj and user_obj.email and user_obj.email_notifications:
                                mean_reward = results.get("mean_reward") or results.get("final_reward", "N/A")
                                await email_service.send_transactional(
                                    to=user_obj.email, template="training_complete",
                                    data={
                                        "env_name": env_obj.name or "Environment",
                                        "env_id": env_obj.id,
                                        "algorithm": results.get("algorithm", "PPO"),
                                        "timesteps": results.get("total_timesteps", "?"),
                                        "mean_reward": mean_reward,
                                    },
                                    user_id=user_obj.id,
                                )
                except Exception as email_err:
                    logger.warning("Failed to send training complete email: %s", email_err)

            # Cleanup temp files but keep model and results
            for fname in ["train_script.py"]:
                fpath = os.path.join(output_dir, fname)
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except OSError:
                        pass

        except Exception as e:
            logger.exception("Error monitoring training run %d: %s", run_id, e)
            try:
                async with async_session() as db:
                    result = await db.execute(
                        select(TrainingRun).where(TrainingRun.id == run_id)
                    )
                    run = result.scalar_one_or_none()
                    if run and run.status == "running":
                        run.status = "failed"
                        run.results_json = json.dumps({"status": "failed", "error": str(e)})
                        run.completed_at = datetime.utcnow()
                        await db.commit()
            except Exception:
                logger.exception("Failed to update run %d status after monitor error", run_id)
        finally:
            self._active_processes.pop(run_id, None)
            # A slot just freed up — start the next queued run, if any.
            try:
                await self._drain_queue()
            except Exception:
                logger.exception("Failed to drain training queue after run %d", run_id)


training_service = TrainingService()
