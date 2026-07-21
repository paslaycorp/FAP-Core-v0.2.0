from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fap_core import __version__
from fap_core.artifact import Artifact, GeoStamp, DeviceStamp
from fap_core.verify import VerificationPipeline
from fap_core.scoring.score import quick_score
from fap_core.api_models import VerifyRequest, VerifyResponse, HealthResponse, EnrollRequest, EnrollResponse
import os, hashlib
from datetime import datetime, timezone

FAP_ENV = os.getenv("FAP_ENV", "development")
FAP_API_KEY = os.getenv("FAP_API_KEY", "dev-key-CHANGE-IN-PROD")
FAP_RATE_LIMIT = os.getenv("FAP_RATE_LIMIT", "100/minute")
security = HTTPBearer(auto_error=False)
limiter = Limiter(key_func=get_remote_address)

def verify_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return "demo-key"
@app.get("/demo")
async def demo():
    l = quick_score(solar_score=1.0, signature_score=0.95, hardware_score=1.0,
                    weather_score=0.93, witness_score=0.85, gps_score=0.90)
    f = quick_score(solar_score=0.15, signature_score=0.20, hardware_score=0.0,
                    weather_score=0.40, witness_score=0.10, gps_score=0.30)
    e = quick_score(solar_score=0.65, signature_score=0.90, hardware_score=1.0,
                    weather_score=0.78, witness_score=0.35, gps_score=0.85)
    return {"scenarios": [
        {"name": "Legitimate", "score": l.total_score, "verdict": l.verdict},
        {"name": "Fraudulent", "score": f.total_score, "verdict": f.verdict},
        {"name": "Edge", "score": e.total_score, "verdict": e.verdict},
    ]}

app = FastAPI(title="FAP-Core", version=__version__, docs_url="/docs" if FAP_ENV != "production" else None)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rl_handler(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

@app.get("/health")
async def health():
    return HealthResponse(status="healthy", version=__version__, timestamp=datetime.now(timezone.utc))



@app.post("/verify", response_model=VerifyResponse)
@limiter.limit(FAP_RATE_LIMIT)
async def verify(request: Request, req: VerifyRequest, api_key: str = Depends(verify_key)):
    geo = GeoStamp(latitude=req.geo.lat, longitude=req.geo.lon)
    device = DeviceStamp(model=req.device.model, manufacturer=req.device.manufacturer, os_version=req.device.os_version, enrollment_id=req.device.enrollment_id)
    artifact = Artifact(artifact_id=req.artifact_id or hashlib.sha256(f"{req.media_hash}:{req.timestamp_claimed.isoformat()}".encode()).hexdigest()[:24], created_at=datetime.now(timezone.utc), media_path="api", media_hash=req.media_hash, media_type=req.media_type, geo=geo, device=device, claimed_timestamp=req.timestamp_claimed, witness_ids=req.witness_ids)
    pipeline = VerificationPipeline()
    artifact = pipeline.verify(artifact)
    return VerifyResponse(artifact_id=artifact.artifact_id, verdict=artifact.verdict or "UNKNOWN", total_score=artifact.final_score or 0.0, confidence=artifact.confidence or 0.0, components=artifact.component_scores or {}, provenance_hash=artifact.provenance_hash(), audit_trail=artifact.audit_trail, recommendations=[], processed_at=datetime.now(timezone.utc))

@app.post("/enroll", response_model=EnrollResponse)
@limiter.limit("10/minute")
async def enroll(request: Request, req: EnrollRequest, api_key: str = Depends(verify_key)):
    from fap_core.signature import DeviceRegistry
    DeviceRegistry().enroll(req.device_id, {})
    return EnrollResponse(device_id=req.device_id, enrolled=True, timestamp=datetime.now(timezone.utc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=(FAP_ENV=="development"))
