from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from re_machine.llm import chat
from re_machine.schemas import Commitment, EpistemicState, VerifierScore

SYSTEM = """You score Faithfulness: how well current commitments C respect the agent's
original commitments C₀.

For EACH original commitment in C₀, classify its status in the current C:
  PRESERVED     — held verbatim or essentially unchanged.
  REFORMULATED  — a variant is held that preserves the original's spirit.
  DROPPED       — no longer held in any form (C is silent on it).
  DENIED        — the negation is held instead.

Return a per-IC list with a 1-sentence note each."""


Status = Literal["preserved", "reformulated", "dropped", "denied"]

_STATUS_SCORES: dict[str, float] = {
    "preserved": 1.0,
    "reformulated": 0.8,
    "dropped": 0.3,
    "denied": 0.0,
}


class FaithfulnessItem(BaseModel):
    initial_commitment_id: str
    status: Status
    note: str


class FaithfulnessReport(BaseModel):
    items: list[FaithfulnessItem]


def score_faithfulness(
    state: EpistemicState, initial_commitments: list[Commitment]
) -> VerifierScore:
    rendered_initial = "\n".join(f"- [{c.id}] {c.text}" for c in initial_commitments)
    user = (
        "Initial commitments C₀:\n"
        f"{rendered_initial}\n\n"
        "Current commitments C:\n"
        f"{state.render_commitments()}\n\n"
        "Classify the status of each original commitment in C."
    )
    report: FaithfulnessReport = chat(SYSTEM, user, response_model=FaithfulnessReport)  # type: ignore[assignment]
    if not report.items:
        return VerifierScore(score=0.0, rationale="(no items returned)")
    avg = sum(_STATUS_SCORES[it.status] for it in report.items) / len(report.items)
    summary = "  |  ".join(
        f"{it.initial_commitment_id}={it.status} ({_STATUS_SCORES[it.status]:.1f}): {it.note}"
        for it in report.items
    )
    return VerifierScore(score=avg, rationale=summary)
