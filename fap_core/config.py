from dataclasses import dataclass
@dataclass
class ScoringConfig:
    weight_solar=0.30; weight_signature=0.20; weight_hardware=0.15
    weight_weather=0.15; weight_witness=0.10; weight_gps=0.10
    tolerance_solar=0.10; tolerance_signature=0.10; tolerance_hardware=0.20
    tolerance_weather=0.15; tolerance_witness=0.20; tolerance_gps=0.20
    threshold_strict=0.90; threshold_probable=0.70
    threshold_suspicious=0.40; threshold_quarantine=0.0
@dataclass
class Config:
    scoring: ScoringConfig = ScoringConfig()
settings = Config()
