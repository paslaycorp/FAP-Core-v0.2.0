# FAP-Insurance Integration Guide for Carriers

## Overview

This guide walks your engineering team through integrating FAP-Insurance into your claims management system. Estimated time: **2-4 hours** for a basic integration, **1-2 days** for full production deployment.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Your CMS / App │────▶│  FAP-Insurance   │────▶│   FAP-Core      │
│                 │◄────│  (this package)  │◄────│   (Render)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │
        ▼
┌─────────────────┐
│  Adjuster Report │
│  (HTML/PDF)      │
└─────────────────┘
```

FAP-Insurance is a thin, adjuster-facing wrapper around FAP-Core. It adds:
- Insurance-specific language (VERIFIED, FRAUD RISK, etc.)
- Adjuster report generation
- Batch processing
- Pricing tier management
- SIU webhook integration

---

## Step 1: Deploy FAP-Insurance

### Option A: Self-Hosted (Recommended for Carriers)

```bash
git clone https://github.com/paslaycorp/FAP-Core-v0.2.0.git
cd FAP-Core-v0.2.0/fap-insurance
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn fap_insurance.api:app --host 0.0.0.0 --port 8001
```

### Option B: Render/Railway (Fastest)

1. Fork the repo
2. Connect to Render
3. Set start command: `uvicorn fap_insurance.api:app --host 0.0.0.0 --port $PORT`
4. Deploy

---

## Step 2: Add "Verify Photo" Button to Your CMS

### Frontend (JavaScript/React)

```javascript
async function verifyPhoto(claimId, photoFile) {
  // Extract EXIF data using a library like exif-js
  const exif = await extractExif(photoFile);

  const payload = {
    claim_id: claimId,
    media_hash: await sha256(photoFile),
    lat: exif.GPSLatitude,
    lon: exif.GPSLongitude,
    timestamp_claimed: exif.DateTimeOriginal,
    device_model: exif.Model,
    device_manufacturer: exif.Make,
    device_os: "iOS " + exif.Software, // or Android version
    enrollment_id: null, // set if device pre-enrolled
    witness_ids: [], // populate if witnesses available
    policy_number: currentPolicy.number,
    adjuster_notes: ""
  };

  const response = await fetch('https://your-fap-instance/verify', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });

  const result = await response.json();

  // Display result to adjuster
  showVerificationBadge(result.verdict, result.score);
  storeVerificationId(claimId, result.verification_id);

  return result;
}
```

### Backend (Python/Django/Flask)

```python
import requests

def verify_claim_photo(claim_id, photo_metadata):
    payload = {
        "claim_id": claim_id,
        "media_hash": photo_metadata["hash"],
        "lat": photo_metadata["lat"],
        "lon": photo_metadata["lon"],
        "timestamp_claimed": photo_metadata["timestamp"],
        "device_model": photo_metadata["model"],
        "device_manufacturer": photo_metadata["make"],
        "device_os": photo_metadata["os"],
        "enrollment_id": photo_metadata.get("enrollment_id"),
        "witness_ids": photo_metadata.get("witnesses", []),
        "policy_number": photo_metadata["policy"],
    }

    resp = requests.post(
        "https://your-fap-instance/verify",
        json=payload,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()
```

---

## Step 3: Store Verification Results

Add these fields to your claim database:

```sql
ALTER TABLE claims ADD COLUMN (
    fap_verification_id VARCHAR(24),
    fap_score DECIMAL(5,4),
    fap_verdict VARCHAR(20),
    fap_verified_at TIMESTAMP,
    fap_report_url VARCHAR(500)
);
```

This lets you:
- Filter claims by verification status
- Generate reports for SIU
- Track ROI over time

---

## Step 4: SIU Webhook Integration

When a claim scores below 0.40 (QUARANTINE), automatically notify your SIU team:

```python
@app.post("/verify")
async def verify_claim(req: VerifyClaimRequest):
    result = await verify_claim(req)

    if result.verdict == "QUARANTINE":
        send_siu_alert(
            claim_id=req.claim_id,
            verification_id=result.verification_id,
            score=result.score,
            report_url=result.report_url
        )

    return result
```

**SIU Alert Payload:**
```json
{
  "alert_type": "FAP_QUARANTINE",
  "claim_id": "CLM-2026-001234",
  "verification_id": "18b87268aea8a82150e77499",
  "score": 0.3675,
  "primary_failure": "solar_timestamp_mismatch",
  "report_url": "https://.../report/18b87268...",
  "timestamp": "2026-07-28T18:31:34Z"
}
```

---

## Step 5: Enroll Adjuster Devices

Pre-enroll devices used by your field adjusters for higher hardware scores:

```bash
curl -X POST https://your-fap-instance/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "ADJ_001_PHONE",
    "fingerprint": {"model": "iPhone15,2", "manufacturer": "Apple"}
  }'
```

Photos from enrolled devices get `hardware = 1.0` automatically.

---

## Step 6: Batch Processing for CAT Events

After a hurricane, process hundreds of photos at once:

```bash
curl -X POST https://your-fap-instance/verify/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"claim_id": "CAT-001", "media_hash": "...", "lat": 29.5, "lon": -98.4, ...},
    {"claim_id": "CAT-002", "media_hash": "...", "lat": 29.6, "lon": -98.5, ...},
    ... up to 10
  ]'
```

---

## Security Considerations

1. **API Key:** Set `FAP_API_KEY` environment variable. Pass it in the `Authorization: Bearer` header.
2. **Rate Limiting:** Default is 100/minute. Contact us for carrier-tier limits.
3. **Data Privacy:** We don't store your photos. We only verify metadata (hash, timestamp, GPS). No PII leaves your infrastructure unless you include it in `adjuster_notes`.
4. **HIPAA/SOX:** FAP-Core processes no medical or financial data. For regulated environments, use the on-premise Enterprise tier.

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| 504 Timeout | FAP-Core cold start on Render | Retry once after 30s |
| solar=0.0 | Timestamp > 7 days old | Use recent timestamps or expect solar miss |
| hardware=0.0 | Device not enrolled | Add `enrollment_id` or use `/enroll` |
| weather=0.0 | Coordinates in remote area | Open-Meteo has limited coverage in some regions |
| 429 Rate Limit | Too many requests | Wait 1 minute or upgrade tier |

---

## Support

- **Slack:** [Coming soon]
- **Email:** paslayco@gmail.com
- **GitHub Issues:** github.com/paslaycorp/FAP-Core-v0.2.0/issues

---

*Last updated: 2026-07-28 | FAP-Insurance v0.1.0*
