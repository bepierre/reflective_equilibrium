from __future__ import annotations

from pydantic import BaseModel

from re_machine.llm import chat
from re_machine.schemas import Case, Commitment

SYSTEM = """You are the CommitmentFormer in a Reflective Equilibrium (RE) machine.

You are given a set of moral cases (raw scenarios — no judgments baked in). Your job is
to form the agent's INITIAL moral commitments C₀ on reading these cases. These are the
agent's starting intuitions, which the rest of the RE process will treat as the anchor
of faithfulness.

STRICT CONSTRAINTS — read carefully, they matter:

  1. Every commitment must be tied to a SPECIFIC CASE. Reference the case by id
     (e.g., "In Case3, ..."). No commitment may generalize across cases.

  2. Every commitment must be an ACTION VERDICT about that case — a judgment of the
     form "the actor MUST do X", "the actor MAY do X", or "the actor MUST NOT do X".
     Pick the verdict you find most defensible on reading the case alone.

  3. Form AT MOST 1-2 commitments per case. One verdict per case is the default;
     a second is only justified if there are genuinely two distinct verdicts (e.g.,
     "the actor may divert" AND "the actor must not push the bystander off the
     bridge while diverting"). Do NOT pad.

  4. Do NOT form cross-case generalizations, distinctions, or principles. Things like
     "in cases where harm is unavoidable...", "actions that directly cause harm are
     worse than those that allow harm", or "minimize total harm when possible" are
     PRINCIPLES — those are the job of the equilibration loop to discover, not
     yours to pre-bake. If you find yourself reaching for a cross-case rule, suppress it.

  5. Do NOT justify your verdicts with general moral theories. Just state the verdict
     and let the case speak for itself.

For each commitment mint a stable id (IC1, IC2, ...). Set origin = 'initial'. Return
a short rationale (2-4 sentences) that summarizes ONLY which cases produced which
verdicts. Do not theorize."""


class FormedCommitments(BaseModel):
    rationale: str
    commitments: list[Commitment]


def form_commitments(cases: list[Case]) -> FormedCommitments:
    rendered_cases = "\n\n".join(f"[{c.id}] {c.text}" for c in cases)
    user = (
        "Cases:\n\n"
        f"{rendered_cases}\n\n"
        "Form the agent's initial commitments C₀ (per-case verdicts only)."
    )
    return chat(SYSTEM, user, response_model=FormedCommitments)  # type: ignore[return-value]
