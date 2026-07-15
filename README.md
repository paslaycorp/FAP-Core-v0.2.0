# FAP-Core v0.2.0

**Fraud-Authenticity Provenance Engine**

Multi-signal environmental verification for media artifacts.

## The Solar Anchor

Solar X-ray flux is chaotic, publicly logged by NOAA, and impossible to fabricate retroactively.

## Scoring Formula

| Signal | Weight | Source |
|--------|--------|--------|
| Solar activity | 0.30 | NOAA SWPC GOES X-ray |
| Device signature | 0.20 | EXIF + sensor fingerprint |
| Hardware enrollment | 0.15 | Device registry |
| Weather conditions | 0.15 | NOAA NWS / Open-Meteo |
| Witness consensus | 0.10 | Multi-party attestation |
| GPS location | 0.10 | Coordinate corroboration |

## Verdicts

- **STRICT** (≥0.90) — Fully verified
- **PROBABLE** (≥0.70) — Likely authentic
- **SUSPICIOUS** (≥0.40) — Mixed signals, review
- **QUARANTINE** (<0.40) — Insufficient evidence

## Quick Start

```python
from fap_core.scoring.score import quick_score
result = quick_score(solar_score=1.0, signature_score=0.95, hardware_score=1.0, weather_score=0.93, witness_score=0.85, gps_score=0.90)
print(f"{result.total_score} → {result.verdict}")  # 1.00 → STRICT
```

## License

PROPRIETARY — All rights reserved.
