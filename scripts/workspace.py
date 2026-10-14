"""Assemble the Moonshot workspace: this repo's assets + the few moonshot-data pieces we reuse.

moonshot-data (pinned tag) is cloned to moonshot/.vendor by `make vendor`. From it we take
the framework modules (runners, results, io, databases), the built-in `refusal` metric and
the built-in `jailbreak-prompts` recipe + dataset. Everything else comes from moonshot/.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / "moonshot"
VENDOR = MS / ".vendor" / "moonshot-data"
WORKSPACE = MS / ".workspace"
RUNS = MS / ".runs"
MOONSHOT_DATA_TAG = "0.7.6"

BUILTIN_RECIPE = "jailbreak-prompts"
BUILTIN_DATASET = "prompt_injection_jailbreak"
JUDGE_ENDPOINT = "merlion-judge"


def _copy_dir(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.is_file():
            shutil.copy2(f, dst / f.name)


def _metrics_config() -> dict:
    rubric = lambda name: (MS / "rubrics" / f"{name}.md").read_text()
    judge = {"endpoints": [JUDGE_ENDPOINT]}
    return {
        "refusal": {"endpoints": ["refusal-evaluator"]},
        "merlion-refusal": {**judge, "configurations": {"rubric": rubric("refusal")}},
        "merlion-harm": {**judge, "configurations": {"rubric": rubric("harm")}},
        "merlion-groundedness": {**judge, "configurations": {"rubric": rubric("groundedness")}},
        "merlion-leakage": {},
        "merlion-label-match": {},
    }


def _refusal_evaluator() -> dict:
    """Moonshot's own refusal-evaluator endpoint, re-pointed from GPT-4o to our Gemini judge."""
    stock = json.loads((VENDOR / "connectors-endpoints" / "refusal-evaluator.json").read_text())
    ours = json.loads((MS / "connectors-endpoints" / f"{JUDGE_ENDPOINT}.json").read_text())
    return {**ours, "name": "Refusal Evaluator (Gemini)", "params": {**ours["params"], "system_prompt": stock["params"]["system_prompt"]}}


def build() -> dict:
    """(Re)build the workspace and return the env dict for api_set_environment_variables."""
    if not VENDOR.exists():
        raise SystemExit(f"moonshot-data missing: run `make vendor` (clones tag {MOONSHOT_DATA_TAG})")
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    for name in ("connectors", "connectors-endpoints", "datasets", "recipes", "cookbooks", "metrics"):
        _copy_dir(MS / name, WORKSPACE / name)
    (WORKSPACE / "prompt-templates").mkdir()

    shutil.copy2(VENDOR / "metrics" / "refusal.py", WORKSPACE / "metrics" / "refusal.py")
    shutil.copy2(VENDOR / "recipes" / f"{BUILTIN_RECIPE}.json", WORKSPACE / "recipes")
    shutil.copy2(VENDOR / "datasets" / f"{BUILTIN_DATASET}.json", WORKSPACE / "datasets")
    (WORKSPACE / "metrics" / "metrics_config.json").write_text(json.dumps(_metrics_config(), indent=2))
    (WORKSPACE / "connectors-endpoints" / "refusal-evaluator.json").write_text(
        json.dumps(_refusal_evaluator(), indent=2)
    )

    for sub in ("databases", "results", "runners", "bookmarks"):
        (RUNS / sub).mkdir(parents=True, exist_ok=True)

    return {
        "ATTACK_MODULES": str(VENDOR / "attack-modules"),
        "BOOKMARKS": str(RUNS / "bookmarks"),
        "CONNECTORS": str(WORKSPACE / "connectors"),
        "CONNECTORS_ENDPOINTS": str(WORKSPACE / "connectors-endpoints"),
        "CONTEXT_STRATEGY": str(VENDOR / "context-strategy"),
        "COOKBOOKS": str(WORKSPACE / "cookbooks"),
        "DATABASES": str(RUNS / "databases"),
        "DATABASES_MODULES": str(VENDOR / "databases-modules"),
        "DATASETS": str(WORKSPACE / "datasets"),
        "IO_MODULES": str(VENDOR / "io-modules"),
        "METRICS": str(WORKSPACE / "metrics"),
        "PROMPT_TEMPLATES": str(WORKSPACE / "prompt-templates"),
        "RECIPES": str(WORKSPACE / "recipes"),
        "RESULTS": str(RUNS / "results"),
        "RESULTS_MODULES": str(VENDOR / "results-modules"),
        "RUNNERS": str(RUNS / "runners"),
        "RUNNERS_MODULES": str(VENDOR / "runners-modules"),
    }
