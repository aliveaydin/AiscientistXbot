import ast
import asyncio
import json
import logging
import subprocess
import sys
import tempfile
import os
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("sandbox")

_executor = ThreadPoolExecutor(max_workers=7)


class SandboxRunner:
    """Runs 8 automated tests on generated Gymnasium environment code."""

    TIMEOUT = 20

    async def run_all_tests(self, env_code: str) -> dict:
        """Run all 8 tests in parallel and return structured results."""
        results = []

        results.append(self._test_syntax(env_code))

        if results[0]["status"] == "fail":
            for name in ["import", "reset", "step", "obs_space", "action_space", "reward_sanity", "determinism"]:
                results.append({"name": name, "status": "fail", "detail": "Skipped due to syntax error"})
            return self._summarize(results)

        loop = asyncio.get_event_loop()
        test_names = ["import", "reset", "step", "obs_space", "action_space", "reward_sanity", "determinism"]
        tasks = [
            loop.run_in_executor(_executor, self._run_subprocess_test, env_code, name)
            for name in test_names
        ]
        parallel_results = await asyncio.gather(*tasks)
        results.extend(parallel_results)

        return self._summarize(results)

    def _test_syntax(self, code: str) -> dict:
        """Test 1: Check if code parses as valid Python."""
        try:
            ast.parse(code)
            return {"name": "syntax", "status": "pass", "detail": "Valid Python syntax"}
        except SyntaxError as e:
            return {"name": "syntax", "status": "fail", "detail": f"SyntaxError: {e.msg} at line {e.lineno}"}

    def _run_subprocess_test(self, env_code: str, test_name: str) -> dict:
        """Run a single test in an isolated subprocess."""
        test_script = self._build_test_script(env_code, test_name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            f.flush()
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True, text=True,
                timeout=self.TIMEOUT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            )

            if result.returncode == 0:
                output = result.stdout.strip().split('\n')[-1]
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    return {"name": test_name, "status": "pass", "detail": result.stdout.strip()[:200]}
            else:
                error = result.stderr.strip()[-500:] if result.stderr else "Unknown error"
                return {"name": test_name, "status": "fail", "detail": error}

        except subprocess.TimeoutExpired:
            return {"name": test_name, "status": "fail", "detail": f"Timeout after {self.TIMEOUT}s"}
        except Exception as e:
            return {"name": test_name, "status": "fail", "detail": str(e)[:200]}
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _build_test_script(self, env_code: str, test_name: str) -> str:
        """Build a self-contained Python script that runs one test."""
        escaped_code = env_code.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')

        preamble = f'''
import json, sys, os, tempfile, importlib, importlib.util, traceback

def emit(name, status, detail):
    print(json.dumps({{"name": name, "status": status, "detail": str(detail)[:500]}}), flush=True)
    sys.exit(0)

ENV_CODE = """{escaped_code}"""

try:
    import gymnasium
    import numpy as np
except ImportError as e:
    emit("{test_name}", "fail", f"Missing dependency: {{e}}")

# Write env code to a temp module and import it
_tmp_dir = tempfile.mkdtemp()
_mod_path = os.path.join(_tmp_dir, "_sandbox_env.py")
with open(_mod_path, "w") as _f:
    _f.write(ENV_CODE)

spec = importlib.util.spec_from_file_location("_sandbox_env", _mod_path)
_mod = importlib.util.module_from_spec(spec)

try:
    spec.loader.exec_module(_mod)
except Exception as e:
    emit("{test_name}", "fail", f"Import error: {{type(e).__name__}}: {{e}}")

# Find the Env class (subclass of gymnasium.Env)
_env_cls = None
for _attr_name in dir(_mod):
    _obj = getattr(_mod, _attr_name)
    if isinstance(_obj, type) and issubclass(_obj, gymnasium.Env) and _obj is not gymnasium.Env:
        _env_cls = _obj
        break

if _env_cls is None:
    emit("{test_name}", "fail", "No gymnasium.Env subclass found in code")

try:
    _env = _env_cls()
except Exception as e:
    emit("{test_name}", "fail", f"Instantiation error: {{type(e).__name__}}: {{e}}")

try:
'''

        cleanup = '''
except Exception as e:
    emit("{test_name}", "fail", f"{{type(e).__name__}}: {{e}}")
finally:
    try:
        os.unlink(_mod_path)
        os.rmdir(_tmp_dir)
    except OSError:
        pass
'''.replace("{test_name}", test_name)

        test_body = self._get_test_body(test_name)

        return preamble + test_body + "\n" + cleanup

    def _get_test_body(self, test_name: str) -> str:
        """Return the test-specific logic as indented code (inside try block)."""
        tests = {
            "import": self._script_test_import,
            "reset": self._script_test_reset,
            "step": self._script_test_step,
            "obs_space": self._script_test_obs_space,
            "action_space": self._script_test_action_space,
            "reward_sanity": self._script_test_reward_sanity,
            "determinism": self._script_test_determinism,
        }
        return tests[test_name]()

    @staticmethod
    def _script_test_import() -> str:
        return '''
    if not hasattr(_env, 'observation_space'):
        emit("import", "fail", "Env missing observation_space attribute")
    if not hasattr(_env, 'action_space'):
        emit("import", "fail", "Env missing action_space attribute")
    emit("import", "pass", f"Env class {_env_cls.__name__} imported and instantiated successfully")
'''

    @staticmethod
    def _script_test_reset() -> str:
        return '''
    result = _env.reset(seed=42)
    if not isinstance(result, tuple):
        emit("reset", "fail", f"reset() returned {type(result).__name__}, expected tuple")
    if len(result) != 2:
        emit("reset", "fail", f"reset() returned tuple of length {len(result)}, expected 2")
    obs, info = result
    if not isinstance(obs, np.ndarray):
        emit("reset", "fail", f"obs is {type(obs).__name__}, expected numpy.ndarray")
    if not isinstance(info, dict):
        emit("reset", "fail", f"info is {type(info).__name__}, expected dict")
    emit("reset", "pass", f"reset() returns (ndarray shape={obs.shape}, dict) correctly")
'''

    @staticmethod
    def _script_test_step() -> str:
        return '''
    _env.reset(seed=42)
    action = _env.action_space.sample()
    result = _env.step(action)
    if not isinstance(result, tuple):
        emit("step", "fail", f"step() returned {type(result).__name__}, expected tuple")
    if len(result) != 5:
        emit("step", "fail", f"step() returned tuple of length {len(result)}, expected 5 (obs, reward, terminated, truncated, info)")
    obs, reward, terminated, truncated, info = result
    errors = []
    if not isinstance(obs, np.ndarray):
        errors.append(f"obs is {type(obs).__name__}, expected ndarray")
    if not isinstance(reward, (int, float, np.integer, np.floating)):
        errors.append(f"reward is {type(reward).__name__}, expected numeric")
    if not isinstance(terminated, (bool, np.bool_)):
        errors.append(f"terminated is {type(terminated).__name__}, expected bool")
    if not isinstance(truncated, (bool, np.bool_)):
        errors.append(f"truncated is {type(truncated).__name__}, expected bool")
    if not isinstance(info, dict):
        errors.append(f"info is {type(info).__name__}, expected dict")
    if errors:
        emit("step", "fail", "; ".join(errors))
    emit("step", "pass", f"step() returns correct 5-tuple (obs shape={obs.shape}, reward={reward})")
'''

    @staticmethod
    def _script_test_obs_space() -> str:
        return '''
    obs, _ = _env.reset(seed=42)
    if not _env.observation_space.contains(obs):
        emit("obs_space", "fail", f"Initial obs not contained in observation_space. obs={obs}, space={_env.observation_space}")
    failures = []
    for i in range(10):
        action = _env.action_space.sample()
        obs, _, terminated, truncated, _ = _env.step(action)
        if not _env.observation_space.contains(obs):
            failures.append(i)
        if terminated or truncated:
            obs, _ = _env.reset(seed=42)
    if failures:
        emit("obs_space", "fail", f"Observation out of space at steps: {failures}")
    emit("obs_space", "pass", "All observations contained in observation_space (10 steps checked)")
'''

    @staticmethod
    def _script_test_action_space() -> str:
        return '''
    for i in range(100):
        a = _env.action_space.sample()
        if not _env.action_space.contains(a):
            emit("action_space", "fail", f"Sampled action not in action_space at iteration {i}: {a}")
    _env.reset(seed=42)
    action = _env.action_space.sample()
    _env.step(action)
    emit("action_space", "pass", "100 sampled actions valid, step() with sampled action succeeded")
'''

    @staticmethod
    def _script_test_reward_sanity() -> str:
        return '''
    _env.reset(seed=42)
    rewards = []
    for i in range(100):
        action = _env.action_space.sample()
        _, reward, terminated, truncated, _ = _env.step(action)
        if not isinstance(reward, (int, float, np.integer, np.floating)):
            emit("reward_sanity", "fail", f"Reward at step {i} is {type(reward).__name__}, not numeric")
        r = float(reward)
        if np.isnan(r):
            emit("reward_sanity", "fail", f"NaN reward at step {i}")
        if np.isinf(r):
            emit("reward_sanity", "fail", f"Inf reward at step {i}")
        rewards.append(r)
        if terminated or truncated:
            _env.reset(seed=42)
    if len(set(rewards)) == 1:
        emit("reward_sanity", "fail", f"All 100 rewards identical ({rewards[0]}), environment may not be functional")
    detail = f"100 rewards collected: min={min(rewards):.4f}, max={max(rewards):.4f}, mean={sum(rewards)/len(rewards):.4f}"
    outside = [r for r in rewards if r < -10 or r > 10]
    if outside:
        detail += f" (warning: {len(outside)} values outside [-10, 10])"
    emit("reward_sanity", "pass", detail)
'''

    @staticmethod
    def _script_test_determinism() -> str:
        return '''
    def run_trajectory(seed, steps):
        _env.reset(seed=seed)
        obs_list, rew_list = [], []
        obs, _ = _env.reset(seed=seed)
        obs_list.append(obs.tolist())
        for _ in range(steps):
            action = _env.action_space.sample()
            obs, reward, terminated, truncated, _ = _env.step(action)
            obs_list.append(obs.tolist())
            rew_list.append(float(reward))
            if terminated or truncated:
                break
        return obs_list, rew_list

    # Need deterministic action sampling too, so reset action_space rng
    _env.action_space.seed(42)
    obs1, rew1 = run_trajectory(42, 20)
    _env.action_space.seed(42)
    obs2, rew2 = run_trajectory(42, 20)

    if len(obs1) != len(obs2):
        emit("determinism", "fail", f"Trajectory lengths differ: {len(obs1)} vs {len(obs2)}")
    obs_match = all(o1 == o2 for o1, o2 in zip(obs1, obs2))
    rew_match = rew1 == rew2
    if not obs_match:
        for i, (o1, o2) in enumerate(zip(obs1, obs2)):
            if o1 != o2:
                emit("determinism", "fail", f"Observations diverge at step {i}")
    if not rew_match:
        for i, (r1, r2) in enumerate(zip(rew1, rew2)):
            if r1 != r2:
                emit("determinism", "fail", f"Rewards diverge at step {i}: {r1} vs {r2}")
    emit("determinism", "pass", f"Trajectories match over {len(rew1)} steps with seed=42")
'''

    def _summarize(self, results: List[dict]) -> dict:
        passed = sum(1 for r in results if r["status"] == "pass")
        return {
            "passed": passed,
            "failed": len(results) - passed,
            "total": len(results),
            "tests": results,
        }


sandbox_runner = SandboxRunner()
