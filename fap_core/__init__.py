"""FAP-Core v0.2.0"""
__version__ = "0.2.0"
__author__ = "Patrick Paslayat"
from .artifact import Artifact, GeoStamp, DeviceStamp, OracleResults, ArtifactStatus
from .scoring.score import ScoringEngine, ScoreResult, quick_score
from .verify import VerificationPipeline, verify, verify_async
__all__ = ["Artifact","GeoStamp","DeviceStamp","OracleResults","ArtifactStatus","ScoringEngine","ScoreResult","quick_score","VerificationPipeline","verify","verify_async"]
