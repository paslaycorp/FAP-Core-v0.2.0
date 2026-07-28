# FAP-Insurance

**Real-time photo provenance verification for insurance claims.**

Powered by [FAP-Core](https://github.com/paslaycorp/FAP-Core-v0.2.0) — the fraud-resistant provenance engine that uses live NOAA solar data to verify photo timestamps.

---

## What This Does

Every claim photo tells a story. FAP-Insurance checks if that story is true.

Upload a photo (or its metadata) and get a **provenance score** in under 3 seconds:

| Score | Verdict | What It Means |
|-------|---------|---------------|
| ≥ 0.90 | **VERIFIED** | Photo passes all checks. Proceed with claim. |
| 0.70 – 0.89 | **LIKELY VALID** | Minor anomalies. Standard review. |
| 0.40 – 0.69 | **FLAGGED** | Multiple issues. Enhanced review required. |
| < 0.40 | **FRAUD RISK** | Escalate to SIU. Recommend denial. |

---

## How It Works

FAP-Core checks six independent signals:

1. **Solar Anchor (30%)** — Matches claimed timestamp against NOAA GOES X-ray flux. The sun doesn't lie.
2. **Media Signature (20%)** — Cryptographic hash of the media file.
3. **Device Enrollment (15%)** — Is this a known, enrolled device?
4. **Weather Oracle (15%)** — Does Open-Meteo confirm the claimed weather conditions?
5. **Witness Consensus (10%)** — Do other enrolled devices corroborate?
6. **GPS Plausibility (10%)** — Does claimed location match EXIF or device GPS?

**No single point of failure.** A fraudster would need to:
- Predict chaotic solar X-ray emissions
- Steal an enrolled device
- Fabricate matching weather data
- Recruit colluding witnesses
- Spoof GPS without detection

That's not fraud. That's a heist movie.

---

## Quick Start

### 1. Verify a Single Claim

```bash
curl -X POST https://fap-core.onrender.com/verify \
  -H "Content-Type: application/json" \
  -d '{
    "media_hash": "sha256_of_your_photo",
    "geo": {"lat": 29.53, "lon": -98.46},
    "timestamp_claimed": "2026-07-28T18:00:00+00:00",
    "device": {
      "model": "iPhone15,2",
      "manufacturer": "Apple",
      "os_version": "iOS 17.1",
      "enrollment_id": "your_device_id"
    },
    "witness_ids": ["witness_1", "witness_2"]
  }'
```

### 2. Run the Demo

```bash
curl https://fap-core.onrender.com/demo
```

Returns the canonical grand slam:
- **Legitimate:** 0.9175 / VERIFIED
- **Fraudulent:** 0.3675 / QUARANTINE

### 3. Get a Report

Every verification returns a `verification_id`. Use it to generate an adjuster report:

```bash
curl https://your-fap-insurance-instance/report/{verification_id}
```

---

## Pricing

| Tier | Volume | Price | Best For |
|------|--------|-------|----------|
| **Pilot** | 1,000/mo | **FREE** | Testing the water |
| **Starter** | 5,000/mo | $0.10/verification ($500 cap) | Independent adjusters |
| **Carrier** | 50,000/mo | $0.08/verification ($4,000 cap) | Regional carriers |
| **Enterprise** | Unlimited | Custom | National carriers |

**ROI Math:** One caught fraud case at $15,000 pays for 187,500 verifications at carrier pricing.

---

## Integration Guide

### For Claims Management Systems

Add a "Verify Photo" button that calls `/verify` when an adjuster uploads a claim photo. Store the `verification_id` and `score` in your claim record.

### For Mobile Apps

Use the device's EXIF data to auto-populate `lat`, `lon`, `timestamp_claimed`, `device_model`, and `device_manufacturer`. The adjuster only adds `claim_id` and hits submit.

### For SIU Teams

Every verification generates a court-ready audit trail with NOAA record IDs. The report includes:
- Exact GOES X-ray flux value at claimed time
- Open-Meteo weather data for claimed location
- Device enrollment status
- Witness consensus breakdown
- Cryptographic provenance hash

---

## API Reference

### POST /verify

Verify a single claim photo.

**Request:**
```json
{
  "claim_id": "CLM-2026-001234",
  "media_hash": "abc123...",
  "lat": 29.53,
  "lon": -98.46,
  "timestamp_claimed": "2026-07-28T18:00:00+00:00",
  "device_model": "iPhone15,2",
  "device_manufacturer": "Apple",
  "device_os": "iOS 17.1",
  "enrollment_id": "optional_enrolled_device",
  "witness_ids": ["w1", "w2"],
  "policy_number": "POL-987654",
  "adjuster_notes": "Claimant says photo taken during hailstorm"
}
```

**Response:**
```json
{
  "claim_id": "CLM-2026-001234",
  "verification_id": "18b87268aea8a82150e77499",
  "verdict": "STRICT",
  "verdict_label": "VERIFIED — Proceed with claim",
  "score": 0.9175,
  "confidence": 0.0131,
  "components": {
    "solar": 1.0,
    "signature": 0.95,
    "hardware": 1.0,
    "weather": 0.85,
    "witness": 1.0,
    "gps": 0.5
  },
  "solar_flux_at_time": 1.253e-08,
  "weather_match": 0.85,
  "device_enrolled": true,
  "witness_count": 2,
  "processing_time_ms": 1247,
  "recommendation": "Photo provenance verified. Proceed with standard claim processing.",
  "timestamp_processed": "2026-07-28T18:25:32.963976+00:00"
}
```

### POST /verify/batch

Verify up to 10 claims at once.

### GET /pricing

Show all pricing tiers.

### GET /demo

Return canonical demo scores without live API call.

### GET /health

Check FAP-Core connectivity.

---

## Deployment

```bash
git clone https://github.com/paslaycorp/FAP-Core-v0.2.0.git
cd FAP-Core-v0.2.0/fap-insurance
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8001
```

Or deploy to Render/Railway/Fly.io with the included Dockerfile.

---

## Support

- **Email:** paslayco@gmail.com
- **GitHub:** github.com/paslaycorp/FAP-Core-v0.2.0
- **Demo:** [YouTube link coming]

---

## License

MIT — See FAP-Core v0.2.0 LICENSE

---

*Built by Patrick Paslay. Solar-verified provenance for the insurance industry.*
