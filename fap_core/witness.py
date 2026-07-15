from typing import List
class WitnessPool:
    def __init__(self): self._witnesses = []
    def add_witness(self, witness_id): self._witnesses.append(witness_id)
    def consensus_score(self, artifact) -> float:
        if not artifact.witness_ids: return 0.0
        return min(1.0, len(artifact.witness_ids) * 0.35)
