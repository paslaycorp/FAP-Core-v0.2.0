"""FAP v0.2.0 Test Suite"""
import pytest
from fap_core.scoring.score import ScoringEngine, quick_score
from fap_core.artifact import Artifact, OracleResults, ArtifactStatus
class TestScoringEngine:
    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValueError): ScoringEngine(weights={"solar": 0.5, "signature": 0.3})
    def test_perfect_scores_yield_strict(self):
        result = ScoringEngine().score(solar_score=1.0, signature_score=1.0, hardware_score=1.0, weather_score=1.0, witness_score=1.0, gps_score=1.0)
        assert result.verdict == "STRICT" and result.total_score == 1.0
    def test_zero_scores_yield_quarantine(self):
        result = ScoringEngine().score(solar_score=0.0, signature_score=0.0, hardware_score=0.0, weather_score=0.0, witness_score=0.0, gps_score=0.0)
        assert result.verdict == "QUARANTINE"
    def test_grand_slam_legitimate(self):
        result = quick_score(solar_score=1.0, signature_score=0.95, hardware_score=1.0, weather_score=0.93, witness_score=0.85, gps_score=0.90)
        assert result.verdict == "STRICT" and result.total_score >= 0.95
    def test_grand_slam_fraudulent(self):
        result = quick_score(solar_score=0.15, signature_score=0.20, hardware_score=0.0, weather_score=0.40, witness_score=0.10, gps_score=0.30)
        assert result.verdict == "QUARANTINE" and result.total_score <= 0.15
class TestArtifact:
    def test_create_from_capture(self):
        artifact = Artifact.from_capture(media_path="/photos/test.jpg", media_hash="abc123", media_type="image", latitude=29.53, longitude=-98.46, device_model="TestPhone", device_manufacturer="TestCo", os_version="1.0", enrollment_id="A7F2-9912")
        assert artifact.status == ArtifactStatus.ENROLLED and artifact.device.is_enrolled()
    def test_provenance_hash_deterministic(self):
        artifact = Artifact.from_capture(media_path="/photos/test.jpg", media_hash="abc123", media_type="image", latitude=29.53, longitude=-98.46, device_model="TestPhone", device_manufacturer="TestCo", os_version="1.0")
        assert artifact.provenance_hash() == artifact.provenance_hash()
    def test_score_lifecycle(self):
        artifact = Artifact.from_capture(media_path="/photos/test.jpg", media_hash="abc123", media_type="image", latitude=29.53, longitude=-98.46, device_model="TestPhone", device_manufacturer="TestCo", os_version="1.0")
        artifact.set_oracle_results(OracleResults(solar={"confidence": 0.95}, weather={"confidence": 0.90}, timestamp_verified=True))
        assert artifact.status == ArtifactStatus.ORACLED
        artifact.set_score(total=0.92, verdict="STRICT", components={"solar": 0.95}, confidence=0.88, audit={})
        assert artifact.status == ArtifactStatus.SCORED and artifact.final_score == 0.92
        artifact.finalize(); assert artifact.status == ArtifactStatus.VERIFIED
class TestVerdictBoundaries:
    @pytest.mark.parametrize("solar,sig,hw,weather,witness,gps,expected", [(1.0,1.0,1.0,1.0,1.0,1.0,"STRICT"),(1.0,0.95,1.0,0.93,0.85,0.90,"STRICT"),(0.8,0.8,0.8,0.8,0.5,0.8,"PROBABLE"),(0.5,0.5,0.5,0.5,0.3,0.5,"SUSPICIOUS"),(0.15,0.20,0.0,0.40,0.10,0.30,"QUARANTINE"),(0.0,0.0,0.0,0.0,0.0,0.0,"QUARANTINE")])
    def test_verdict_matrix(self, solar, sig, hw, weather, witness, gps, expected):
        result = quick_score(solar_score=solar, signature_score=sig, hardware_score=hw, weather_score=weather, witness_score=witness, gps_score=gps)
        assert result.verdict == expected
if __name__ == "__main__": pytest.main([__file__, "-v"])
