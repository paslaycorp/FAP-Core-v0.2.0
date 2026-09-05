from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fap_core import __version__
from fap_core.artifact import Artifact, GeoStamp, DeviceStamp
from fap_core.verify import VerificationPipeline
from fap_core.scoring.score import quick_score
from fap_core.api_models import VerifyRequest, VerifyResponse, HealthResponse, EnrollRequest, EnrollResponse
from fap_core.epm_exchange import build_attestation
import os, hashlib, base64, json
from datetime import datetime, timezone

FAP_ENV = os.getenv("FAP_ENV", "development")
FAP_API_KEY = os.getenv("FAP_API_KEY")
FAP_RATE_LIMIT = os.getenv("FAP_RATE_LIMIT", "100/minute")

# Validate required secrets on startup
if FAP_ENV == "production" and not FAP_API_KEY:
    raise ValueError("CRITICAL: FAP_API_KEY environment variable must be set in production")

security = HTTPBearer(auto_error=False)
limiter = Limiter(key_func=get_remote_address)

# app MUST be defined BEFORE any @app.route decorators
app = FastAPI(title="FAP-Core", version=__version__, docs_url="/docs" if FAP_ENV != "production" else None)
app.state.limiter = limiter

@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>FAP-Core | Fraud-Resistant Evidence Verification</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 60px auto; padding: 20px; background: #0a0a0a; color: #e0e0e0; }
            h1 { color: #4ade80; font-size: 2.5em; margin-bottom: 10px; }
            .tagline { color: #888; font-size: 1.1em; margin-bottom: 30px; }
            .card { background: #1a1a1a; border-radius: 12px; padding: 24px; margin: 16px 0; border: 1px solid #333; }
            .score { font-size: 2em; font-weight: bold; }
            .strict { color: #4ade80; }
            .quarantine { color: #ef4444; }
            a { color: #4ade80; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .btn { display: inline-block; background: #4ade80; color: #0a0a0a; padding: 12px 24px; border-radius: 8px; font-weight: bold; margin: 8px 8px 0 0; }
            .btn-secondary { background: #333; color: #e0e0e0; }
            .version { color: #666; font-size: 0.85em; margin-top: 40px; }
        </style>
    </head>
    <body>
        <h1>FAP-Core</h1>
        <p class="tagline">Fraud-resistant provenance verification for insurance claims.</p>
        <div class="card">
            <p><strong>Live solar anchors.</strong> GOES-16 X-ray flux, impossible to fabricate retroactively.</p>
            <p><strong>Real-time weather corroboration.</strong> NOAA-validated conditions at time of claim.</p>
            <p><strong>Device fingerprinting.</strong> Enrolled hardware, not spoofable GPS.</p>
        </div>
        <div class="card">
            <p><strong>Grand Slam Demo Results</strong></p>
            <p>Legitimate claim: <span class="score strict">0.9545 STRICT</span></p>
            <p>Fraudulent claim: <span class="score quarantine">0.1800 QUARANTINE</span></p>
            <p>Gap: <strong>0.77</strong> — clear enough for automated decisioning.</p>
        </div>
        <a href="/docs" class="btn">API Documentation</a>
        <a href="/demo" class="btn btn-secondary">Run Live Demo</a>
        <p class="version">v0.2.0 | San Antonio, TX | Built by Patrick Paslay</p>
    </body>
    </html>
    """)


@app.exception_handler(RateLimitExceeded)
async def rl_handler(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

def verify_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate incoming API key against the environment secret."""
    if not credentials:
        raise HTTPException(
            status_code=403,
            detail="Missing API key. Provide via Authorization: Bearer <key>"
        )

    # Validate against the injected environment secret in every environment.
    if FAP_API_KEY and credentials.credentials == FAP_API_KEY:
        return credentials.credentials

    raise HTTPException(
        status_code=403,
        detail="Invalid API key"
    )

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

@app.get("/health")
async def health():
    return HealthResponse(status="healthy", version=__version__, timestamp=datetime.now(timezone.utc))


def _decode_epm_exchange(value: str) -> dict:
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid EPM assurance envelope.") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid EPM assurance envelope.")
    return data

@app.post("/verify", response_model=VerifyResponse)
@limiter.limit(FAP_RATE_LIMIT)
async def verify(request: Request, req: VerifyRequest, api_key: str = Depends(verify_key)):
    geo = GeoStamp(latitude=req.geo.lat, longitude=req.geo.lon)
    device = DeviceStamp(model=req.device.model, manufacturer=req.device.manufacturer,
                         os_version=req.device.os_version, enrollment_id=req.device.enrollment_id)
    artifact = Artifact(
        artifact_id=req.artifact_id or hashlib.sha256(
            f"{req.media_hash}:{req.timestamp_claimed.isoformat()}".encode()
        ).hexdigest()[:24],
        created_at=datetime.now(timezone.utc),
        media_path="api",
        media_hash=req.media_hash,
        media_type=req.media_type,
        geo=geo,
        device=device,
        claimed_timestamp=req.timestamp_claimed,
        witness_ids=req.witness_ids
    )
    pipeline = VerificationPipeline()
    artifact = pipeline.verify(artifact)
    result = VerifyResponse(
        artifact_id=artifact.artifact_id,
        verdict=artifact.verdict or "UNKNOWN",
        total_score=artifact.final_score or 0.0,
        confidence=artifact.confidence or 0.0,
        components=artifact.component_scores or {},
        provenance_hash=artifact.provenance_hash(),
        audit_trail=artifact.audit_trail,
        recommendations=[],
        processed_at=datetime.now(timezone.utc)
    )
    epm_header = request.headers.get("X-EPM-Assurance")
    if epm_header:
        exchange = _decode_epm_exchange(epm_header)
        try:
            result.epm_attestation = build_attestation(
                exchange=exchange,
                verification=req.model_dump(mode="python", exclude_none=False),
                result=result.model_dump(mode="python"),
            )
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail="EPM assurance binding failed.") from exc
    return result

@app.post("/enroll", response_model=EnrollResponse)
@limiter.limit("10/minute")
async def enroll(request: Request, req: EnrollRequest, api_key: str = Depends(verify_key)):
    from fap_core.signature import DeviceRegistry
    DeviceRegistry().enroll(req.device_id, {})
    return EnrollResponse(device_id=req.device_id, enrolled=True, timestamp=datetime.now(timezone.utc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=(FAP_ENV == "development"))
