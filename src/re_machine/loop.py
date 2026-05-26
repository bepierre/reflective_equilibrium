from __future__ import annotations

from rich.console import Console

from re_machine.agents import (
    propose_commitments,
    propose_theory,
    score_account,
    score_faithfulness,
    score_systematicity,
)
from re_machine.schemas import (
    Commitment,
    EpistemicState,
    RoundScores,
    RunResult,
    TraceStep,
    Weights,
)


def _verify(
    state: EpistemicState, initial_commitments: list[Commitment]
) -> RoundScores:
    return RoundScores(
        account=score_account(state),
        systematicity=score_systematicity(state),
        faithfulness=score_faithfulness(state, initial_commitments),
    )


def equilibrate(
    initial_commitments: list[Commitment],
    weights: Weights | None = None,
    max_steps: int = 12,
    console: Console | None = None,
) -> RunResult:
    weights = weights or Weights()
    console = console or Console()

    state = EpistemicState(commitments=list(initial_commitments), theory=[])
    scores = _verify(state, initial_commitments)
    z = scores.z(weights)
    console.print(f"[bold]Initial Z[/bold] = {z:.3f}")
    console.print(scores.rationales_for_inferencer())

    trace: list[TraceStep] = []
    converged = False

    for step in range(1, max_steps + 1):
        accepted_this_round = False

        # ── A-step: theory revision ──
        console.rule(f"[bold cyan]Step {step}A — theory revision")
        proposal_t = propose_theory(state, scores)
        proposed_state_t = EpistemicState(
            commitments=state.commitments, theory=proposal_t.theory
        )
        scores_t = _verify(proposed_state_t, initial_commitments)
        z_t = scores_t.z(weights)
        accept_t = z_t > z
        console.print(f"proposed Z = {z_t:.3f}  (was {z:.3f})  → {'ACCEPT' if accept_t else 'reject'}")
        console.print(f"diff: {proposal_t.proposal_diff}")
        trace.append(
            TraceStep(
                step=step,
                kind="A",
                state_before=state,
                state_proposed=proposed_state_t,
                scores_before=scores,
                scores_proposed=scores_t,
                z_before=z,
                z_proposed=z_t,
                accepted=accept_t,
                proposal_diff=proposal_t.proposal_diff,
            )
        )
        if accept_t:
            state = proposed_state_t
            scores = scores_t
            z = z_t
            accepted_this_round = True

        # ── B-step: commitment revision ──
        console.rule(f"[bold magenta]Step {step}B — commitment revision")
        proposal_c = propose_commitments(state, initial_commitments, scores)
        proposed_state_c = EpistemicState(
            commitments=proposal_c.commitments, theory=state.theory
        )
        scores_c = _verify(proposed_state_c, initial_commitments)
        z_c = scores_c.z(weights)
        accept_c = z_c > z
        console.print(f"proposed Z = {z_c:.3f}  (was {z:.3f})  → {'ACCEPT' if accept_c else 'reject'}")
        console.print(f"diff: {proposal_c.proposal_diff}")
        trace.append(
            TraceStep(
                step=step,
                kind="B",
                state_before=state,
                state_proposed=proposed_state_c,
                scores_before=scores,
                scores_proposed=scores_c,
                z_before=z,
                z_proposed=z_c,
                accepted=accept_c,
                proposal_diff=proposal_c.proposal_diff,
            )
        )
        if accept_c:
            state = proposed_state_c
            scores = scores_c
            z = z_c
            accepted_this_round = True

        if not accepted_this_round:
            console.print(f"[bold green]Fixed point reached after step {step}.[/bold green]")
            converged = True
            break

    return RunResult(
        final_state=state,
        initial_commitments=list(initial_commitments),
        weights=weights,
        trace=trace,
        converged=converged,
        final_z=z,
    )
