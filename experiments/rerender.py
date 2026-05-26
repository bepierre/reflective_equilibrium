"""Re-render the markdown writeup from a previously saved JSON trace.

Useful when render_markdown() has been updated (e.g., new explainers) and you don't
want to spend API calls re-running the experiment.

Usage:
    python -m experiments.rerender runs/trolley_<timestamp>.json \\
        --model google/gemini-2.0-flash-001
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from re_machine.schemas import RunResult
from re_machine.trace import render_markdown
from experiments.trolley import TROLLEY_CASES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--model", default="(unknown)")
    parser.add_argument(
        "--rationale",
        default="(formation rationale not stored in this trace)",
        help="The original CommitmentFormer rationale to inline in the markdown.",
    )
    parser.add_argument("--title", default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    result = RunResult.model_validate_json(args.json_path.read_text())
    title = args.title or f"Reflective Equilibrium run — trolley ({args.model})"
    md = render_markdown(
        result,
        cases=TROLLEY_CASES,
        formation_rationale=args.rationale,
        model=args.model,
        title=title,
    )
    out = args.out or args.json_path.with_suffix(".md")
    out.write_text(md)
    print(f"wrote {out}  ({len(md)} chars)")


if __name__ == "__main__":
    main()
