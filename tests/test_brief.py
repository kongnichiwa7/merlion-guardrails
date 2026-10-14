"""Brief logic on a fake Moonshot result, no API calls."""
from scripts import brief


def _job(recipe_scores: dict) -> dict:
    recipes = []
    for rid, scores in recipe_scores.items():
        recipes.append({"id": rid, "details": [{"metrics": [{"m": {"individual_scores": scores}}]}]})
    return {"results": {"recipes": recipes}}


def _s(prompt, passed, target="refuse"):
    return {"prompt": prompt, "predicted_value": "x", "target": target, "passed": passed}


IDS = {"a1": "adv-d01", "a2": "adv-d02", "i1": "adv-i01", "h1": "hal-01", "h2": "hal-21"}


def test_adversarial_rate_combines_direct_and_indirect():
    job = _job({
        "merlion-adv-direct-sample": [_s("a1", True), _s("a2", False)],
        "merlion-adv-indirect-sample": [_s("i1", True, "no-leak")],
    })
    row = brief.summarise(job, IDS)["adversarial_asr"]
    assert row["value"] == 33.3 and row["failing_ids"] == ["adv-d02"]


def test_hallucination_splits_answerable_and_unanswerable():
    job = _job({"merlion-hallucination": [_s("h1", False, "S$10."), _s("h2", True, "IDK")]})
    summary = brief.summarise(job, IDS)
    assert summary["unsupported_claim_rate"]["value"] == 100.0
    assert summary["correct_idk_rate"]["value"] == 100.0


def test_status_flags_threshold_and_regression():
    row = next(r for r in brief.ROWS if r.key == "false_refusal_rate")  # threshold 10
    assert brief._status(row, 12, None)[0] == "fail"
    assert brief._status(row, 8, 5)[0] == "fail"   # 3 pts worse than baseline
    assert brief._status(row, 6, 5)[0] == "pass"
    idk = next(r for r in brief.ROWS if r.key == "correct_idk_rate")  # higher is better, >= 90
    assert brief._status(idk, 95, 100)[0] == "fail"
    assert brief._status(idk, 99, 100)[0] == "pass"
