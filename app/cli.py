"""Chat with the bot in a terminal: `uv run python -m app.cli [--unguarded]`."""
from __future__ import annotations

import argparse

from app.bot import answer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unguarded", action="store_true", help="switch every guardrail off")
    parser.add_argument("--debug", action="store_true", help="show which guardrail fired and why")
    args = parser.parse_args()

    print("Merlion Bank assistant (fictional). Ctrl+C to quit.")
    while True:
        try:
            question = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not question:
            continue
        result = answer(question, guarded=not args.unguarded)
        print(f"bot> {result.reply}")
        if args.debug:
            print(f"     blocked_by={result.blocked_by} reason={result.reason!r}")
            print(f"     used={result.chunks_used} notes={result.retrieval_notes}")


if __name__ == "__main__":
    main()
