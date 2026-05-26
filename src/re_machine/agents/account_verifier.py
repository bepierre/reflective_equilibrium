from __future__ import annotations

from pydantic import BaseModel, confloat

from re_machine.llm import chat
from re_machine.schemas import EpistemicState, VerifierScore

SYSTEM = """You score Account: how well theory T agrees with commitments C.

For EACH commitment in C, assign a score in [0, 1]:
  1.0  T clearly entails / supports the commitment.
  0.5  T is silent on the commitment, or only partially supports it.
  0.0  T contradicts the commitment (T entails its negation).

Return a per-commitment list of judgments with a 1-sentence note each, naming
specific principles by id where relevant."""


class AccountItem(BaseModel):
    commitment_id: str
    score: confloat(ge=0.0, le=1.0)  # type: ignore[valid-type]
    note: str


class AccountReport(BaseModel):
    items: list[AccountItem]


def score_account(state: EpistemicState) -> VerifierScore:
    user = (
        "Commitments C:\n"
        f"{state.render_commitments()}\n\n"
        "Theory T:\n"
        f"{state.render_theory()}\n\n"
        "Score Account per commitment."
    )
    report: AccountReport = chat(SYSTEM, user, response_model=AccountReport)  # type: ignore[assignment]
    if not report.items:
        return VerifierScore(score=0.0, rationale="(no items returned)")
    avg = sum(it.score for it in report.items) / len(report.items)
    summary = "  |  ".join(f"{it.commitment_id}={it.score:.1f}: {it.note}" for it in report.items)
    return VerifierScore(score=avg, rationale=summary)
