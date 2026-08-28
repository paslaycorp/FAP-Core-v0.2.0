from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import re
from pydantic import BaseModel, Field, field_validator
from .epistemic_boundary import EpistemicBoundary

class GeoInput(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)

class DeviceInput(BaseModel):
    model: str
    manufacturer: str
    os_version: str
    enrollment_id: Optional[str] = None

class WeatherReport(BaseModel):
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = Field(None, ge=0.0, le=100.0)

class VerifyRequest(BaseModel):
    artifact_id: Optional[str] = None
    timestamp_claimed: datetime
    geo: GeoInput
    media_hash: str = Field(..., min_length=64, max_length=64)
    media_type: str = Field(default="image", pattern="^(image|video|audio|document)$")
    device: DeviceInput
    weather_reported: Optional[WeatherReport] = None
    witness_ids: List[str] = Field(default_factory=list)

    @field_validator("media_hash")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", value):
            raise ValueError("media_hash must be a 64-character hexadecimal SHA-256 digest")
        return value.lower()

    @field_validator("timestamp_claimed")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp_claimed must include an explicit timezone")
        normalized = value.astimezone(timezone.utc)
        if normalized > datetime.now(timezone.utc):
            raise ValueError("timestamp_claimed cannot be in the future")
        return normalized

class VerifyResponse(BaseModel):
    artifact_id: str
    verdict: str
    total_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    components: Dict[str, float]
    provenance_hash: str
    audit_trail: List[Dict[str, Any]]
    recommendations: List[str]
    epistemic_boundary: EpistemicBoundary
    actionable: bool = False
    processed_at: datetime

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime

class EnrollRequest(BaseModel):
    device_id: str = Field(..., min_length=4, max_length=128)

class EnrollResponse(BaseModel):
    device_id: str
    enrolled: bool
    timestamp: datetime
