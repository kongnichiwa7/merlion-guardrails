# Merlion Bank guardrails

Guardrails for an LLM support chatbot, tested against Singapore IMDA's *Starter Kit for Testing LLM-Based Applications for Safety and Reliability* (v1.0, Jan 2026) with IMDA's **Project Moonshot**.

> **Merlion Bank is fictional.** All documents, fees, names, IDs and account numbers are synthetic test data. See [data/README.md](data/README.md).

## How it works

```
question ─► input filter ─► BM25 retrieval ─► retrieval sanitiser ─► Gemini ─► output filter ─► reply
            rules +                            deny list,                       secrets, NRIC,
            injection classifier               hidden-text strip, rules         account no., ungrounded numbers
```

| Guardrail | File | IMDA risks |
|---|---|---|
| Hardened system prompt | [prompts/system.md](prompts/system.md) | all |
| Input filter | [guardrails/input_filter.py](guardrails/input_filter.py) | Adversarial prompts |
| Retrieval sanitiser | [guardrails/retrieval_sanitiser.py](guardrails/retrieval_sanitiser.py) | Adversarial prompts (indirect), data leakage |
| Output filter | [guardrails/output_filter.py](guardrails/output_filter.py) | Data leakage, hallucination |

`GUARDRAILS=off` switches all of them off, so the suite can measure what they buy.

## Run it

```bash
uv sync
cp .env.example .env   # then add your GEMINI_API_KEY
uv run pytest          # offline unit tests, no key needed
uv run python -m app.cli --debug
```

## Findings log

1. **The injection classifier over-blocks bank documents.** Run over the FAQ store, `protectai/deberta-v3-base-prompt-injection-v2` scored five clean sections (scams, OTP safety, app login) at 0.97 to 1.00. Those pages are written as instructions ("Freeze your card…", "Call…"), and the model was trained on user prompts. Fix: the classifier screens user input only; documents go through a deny list, hidden-text stripping and pattern rules. A regression test keeps the pages in.

*Work in progress: the Moonshot test suite, CI loop and IMDA mapping are next.*
