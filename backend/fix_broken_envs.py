import asyncio
import json
import sqlite3

from app.services.sandbox_runner import sandbox_runner
from app.services.architect_service import architect_service, PASS_THRESHOLD

DB = "/app/data/bot.db"
TARGET = [1, 2, 3, 4, 5, 6, 7, 8, 12, 14, 20, 21, 22, 23, 26, 28, 33, 37, 38, 39, 40, 41, 42]


async def main():
    c = sqlite3.connect(DB)
    for eid in TARGET:
        row = c.execute(
            "select code, env_spec_json, status from rl_environments where id=?", (eid,)
        ).fetchone()
        if not row:
            print(f"#{eid} missing", flush=True)
            continue
        code, spec, status = row[0], (row[1] or "{}"), row[2]
        if not code or "class" not in code:
            print(f"#{eid} no usable code, skip", flush=True)
            continue
        try:
            res = await sandbox_runner.run_all_tests(code)
        except Exception as e:
            print(f"#{eid} test error: {e}", flush=True)
            continue

        if res["passed"] == res["total"] and res["total"]:
            c.execute(
                "update rl_environments set test_results_json=? where id=?",
                (json.dumps(res), eid),
            )
            c.commit()
            print(f"#{eid} already {res['passed']}/{res['total']} (persisted)", flush=True)
            continue

        try:
            nc, nr, log = await architect_service.auto_fix_until_passing(
                code, spec, res, max_attempts=4
            )
        except Exception as e:
            print(f"#{eid} fix error: {e}", flush=True)
            continue

        new_status = "published" if nr["passed"] >= PASS_THRESHOLD else "draft"
        c.execute(
            "update rl_environments set code=?, test_results_json=?, status=?, "
            "generation_log=?, ai_model_used=? where id=?",
            (nc, json.dumps(nr), new_status, "\n".join(log), "claude-opus-4-8", eid),
        )
        c.commit()
        print(
            f"#{eid} {res['passed']}->{nr['passed']}/{nr['total']} status={new_status}",
            flush=True,
        )
    c.close()
    print("DONE", flush=True)


asyncio.run(main())
