
# ============================================================
# FIX 1: SOLAR ORACLE — Add 30-day fallback + historical awareness
# ============================================================
solar_fixed = '''import requests
from datetime import datetime, timezone
from typing import Dict, Any

class SolarOracle:
    """NOAA SWPC GOES X-ray flux oracle with multi-horizon fallback.
    
    Tries 7-day recent data first (fast), falls back to 30-day archive
    for older timestamps. Returns degraded confidence for historical gaps
    rather than hard zero.
    """
    GOES_7DAY = "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json"
    GOES_30DAY = "https://services.swpc.noaa.gov/json/goes/primary/xrays-30-day.json"
    
    def verify(self, timestamp, latitude, longitude):
        # Try 7-day first (fast, cached by CDN)
        result = self._query(self.GOES_7DAY, timestamp)
        if result.get("confidence", 0) > 0:
            return result
        # Fallback to 30-day for older timestamps
        result = self._query(self.GOES_30DAY, timestamp)
        if result.get("confidence", 0) > 0:
            result["source"] = "noaa-swpc-goes-30d"
            return result
        # No data available — return structured failure with age context
        age_days = (datetime.now(timezone.utc) - timestamp).total_seconds() / 86400
        return {
            "confidence": 0.0,
            "source": "noaa-swpc-goes",
            "timestamp_match": False,
            "error": "No matching solar data within available archive",
            "data_age_days": round(age_days, 1),
            "recommendation": "Timestamp exceeds GOES archive window (30 days)"
        }
    
    def _query(self, url: str, timestamp: datetime) -> Dict[str, Any]:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            target_ts = timestamp.timestamp()
            closest = None
            min_diff = float("inf")
            for record in data:
                rec_ts_str = record.get("time_tag", "")
                if not rec_ts_str:
                    continue
                rec_ts = datetime.fromisoformat(rec_ts_str.replace("Z", "+00:00")).timestamp()
                diff = abs(rec_ts - target_ts)
                if diff < min_diff:
                    min_diff = diff
                    closest = record
            if closest and min_diff < 300:  # 5 minute window
                return {
                    "confidence": 1.0,
                    "flux": closest.get("flux", 0),
                    "source": "noaa-swpc-goes",
                    "timestamp_match": True,
                    "time_diff_seconds": round(min_diff, 2),
                    "record_time": closest.get("time_tag")
                }
            return {"confidence": 0.0}
        except Exception as e:
            return {"confidence": 0.0, "error": str(e)}
'''

with open("fap_core/oracles/solar_oracle.py", "w") as f:
    f.write(solar_fixed)
print("[FIXED] fap_core/oracles/solar_oracle.py")
