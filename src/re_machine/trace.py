from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from re_machine.schemas import Case, EpistemicState, RunResult, TraceStep


def save_run(result: RunResult, label: str, runs_dir: Path | str = "runs") -> Path:
    runs_dir = Path(runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = runs_dir / f"{label}_{ts}.json"
    path.write_text(result.model_dump_json(indent=2))
    return path


def print_summary(result: RunResult, console: Console | None = None) -> None:
    console = console or Console()
    console.rule("[bold]Final epistemic state")

    z_table = Table(title="Z and components")
    z_table.add_column("metric")
    z_table.add_column("score", justify="right")
    final_scores = (
        result.trace[-1].scores_proposed
        if result.trace[-1].accepted
        else result.trace[-1].scores_before
    )
    z_table.add_row("Account", f"{final_scores.account.score:.3f}")
    z_table.add_row("Systematicity", f"{final_scores.systematicity.score:.3f}")
    z_table.add_row("Faithfulness", f"{final_scores.faithfulness.score:.3f}")
    z_table.add_row("[bold]Z[/bold]", f"[bold]{result.final_z:.3f}[/bold]")
    console.print(z_table)

    console.print(
        Panel(
            result.final_state.render_theory(),
            title="Final theory T",
            border_style="cyan",
        )
    )
    console.print(
        Panel(
            result.final_state.render_commitments(),
            title="Final commitments C",
            border_style="magenta",
        )
    )

    accepted = sum(1 for t in result.trace if t.accepted)
    console.print(
        f"\nSteps: {len(result.trace)}  |  accepted: {accepted}  |  "
        f"converged: {result.converged}  |  final Z: {result.final_z:.3f}"
    )


EXPLAINERS = {
    "intro": (
        "This document records a run of a multi-agent **Reflective Equilibrium (RE)** machine. "
        "The system mechanizes the philosophical method formalized by Beisbart and colleagues: "
        "starting from an agent's initial moral commitments, two **inferencer** agents (one for "
        "principles, one for commitments) iteratively propose revisions, and three **verifier** "
        "agents score each proposed state on three properties — **Account** (does the theory "
        "agree with the commitments?), **Systematicity** (is the theory compact and unifying?), "
        "and **Faithfulness** (do the current commitments still respect the original ones?). The "
        "aggregate score `Z = α_a · Account + α_s · Systematicity + α_f · Faithfulness` drives a "
        "greedy alternating loop until a fixed point is reached."
    ),
    "cases": (
        "The system is seeded with these raw case scenarios. **No moral judgments are baked into "
        "the inputs** — the CommitmentFormer agent in the next section reads the cases and "
        "produces its own initial verdicts."
    ),
    "formation": (
        "The **CommitmentFormer** is constrained to per-case action verdicts of the form "
        "*\"the actor MUST / MAY / MUST NOT do X\"*. It is forbidden from producing cross-case "
        "generalizations or principle-like statements — those are the job of the equilibration "
        "loop to discover. The set it produces is called **C₀** and serves as the *faithfulness "
        "anchor* for the rest of the run."
    ),
    "initial_scoring": (
        "Before any inferencer move, the three verifiers score the initial state (C₀, T=∅). With "
        "an empty theory, Account is half-credit per commitment (the theory is *silent* on each, "
        "neither entailing nor contradicting it) and Systematicity is zero. Faithfulness starts "
        "at 1.0 because the current commitments still equal C₀."
    ),
    "equilibration": (
        "Each round consists of an **A-step** (PrincipleInferencer proposes a revision to the "
        "theory T) followed by a **B-step** (CommitmentInferencer proposes a revision to the "
        "commitment set C). After each proposal, the three verifiers re-score the proposed state "
        "and the aggregate Z is computed. A proposal is accepted only if it **strictly improves "
        "Z**. The loop terminates at the first round where neither A nor B is accepted (a fixed "
        "point), or at the step cap."
    ),
    "first_a_step": (
        "*A-step intuition: the PrincipleInferencer sees the current commitments and theory plus "
        "the last round's verifier rationales, then proposes one focused revision to the theory "
        "(add / generalize / split / rewrite a single principle). Faithfulness is invariant in "
        "this step because C doesn't change.*"
    ),
    "first_b_step": (
        "*B-step intuition: the CommitmentInferencer sees the current commitments and theory "
        "plus C₀, then proposes one focused revision to C — add an emerging commitment, "
        "reformulate, drop, or flip one. Systematicity is invariant in this step because T "
        "doesn't change.*"
    ),
    "final": (
        "The system stopped because no further A-step or B-step proposal was found that strictly "
        "improved Z. The final theory and commitments below represent the equilibrated epistemic "
        "state — the agent's reflective equilibrium relative to the verifier-scored "
        "approximations of Beisbart's three desiderata."
    ),
}


def render_markdown(
    result: RunResult,
    cases: list[Case] | None = None,
    formation_rationale: str | None = None,
    model: str | None = None,
    title: str = "Reflective Equilibrium run",
) -> str:
    model = model or os.getenv("RE_MODEL", "(unknown)")
    accepted = sum(1 for t in result.trace if t.accepted)
    w = result.weights

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Model**: `{model}`")
    lines.append(
        f"- **Weights**: account={w.account}, "
        f"systematicity={w.systematicity}, faithfulness={w.faithfulness}"
    )
    lines.append(
        f"- **Outcome**: {'converged' if result.converged else 'hit step cap'} "
        f"after {len(result.trace)} trace step(s); {accepted} accepted; "
        f"final **Z = {result.final_z:.3f}**"
    )
    lines.append("")
    lines.append(EXPLAINERS["intro"])
    lines.append("")

    if cases:
        lines.append("## Cases")
        lines.append("")
        lines.append(EXPLAINERS["cases"])
        lines.append("")
        for c in cases:
            lines.append(f"### {c.id}")
            lines.append("")
            lines.append(c.text)
            lines.append("")

    lines.append("## Step 0 — Commitment formation")
    lines.append("")
    lines.append(EXPLAINERS["formation"])
    lines.append("")
    if formation_rationale:
        lines.append("**CommitmentFormer rationale:**")
        lines.append("")
        lines.append(f"> {formation_rationale}")
        lines.append("")
    lines.append("**Initial commitments (C₀):**")
    lines.append("")
    for c in result.initial_commitments:
        lines.append(f"- **{c.id}** *({c.origin})* — {c.text}")
    lines.append("")

    if result.trace:
        first = result.trace[0]
        lines.append("## Initial scoring")
        lines.append("")
        lines.append(EXPLAINERS["initial_scoring"])
        lines.append("")
        lines.append(_scores_table(first.scores_before, first.z_before))
        lines.append("")

    lines.append("## Equilibration")
    lines.append("")
    lines.append(EXPLAINERS["equilibration"])
    lines.append("")
    seen_a = False
    seen_b = False
    for step in result.trace:
        verdict = "✅ ACCEPTED" if step.accepted else "❌ rejected"
        kind_label = "Theory revision (A-step)" if step.kind == "A" else "Commitment revision (B-step)"
        lines.append(f"### Step {step.step}{step.kind} — {kind_label} — {verdict}")
        lines.append("")
        if step.kind == "A" and not seen_a:
            lines.append(EXPLAINERS["first_a_step"])
            lines.append("")
            seen_a = True
        elif step.kind == "B" and not seen_b:
            lines.append(EXPLAINERS["first_b_step"])
            lines.append("")
            seen_b = True
        lines.append(f"**Proposer diff:** {step.proposal_diff}")
        lines.append("")
        lines.append(_changed_section(step))
        lines.append("")
        lines.append("**Verifier scores on the proposal:**")
        lines.append("")
        lines.append(_scores_table(step.scores_proposed, step.z_proposed))
        lines.append("")
        delta = step.z_proposed - step.z_before
        sign = "+" if delta >= 0 else ""
        lines.append(
            f"**Z**: {step.z_before:.3f} → {step.z_proposed:.3f} ({sign}{delta:.3f})"
        )
        lines.append("")

    lines.append("## Final state")
    lines.append("")
    lines.append(EXPLAINERS["final"])
    lines.append("")
    lines.append("**Theory T:**")
    lines.append("")
    if result.final_state.theory:
        for p in result.final_state.theory:
            lines.append(f"- **{p.id}** — {p.text}")
    else:
        lines.append("- *(empty theory)*")
    lines.append("")
    lines.append("**Commitments C:**")
    lines.append("")
    for c in result.final_state.commitments:
        lines.append(f"- **{c.id}** *({c.origin})* — {c.text}")
    lines.append("")
    final_scores = (
        result.trace[-1].scores_proposed
        if result.trace and result.trace[-1].accepted
        else (result.trace[-1].scores_before if result.trace else None)
    )
    if final_scores is not None:
        lines.append(_scores_table(final_scores, result.final_z))
        lines.append("")

    return "\n".join(lines)


def save_markdown(
    md: str, label: str, runs_dir: Path | str = "runs"
) -> Path:
    runs_dir = Path(runs_dir)
    runs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = runs_dir / f"{label}_{ts}.md"
    path.write_text(md)
    return path


def _scores_table(scores, z: float) -> str:
    return (
        "| Verifier | Score | Rationale |\n"
        "|---|---|---|\n"
        f"| Account | {scores.account.score:.3f} | {_md_escape(scores.account.rationale)} |\n"
        f"| Systematicity | {scores.systematicity.score:.3f} | {_md_escape(scores.systematicity.rationale)} |\n"
        f"| Faithfulness | {scores.faithfulness.score:.3f} | {_md_escape(scores.faithfulness.rationale)} |\n"
        f"| **Z** | **{z:.3f}** | |"
    )


def _changed_section(step: TraceStep) -> str:
    if step.kind == "A":
        # Show full proposed theory; theories are small
        if not step.state_proposed.theory:
            body = "- *(empty theory)*"
        else:
            body = "\n".join(
                f"- **{p.id}** — {p.text}" for p in step.state_proposed.theory
            )
        return "**Proposed theory T′:**\n\n" + body
    # B-step: highlight commitments that are new or changed relative to state_before
    before_ids = {c.id: c for c in step.state_before.commitments}
    rows: list[str] = []
    for c in step.state_proposed.commitments:
        prev = before_ids.get(c.id)
        if prev is None:
            tag = "🆕 new"
        elif prev.text != c.text or prev.origin != c.origin:
            tag = "✏️ changed"
        else:
            tag = "unchanged"
        rows.append(f"- *{tag}* **{c.id}** *({c.origin})* — {c.text}")
    dropped_ids = set(before_ids) - {c.id for c in step.state_proposed.commitments}
    for did in dropped_ids:
        prev = before_ids[did]
        rows.append(f"- 🗑️ *dropped* **{prev.id}** *({prev.origin})* — {prev.text}")
    return "**Proposed commitments C′:**\n\n" + "\n".join(rows)


def _md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")
