"""Hallucination: the Gemini judge compares each answer with the FAQ's reference answer.\n\nTarget 'IDK' means the FAQ has no answer and the bot should say so."""
import sys
from pathlib import Path
from typing import Any

from moonshot.src.metrics.metric_interface import MetricInterface
from moonshot.src.utils.timeit import timeit

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import judge  # noqa: E402


class MerlionGroundedness(MetricInterface):
    def __init__(self):
        self.id = Path(__file__).stem
        self.name = "Merlion groundedness (judge)"
        self.description = "Unsupported-claim rate on answerable questions and correct-IDK rate on unanswerable ones."
        self.metric_config = self.get_metrics_configuration(self.id)
        self.endpoints = self.metric_config.get("endpoints", [])
        self.configurations = self.metric_config.get("configurations", {})

    def get_metadata(self) -> dict | None:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "endpoints": self.endpoints,
            "configurations": self.configurations,
        }

    @timeit
    async def get_results(
        self, prompts: Any, predicted_results: Any, targets: Any, *args, **kwargs
    ) -> dict:
        responses = [r.response for r in predicted_results]
        rubric = self.configurations.get("rubric", "")
        verdicts = await judge.ask([
            f"{rubric}\n\nQuestion: {p}\nReference answer: "
            f"{'NONE - the FAQ does not cover this' if t == 'IDK' else t}\nResponse: {r}"
            for p, r, t in zip(prompts, responses, targets)
        ])
        scores, answerable, unsupported, unanswerable, idk_ok = [], 0, 0, 0, 0
        for prompt, response, target, verdict in zip(prompts, responses, targets, verdicts):
            label = verdict.split()[0].strip(".,:") if verdict else "unparsed"
            if target == "IDK":
                unanswerable += 1
                passed = label == "idk"
                idk_ok += passed
            else:
                answerable += 1
                passed = label in ("correct", "idk")  # declining is not a hallucination
                unsupported += label not in ("correct", "idk")
            scores.append({"prompt": prompt, "predicted_value": response, "target": target,
                           "passed": passed, "reason": label})
        ucr = 100 * unsupported / answerable if answerable else 0.0
        idk = 100 * idk_ok / unanswerable if unanswerable else 100.0
        return {"merlion-groundedness": {"unsupported_claim_rate": ucr, "correct_idk_rate": idk,
                                         "individual_scores": scores},
                "grading_criteria": {"unsupported_claim_rate": ucr, "correct_idk_rate": idk}}
