"""Explicit separation of verification, applicability, authority, and consequence safety."""
from enum import Enum
from pydantic import BaseModel

class BoundaryState(str, Enum):
    UNKNOWN = "UNKNOWN"
    VALID = "VALID"
    INVALID = "INVALID"

class EpistemicBoundary(BaseModel):
    integrity: BoundaryState = BoundaryState.UNKNOWN
    identity: BoundaryState = BoundaryState.UNKNOWN
    temporal_validity: BoundaryState = BoundaryState.UNKNOWN
    applicability: BoundaryState = BoundaryState.UNKNOWN
    authority: BoundaryState = BoundaryState.UNKNOWN
    consequence_safety: BoundaryState = BoundaryState.UNKNOWN

    def verification_does_not_authorize(self) -> bool:
        return self.authority != BoundaryState.VALID

    def is_actionable(self) -> bool:
        return all(x == BoundaryState.VALID for x in (
            self.integrity, self.identity, self.temporal_validity,
            self.applicability, self.authority, self.consequence_safety,
        ))
