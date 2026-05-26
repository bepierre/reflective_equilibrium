from __future__ import annotations

from pydantic import BaseModel

from re_machine.llm import chat
from re_machine.schemas import Commitment, EpistemicState, RoundScores

SYSTEM = """You revise an agent's moral commitments in light of a theory.

Given current commitments C, current theory T, and the agent's original commitments C₀,
propose ONE focused revision to C. The available moves are:

  - ADD an emerging commitment (a new case verdict the agent now accepts).
  - REFORMULATE an existing commitment (preserve the original's spirit).
  - DROP an existing commitment (faithfulness cost).
  - FLIP an existing commitment to its negation (largest faithfulness cost).

You will receive the verifiers' rationales from the previous round — use them as concrete
targets.

Return the FULL revised commitment set C' (all commitments, with stable ids and origin =
initial / emerging / inferred). Reuse ids for unchanged commitments; mint new ids (EC1,
EC2, ..., NC1, NC2, ...) for new ones. Include a short proposal_diff describing the change."""


class CommitmentProposal(BaseModel):
    proposal_diff: str
    commitments: list[Commitment]


def propose_commitments(
    state: EpistemicState,
    initial_commitments: list[Commitment],
    last_scores: RoundScores | None,
) -> CommitmentProposal:
    rendered_initial = "\n".join(f"- [{c.id}] {c.text}" for c in initial_commitments)
    scores_block = (
        last_scores.rationales_for_inferencer()
        if last_scores is not None
        else "(no scores yet — this is the first round)"
    )
    user = (
        "Initial commitments C₀:\n"
        f"{rendered_initial}\n\n"
        "Current commitments C:\n"
        f"{state.render_commitments()}\n\n"
        "Current theory T:\n"
        f"{state.render_theory()}\n\n"
        "Verifier rationales from the previous round:\n"
        f"{scores_block}\n\n"
        "Propose a revised commitment set C'."
    )
    return chat(SYSTEM, user, response_model=CommitmentProposal)  # type: ignore[return-value]
