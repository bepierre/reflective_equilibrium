from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, confloat


CommitmentOrigin = Literal["initial", "emerging", "inferred"]


class Case(BaseModel):
    id: str
    text: str  # raw scenario description, no moral judgment baked in


class Commitment(BaseModel):
    id: str
    text: str
    origin: CommitmentOrigin = "initial"


class Principle(BaseModel):
    id: str
    text: str


class EpistemicState(BaseModel):
    commitments: list[Commitment] = Field(default_factory=list)
    theory: list[Principle] = Field(default_factory=list)

    def render_commitments(self) -> str:
        if not self.commitments:
            return "(none)"
        return "\n".join(f"- [{c.id}] ({c.origin}) {c.text}" for c in self.commitments)

    def render_theory(self) -> str:
        if not self.theory:
            return "(empty theory)"
        return "\n".join(f"- [{p.id}] {p.text}" for p in self.theory)


class VerifierScore(BaseModel):
    score: confloat(ge=0.0, le=1.0)  # type: ignore[valid-type]
    rationale: str


class Weights(BaseModel):
    account: confloat(ge=0.0, le=1.0) = 0.5  # type: ignore[valid-type]
    systematicity: confloat(ge=0.0, le=1.0) = 0.25  # type: ignore[valid-type]
    faithfulness: confloat(ge=0.0, le=1.0) = 0.25  # type: ignore[valid-type]


class RoundScores(BaseModel):
    account: VerifierScore
    systematicity: VerifierScore
    faithfulness: VerifierScore

    def z(self, weights: Weights) -> float:
        return (
            weights.account * self.account.score
            + weights.systematicity * self.systematicity.score
            + weights.faithfulness * self.faithfulness.score
        )

    def rationales_for_inferencer(self) -> str:
        return (
            f"Account score = {self.account.score:.2f}\n"
            f"  Rationale: {self.account.rationale}\n"
            f"Systematicity score = {self.systematicity.score:.2f}\n"
            f"  Rationale: {self.systematicity.rationale}\n"
            f"Faithfulness score = {self.faithfulness.score:.2f}\n"
            f"  Rationale: {self.faithfulness.rationale}"
        )


StepKind = Literal["A", "B"]  # A = theory revision, B = commitment revision


class TraceStep(BaseModel):
    step: int
    kind: StepKind
    state_before: EpistemicState
    state_proposed: EpistemicState
    scores_before: RoundScores
    scores_proposed: RoundScores
    z_before: float
    z_proposed: float
    accepted: bool
    proposal_diff: str


class RunResult(BaseModel):
    final_state: EpistemicState
    initial_commitments: list[Commitment]
    weights: Weights
    trace: list[TraceStep]
    converged: bool
    final_z: float
