"""FAP v0.2.0 Verification Pipeline"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .artifact import Artifact, OracleResults
from .scoring.score import ScoringEngine, ScoreResult
from .oracles.solar_oracle import SolarOracle
from .oracles.oracle import WeatherOracle
from .signature import SignatureVerifier
from .witness import WitnessPool
class VerificationPipeline:
    def __init__(self, solar_oracle=None, weather_oracle=None, signature_verifier=None, witness_pool=None, scoring_engine=None):
        self.solar = solar_oracle or SolarOracle(); self.weather = weather_oracle or WeatherOracle(); self.signature = signature_verifier or SignatureVerifier(); self.witnesses = witness_pool or WitnessPool(); self.scorer = scoring_engine or ScoringEngine()
    def verify(self, artifact):
        artifact.record_event("verification_start")
        sig_score = self._check_signature(artifact); artifact.record_event("signature_check", {"score": sig_score})
        hw_score = self._check_hardware(artifact); artifact.record_event("hardware_check", {"score": hw_score})
        solar_result = self.solar.verify(timestamp=artifact.claimed_timestamp, latitude=artifact.geo.latitude, longitude=artifact.geo.longitude); solar_score = solar_result.get("confidence", 0.0); artifact.record_event("solar_oracle", solar_result)
        weather_result = self.weather.verify(timestamp=artifact.claimed_timestamp, latitude=artifact.geo.latitude, longitude=artifact.geo.longitude, claimed_conditions=artifact.metadata.get("claimed_weather")); weather_score = weather_result.get("confidence", 0.0); artifact.record_event("weather_oracle", weather_result)
        witness_score = self._check_witnesses(artifact); artifact.record_event("witness_check", {"score": witness_score})
        gps_score = self._check_gps(artifact); artifact.record_event("gps_check", {"score": gps_score})
        artifact.set_oracle_results(OracleResults(solar=solar_result, weather=weather_result, timestamp_verified=solar_result.get("timestamp_match", False)))
        result = self.scorer.score(solar_score=solar_score, signature_score=sig_score, hardware_score=hw_score, weather_score=weather_score, witness_score=witness_score, gps_score=gps_score, audit_context={"artifact_id": artifact.artifact_id, "solar_result": solar_result, "weather_result": weather_result})
        artifact.set_score(total=result.total_score, verdict=result.verdict, components=result.component_scores, confidence=result.confidence, audit=result.audit_trail); artifact.finalize(); artifact.record_event("verification_complete")
        return artifact
    def verify_batch(self, artifacts): return [self.verify(a) for a in artifacts]
    async def verify_async(self, artifact):
        artifact.record_event("verification_start_async")
        sig_task = asyncio.create_task(self._check_signature_async(artifact)); hw_task = asyncio.create_task(self._check_hardware_async(artifact)); solar_task = asyncio.create_task(self._solar_async(artifact)); weather_task = asyncio.create_task(self._weather_async(artifact)); witness_task = asyncio.create_task(self._check_witnesses_async(artifact)); gps_task = asyncio.create_task(self._check_gps_async(artifact))
        sig_score = await sig_task; hw_score = await hw_task; solar_result = await solar_task; weather_result = await weather_task; witness_score = await witness_task; gps_score = await gps_task
        solar_score = solar_result.get("confidence", 0.0); weather_score = weather_result.get("confidence", 0.0)
        artifact.set_oracle_results(OracleResults(solar=solar_result, weather=weather_result, timestamp_verified=solar_result.get("timestamp_match", False)))
        result = self.scorer.score(solar_score=solar_score, signature_score=sig_score, hardware_score=hw_score, weather_score=weather_score, witness_score=witness_score, gps_score=gps_score, audit_context={"artifact_id": artifact.artifact_id, "mode": "async"})
        artifact.set_score(total=result.total_score, verdict=result.verdict, components=result.component_scores, confidence=result.confidence, audit=result.audit_trail); artifact.finalize(); artifact.record_event("verification_complete_async")
        return artifact
    def _check_signature(self, artifact):
        try: return self.signature.verify(artifact)
        except Exception as e: artifact.record_event("signature_error", {"error": str(e)}); return 0.0
    def _check_hardware(self, artifact): return 1.0 if artifact.device.is_enrolled() else 0.0
    def _check_witnesses(self, artifact):
        if not artifact.witness_ids: return 0.0
        try: return self.witnesses.consensus_score(artifact)
        except Exception: return 0.0
    def _check_gps(self, artifact):
        claimed = artifact.metadata.get("claimed_location")
        if not claimed: return 0.5
        try:
            lat_diff = abs(artifact.geo.latitude - claimed.get("lat", 0)); lon_diff = abs(artifact.geo.longitude - claimed.get("lon", 0)); max_diff = max(lat_diff, lon_diff)
            if max_diff < 0.001: return 1.0
            elif max_diff < 0.01: return 0.7
            elif max_diff < 0.1: return 0.3
            else: return 0.0
        except Exception: return 0.0
    async def _check_signature_async(self, artifact): return self._check_signature(artifact)
    async def _check_hardware_async(self, artifact): return self._check_hardware(artifact)
    async def _solar_async(self, artifact):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.solar.verify, artifact.claimed_timestamp, artifact.geo.latitude, artifact.geo.longitude)
    async def _weather_async(self, artifact):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.weather.verify, artifact.claimed_timestamp, artifact.geo.latitude, artifact.geo.longitude, artifact.metadata.get("claimed_weather"))
    async def _check_witnesses_async(self, artifact): return self._check_witnesses(artifact)
    async def _check_gps_async(self, artifact): return self._check_gps(artifact)
def verify(artifact): return VerificationPipeline().verify(artifact)
async def verify_async(artifact): return await VerificationPipeline().verify_async(artifact)
