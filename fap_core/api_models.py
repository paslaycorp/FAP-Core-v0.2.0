from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

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
    media_hash: str = Field(..., min_length=8)
    media_type: str = Field(default="image", pattern="^(image|video|audio|document)$")
    device: DeviceInput
    weather_reported: Optional[WeatherReport] = None
    witness_ids: List[str] = Field(default_factory=list)

class VerifyResponse(BaseModel):
    artifact_id: str
    verdict: str
    total_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float
    components: Dict[str, float]
    provenance_hash: str
    audit_trail: List[Dict[str, Any]]
    recommendations: List[str]
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
