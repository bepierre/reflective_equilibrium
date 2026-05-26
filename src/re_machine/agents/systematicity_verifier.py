from __future__ import annotations

from re_machine.llm import chat
from re_machine.schemas import EpistemicState, VerifierScore

SYSTEM = """You score Systematicity: how compact and unifying theory T is.

Higher score (closer to 1.0) when T:
  - has fewer principles,
  - states principles at a general, unifying level (not case-by-case stipulations),
  - has broad implications across the cases under consideration,
  - is internally consistent.

Lower score (closer to 0.0) when T is empty, fragmented, or contradicts itself.

Output a single score in [0, 1] and a 2-3 sentence rationale that names principles by id."""


def score_systematicity(state: EpistemicState) -> VerifierScore:
    user = (
        "Theory T:\n"
        f"{state.render_theory()}\n\n"
        "Score Systematicity(T)."
    )
    return chat(SYSTEM, user, response_model=VerifierScore)  # type: ignore[return-value]
