from __future__ import annotations

from pydantic import BaseModel

from re_machine.llm import chat
from re_machine.schemas import EpistemicState, Principle, RoundScores

SYSTEM = """You propose moral principles that account for a set of moral commitments.

Given current commitments C and current theory T (possibly empty), propose ONE focused
revision to T: add, remove, generalize, split, or rewrite a single principle. Do not
rewrite the whole theory.

You will receive the verifiers' rationales from the previous round — use them as concrete
targets.

Return the FULL revised theory T' (all principles, including unchanged ones, with stable
ids — reuse existing ids for unchanged principles; mint new ids like P3, P4, ... for new
ones). Include a short proposal_diff describing the change."""


class TheoryProposal(BaseModel):
    proposal_diff: str
    theory: list[Principle]


def propose_theory(
    state: EpistemicState,
    last_scores: RoundScores | None,
) -> TheoryProposal:
    scores_block = (
        last_scores.rationales_for_inferencer()
        if last_scores is not None
        else "(no scores yet — this is the first round)"
    )
    user = (
        "Current commitments C:\n"
        f"{state.render_commitments()}\n\n"
        "Current theory T:\n"
        f"{state.render_theory()}\n\n"
        "Verifier rationales from the previous round:\n"
        f"{scores_block}\n\n"
        "Propose a revised theory T'."
    )
    return chat(SYSTEM, user, response_model=TheoryProposal)  # type: ignore[return-value]
