"""FAP v0.2.0 Artifact Container"""
import hashlib, json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
class ArtifactStatus(Enum):
    CAPTURED = "captured"; ENROLLED = "enrolled"; ORACLED = "oracled"
    SCORED = "scored"; VERIFIED = "verified"; SUSPICIOUS = "suspicious"; QUARANTINED = "quarantined"; REJECTED = "rejected"
@dataclass
class GeoStamp:
    latitude: float; longitude: float; altitude: Optional[float] = None; accuracy: Optional[float] = None; source: str = "gps"
    def to_dict(self): return asdict(self)
    def hash(self):
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True, default=str).encode()).hexdigest()[:32]
@dataclass
class DeviceStamp:
    model: str; manufacturer: str; os_version: str; camera_model: Optional[str] = None; lens_info: Optional[str] = None; sensor_id: Optional[str] = None; enrollment_id: Optional[str] = None
    def to_dict(self): return asdict(self)
    def is_enrolled(self): return self.enrollment_id is not None
@dataclass
class OracleResults:
    solar: Dict[str, Any] = field(default_factory=dict); weather: Dict[str, Any] = field(default_factory=dict); timestamp_verified: bool = False
    def to_dict(self): return asdict(self)
@dataclass
class Artifact:
    artifact_id: str; created_at: datetime; media_path: str; media_hash: str; media_type: str; geo: GeoStamp; device: DeviceStamp; claimed_timestamp: datetime; metadata: Dict[str, Any] = field(default_factory=dict); exif_raw: Dict[str, Any] = field(default_factory=dict); tags: List[str] = field(default_factory=list); oracle_results: OracleResults = field(default_factory=OracleResults); component_scores: Dict[str, float] = field(default_factory=dict); final_score: Optional[float] = None; verdict: Optional[str] = None; confidence: Optional[float] = None; status: ArtifactStatus = ArtifactStatus.CAPTURED; audit_trail: List[Dict[str, Any]] = field(default_factory=list); parent_id: Optional[str] = None; witness_ids: List[str] = field(default_factory=list)
    def __post_init__(self):
        if isinstance(self.created_at, str): self.created_at = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        if isinstance(self.claimed_timestamp, str): self.claimed_timestamp = datetime.fromisoformat(self.claimed_timestamp.replace("Z", "+00:00"))
    def record_event(self, event, details=None):
        self.audit_trail.append({"event": event, "timestamp": datetime.now(timezone.utc).isoformat(), "details": details or {}})
    def set_oracle_results(self, results):
        self.oracle_results = results; self.status = ArtifactStatus.ORACLED; self.record_event("oracle_complete", results.to_dict())
    def set_score(self, total, verdict, components, confidence, audit):
        self.final_score = total; self.verdict = verdict; self.component_scores = components; self.confidence = confidence; self.status = ArtifactStatus.SCORED; self.record_event("scored", {"total": total, "verdict": verdict, "confidence": confidence})
    def finalize(self):
        if self.verdict == "QUARANTINE": self.status = ArtifactStatus.QUARANTINED
        elif self.verdict in ("STRICT", "PROBABLE"): self.status = ArtifactStatus.VERIFIED
        else: self.status = ArtifactStatus.SUSPICIOUS
        self.record_event("finalized", {"status": self.status.value})
    def provenance_hash(self):
        core = {"artifact_id": self.artifact_id, "media_hash": self.media_hash, "geo_hash": self.geo.hash(), "device": self.device.to_dict(), "claimed_timestamp": self.claimed_timestamp.isoformat(), "created_at": self.created_at.isoformat()}
        return hashlib.sha256(json.dumps(core, sort_keys=True, default=str).encode()).hexdigest()
    def to_dict(self):
        return {"artifact_id": self.artifact_id, "status": self.status.value, "created_at": self.created_at.isoformat(), "media": {"path": self.media_path, "hash": self.media_hash, "type": self.media_type}, "geo": self.geo.to_dict(), "device": self.device.to_dict(), "claimed_timestamp": self.claimed_timestamp.isoformat(), "metadata": self.metadata, "exif": self.exif_raw, "tags": self.tags, "oracle_results": self.oracle_results.to_dict(), "scores": {"components": self.component_scores, "total": self.final_score, "verdict": self.verdict, "confidence": self.confidence}, "provenance_hash": self.provenance_hash(), "audit_trail": self.audit_trail, "parent_id": self.parent_id, "witness_ids": self.witness_ids}
    def to_json(self, indent=None): return json.dumps(self.to_dict(), indent=indent, default=str)
    @classmethod
    def from_capture(cls, media_path, media_hash, media_type, latitude, longitude, device_model, device_manufacturer, os_version, claimed_timestamp=None, altitude=None, camera_model=None, enrollment_id=None, metadata=None, exif=None, tags=None):
        now = datetime.now(timezone.utc)
        artifact_id = hashlib.sha256(f"{media_hash}:{now.isoformat()}:{latitude}:{longitude}".encode()).hexdigest()[:24]
        geo = GeoStamp(latitude=latitude, longitude=longitude, altitude=altitude)
        device = DeviceStamp(model=device_model, manufacturer=device_manufacturer, os_version=os_version, camera_model=camera_model, enrollment_id=enrollment_id)
        artifact = cls(artifact_id=artifact_id, created_at=now, media_path=media_path, media_hash=media_hash, media_type=media_type, geo=geo, device=device, claimed_timestamp=claimed_timestamp or now, metadata=metadata or {}, exif_raw=exif or {}, tags=tags or [])
        artifact.record_event("captured")
        if enrollment_id: artifact.status = ArtifactStatus.ENROLLED; artifact.record_event("enrolled", {"enrollment_id": enrollment_id})
        return artifact
    @classmethod
    def from_dict(cls, data):
        return cls(artifact_id=data["artifact_id"], created_at=data["created_at"], media_path=data["media_path"], media_hash=data["media_hash"], media_type=data["media_type"], geo=GeoStamp(**data["geo"]), device=DeviceStamp(**data["device"]), claimed_timestamp=data["claimed_timestamp"], metadata=data.get("metadata", {}), exif_raw=data.get("exif_raw", {}), tags=data.get("tags", []), oracle_results=OracleResults(**data.get("oracle_results", {})), component_scores=data.get("component_scores", {}), final_score=data.get("final_score"), verdict=data.get("verdict"), confidence=data.get("confidence"), status=ArtifactStatus(data.get("status", "captured")), audit_trail=data.get("audit_trail", []), parent_id=data.get("parent_id"), witness_ids=data.get("witness_ids", []))
