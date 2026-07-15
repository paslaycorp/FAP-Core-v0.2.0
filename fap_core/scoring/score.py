"""FAP v0.2.0 Scoring Engine"""
import math
from typing import Dict, Any, Optional
from dataclasses import dataclass
from ..config import settings
@dataclass
class ScoreResult:
    total_score: float
    verdict: str
    component_scores: Dict[str, float]
    component_details: Dict[str, Any]
    confidence: float
    audit_trail: Dict[str, Any]
class ScoringEngine:
    def __init__(self, weights=None, tolerances=None, thresholds=None):
        self.weights = weights or {"solar": settings.scoring.weight_solar, "signature": settings.scoring.weight_signature, "hardware": settings.scoring.weight_hardware, "weather": settings.scoring.weight_weather, "witness": settings.scoring.weight_witness, "gps": settings.scoring.weight_gps}
        self.tolerances = tolerances or {"solar": settings.scoring.tolerance_solar, "signature": settings.scoring.tolerance_signature, "hardware": settings.scoring.tolerance_hardware, "weather": settings.scoring.tolerance_weather, "witness": settings.scoring.tolerance_witness, "gps": settings.scoring.tolerance_gps}
        self.thresholds = thresholds or {"strict": settings.scoring.threshold_strict, "probable": settings.scoring.threshold_probable, "suspicious": settings.scoring.threshold_suspicious, "quarantine": settings.scoring.threshold_quarantine}
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    def score(self, solar_score, signature_score, hardware_score, weather_score, witness_score, gps_score, audit_context=None):
        raw = {"solar": self._clamp(solar_score), "signature": self._clamp(signature_score), "hardware": self._clamp(hardware_score), "weather": self._clamp(weather_score), "witness": self._clamp(witness_score), "gps": self._clamp(gps_score)}
        adjusted = self._apply_tolerances(raw)
        total = sum(adjusted[k] * self.weights[k] for k in adjusted)
        total = self._clamp(total)
        verdict = self._verdict(total)
        confidence = self._compute_confidence(adjusted)
        audit = {"engine_version": "2.0", "weights": self.weights, "tolerances": self.tolerances, "thresholds": self.thresholds, "raw_scores": raw, "adjusted_scores": adjusted, "total_score": total, "verdict": verdict, "confidence": confidence, "context": audit_context or {}}
        return ScoreResult(total_score=round(total, 4), verdict=verdict, component_scores={k: round(v, 4) for k, v in adjusted.items()}, component_details=audit_context or {}, confidence=round(confidence, 4), audit_trail=audit)
    def score_from_artifact(self, artifact):
        return self.score(solar_score=artifact.get("solar", 0.0), signature_score=artifact.get("signature", 0.0), hardware_score=artifact.get("hardware", 0.0), weather_score=artifact.get("weather", 0.0), witness_score=artifact.get("witness", 0.0), gps_score=artifact.get("gps", 0.0), audit_context=artifact.get("metadata"))
    def get_scoring_shape(self):
        return {"version": "2.0", "principle": "Multi-signal environmental verification with solar anchor", "signals": [{"name": "solar_activity", "importance": "HIGH", "description": "GOES X-ray flux and solar wind at artifact timestamp", "rationale": "Impossible to fabricate retroactively; publicly logged by NOAA", "weight": self.weights.get("solar"), "tolerance": self.tolerances.get("solar")}, {"name": "device_signature", "importance": "HIGH", "description": "Camera model, lens, sensor fingerprint, EXIF integrity", "rationale": "Links artifact to known enrolled device", "weight": self.weights.get("signature"), "tolerance": self.tolerances.get("signature")}, {"name": "hardware_enrollment", "importance": "MEDIUM", "description": "Whether the device is in the enrolled registry", "rationale": "Unknown devices are higher risk", "weight": self.weights.get("hardware"), "tolerance": self.tolerances.get("hardware")}, {"name": "weather_conditions", "importance": "MEDIUM", "description": "NOAA-verified temperature, pressure, humidity at location/time", "rationale": "Weather is locally predictable but globally chaotic", "weight": self.weights.get("weather"), "tolerance": self.tolerances.get("weather")}, {"name": "witness_consensus", "importance": "LOW", "description": "Multi-party attestation from co-located devices", "rationale": "Social proof; harder to coordinate fraud at scale", "weight": self.weights.get("witness"), "tolerance": self.tolerances.get("witness")}, {"name": "gps_location", "importance": "LOW", "description": "GPS coordinates vs claimed location", "rationale": "Spoofable alone; corroborative only", "weight": self.weights.get("gps"), "tolerance": self.tolerances.get("gps")}], "thresholds": self.thresholds, "verdicts": {"STRICT": ">= strict threshold", "PROBABLE": ">= probable threshold", "SUSPICIOUS": ">= suspicious threshold", "QUARANTINE": "< suspicious threshold"}}
    @staticmethod
    def _clamp(v): return max(0.0, min(1.0, float(v)))
    def _apply_tolerances(self, raw):
        adjusted = {}
        for key, score in raw.items():
            tol = self.tolerances.get(key, 0.0)
            if score < tol:
                adjusted[key] = score * (score / tol)
            else:
                adjusted[key] = score
        return adjusted
    def _verdict(self, total):
        if total >= self.thresholds["strict"]: return "STRICT"
        elif total >= self.thresholds["probable"]: return "PROBABLE"
        elif total >= self.thresholds["suspicious"]: return "SUSPICIOUS"
        else: return "QUARANTINE"
    def _compute_confidence(self, scores):
        values = list(scores.values())
        if not values or sum(values) == 0: return 0.0
        total = sum(values)
        probs = [v / total for v in values]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        max_entropy = math.log2(len(values))
        norm_entropy = entropy / max_entropy if max_entropy > 0 else 0
        return self._clamp(1.0 - norm_entropy)
default_engine = ScoringEngine()
def quick_score(**kwargs): return default_engine.score(**kwargs)
