"""Run the Reflective Equilibrium machine on five trolley cases.

Seed: five RAW case scenarios (no moral judgments baked in). The CommitmentFormer agent
reads the cases and forms freeform initial commitments C₀. Then the equilibration loop
takes over.

Usage:
    python -m experiments.trolley
    python -m experiments.trolley --markdown    # also save a markdown writeup
"""
from __future__ import annotations

import argparse
import os

from rich.console import Console
from rich.panel import Panel

from re_machine import Case, Weights, equilibrate
from re_machine.agents import form_commitments
from re_machine.trace import print_summary, render_markdown, save_markdown, save_run


TROLLEY_CASES: list[Case] = [
    Case(
        id="Case1",
        text=(
            "A judge in a small town presides over a case in which an angry mob has "
            "threatened to kill five hostages unless an innocent person is convicted "
            "for a crime they did not commit. The judge has the power to frame the "
            "innocent person and ensure their conviction, which would satisfy the mob "
            "and save the five hostages. If the judge refuses, the mob will kill the "
            "five hostages."
        ),
    ),
    Case(
        id="Case2",
        text=(
            "The driver of a runaway trolley with failed brakes is heading toward five "
            "workmen on the track ahead. The driver can either continue straight, in "
            "which case the five workmen will be killed, or steer onto a side track on "
            "which only one workman is working, killing that one workman instead."
        ),
    ),
    Case(
        id="Case3",
        text=(
            "A bystander is standing next to a switch that controls the direction of a "
            "runaway trolley. If the bystander does nothing, the trolley will continue "
            "down the main track and kill five workmen. If the bystander throws the "
            "switch, the trolley will divert onto a side track on which only one "
            "workman is working, killing that one workman instead."
        ),
    ),
    Case(
        id="Case4",
        text=(
            "A bystander is standing on a bridge over a trolley track. A runaway trolley "
            "is heading toward five workmen on the track below. The only way to stop the "
            "trolley before it reaches the five workmen is for the bystander to push a "
            "very heavy man, who is also on the bridge, down onto the track. The heavy "
            "man's body would stop the trolley and save the five workmen, but the heavy "
            "man would be killed by the impact."
        ),
    ),
    Case(
        id="Case5",
        text=(
            "A bystander is standing next to a switch with three positions. A runaway "
            "trolley is approaching. If the bystander does nothing, the trolley will "
            "continue down the main track and kill five workmen. If the bystander throws "
            "the switch one way, the trolley will divert onto a side track and kill one "
            "workman. If the bystander throws the switch the other way, the trolley will "
            "divert onto a different side track and kill five workmen."
        ),
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Also save a human-readable markdown writeup of the run to runs/.",
    )
    args = parser.parse_args()

    console = Console()
    console.rule("[bold]Reflective Equilibrium machine — trolley replication")
    console.print(
        f"Seeding with {len(TROLLEY_CASES)} raw trolley case scenarios.\n"
        "Step 0: CommitmentFormer reads the cases and forms freeform C₀.\n"
        "Then two inferencers + three verifiers iterate until fixed point.\n"
    )

    console.rule("[bold yellow]Step 0 — initial commitment formation")
    formed = form_commitments(TROLLEY_CASES)
    console.print(
        Panel(formed.rationale, title="CommitmentFormer rationale", border_style="yellow")
    )
    for c in formed.commitments:
        console.print(f"  [{c.id}] ({c.origin}) {c.text}")
    console.print(f"\n→ {len(formed.commitments)} initial commitments formed.\n")

    result = equilibrate(
        initial_commitments=formed.commitments,
        weights=Weights(account=0.5, systematicity=0.25, faithfulness=0.25),
        max_steps=12,
        console=console,
    )
    print_summary(result, console=console)
    json_path = save_run(result, label="trolley")
    console.print(f"\nSaved trace to {json_path}")

    if args.markdown:
        md = render_markdown(
            result,
            cases=TROLLEY_CASES,
            formation_rationale=formed.rationale,
            model=os.getenv("RE_MODEL"),
            title="Reflective Equilibrium run — trolley",
        )
        md_path = save_markdown(md, label="trolley")
        console.print(f"Saved markdown writeup to {md_path}")


if __name__ == "__main__":
    main()
