import requests
from datetime import datetime
from typing import Dict, Any
class SolarOracle:
    GOES_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json"
    def verify(self, timestamp, latitude, longitude):
        try:
            resp = requests.get(self.GOES_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            target_ts = timestamp.isoformat()
            closest = None
            min_diff = float("inf")
            for record in data:
                rec_ts = record.get("time_tag", "")
                diff = abs(datetime.fromisoformat(rec_ts.replace("Z", "+00:00")).timestamp() - timestamp.timestamp())
                if diff < min_diff:
                    min_diff = diff
                    closest = record
            if closest and min_diff < 300:
                return {"confidence": 1.0, "flux": closest.get("flux", 0), "source": "noaa-swpc-goes", "timestamp_match": True, "time_diff_seconds": min_diff, "record_time": closest.get("time_tag")}
            else:
                return {"confidence": 0.0, "source": "noaa-swpc-goes", "timestamp_match": False, "error": "No matching solar data within 5 minutes"}
        except Exception as e:
            return {"confidence": 0.0, "source": "noaa-swpc-goes", "timestamp_match": False, "error": str(e)}
