"""Run the Merlion test suite with Moonshot and write one combined results file.

  uv run python -m scripts.run_suite --suite sample          # quick
  uv run python -m scripts.run_suite --suite full --unguarded

Jobs (each is a Moonshot runner):
  components  - each component recipe against its own guardrail endpoint (no model calls)
  output      - the merlion-imda cookbook against merlion-bot
  builtin     - Moonshot's jailbreak-prompts recipe (a fixed 1% sample) against merlion-bot
  unguarded   - the cookbook against merlion-bot-unguarded (only with --unguarded)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from scripts import workspace
from scripts.build_suite import COMPONENT_RECIPES

SEED = 42
BUILTIN_PERCENT = 1  # of 3,600 jailbreak prompts -> 36


def _run(name: str, endpoints: list[str], recipes: list[str] = (), cookbooks: list[str] = (),
         percent: int = 100) -> dict:
    from moonshot.api import api_create_runner, api_delete_runner, api_get_all_run, api_get_all_runner_name
    from slugify import slugify

    runner_id = slugify(name, lowercase=True)
    if runner_id in api_get_all_runner_name():
        api_delete_runner(runner_id)
    runner = api_create_runner(name, endpoints)

    async def go():
        if cookbooks:
            await runner.run_cookbooks(list(cookbooks), percent, SEED)
        else:
            await runner.run_recipes(list(recipes), percent, SEED)
        await runner.close()

    asyncio.run(go())
    results = api_get_all_run(runner.id)[-1].get("results")
    if not results:
        raise RuntimeError(f"Moonshot produced no results for job {name}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=["full", "sample"], default="full")
    parser.add_argument("--unguarded", action="store_true")
    parser.add_argument("--skip-builtin", action="store_true")
    parser.add_argument("--out", type=Path, default=workspace.RUNS / "latest.json")
    args = parser.parse_args()

    from moonshot.api import api_set_environment_variables

    api_set_environment_variables(workspace.build())
    cookbook = "merlion-imda" if args.suite == "full" else "merlion-imda-sample"
    started = time.time()
    jobs = {}

    for recipe, endpoint in COMPONENT_RECIPES.items():
        jobs[f"component:{recipe}"] = _run(f"merlion {recipe}", [endpoint], recipes=[recipe])
    jobs["output"] = _run("merlion output", ["merlion-bot"], cookbooks=[cookbook])
    if not args.skip_builtin:
        jobs["builtin"] = _run("merlion builtin", ["merlion-bot"], recipes=[workspace.BUILTIN_RECIPE],
                               percent=BUILTIN_PERCENT)
    if args.unguarded:
        jobs["unguarded"] = _run("merlion unguarded", ["merlion-bot-unguarded"], cookbooks=[cookbook])

    from app import llm

    combined = {
        "suite": args.suite,
        "unguarded": args.unguarded,
        "api_calls": dict(llm.CALLS),
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_s": round(time.time() - started),
        "jobs": jobs,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(combined, indent=2, default=str))
    print(f"results written to {args.out}")


if __name__ == "__main__":
    main()
