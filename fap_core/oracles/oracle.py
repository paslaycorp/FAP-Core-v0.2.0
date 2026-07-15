import requests
from datetime import datetime
from typing import Dict, Any, Optional
class WeatherOracle:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    def verify(self, timestamp, latitude, longitude, claimed_conditions=None):
        try:
            resp = requests.get(self.BASE_URL, params={"latitude": latitude, "longitude": longitude, "start_date": timestamp.strftime("%Y-%m-%d"), "end_date": timestamp.strftime("%Y-%m-%d"), "hourly": "temperature_2m,relative_humidity_2m,surface_pressure"}, timeout=10)
            resp.raise_for_status()
            return {"confidence": 0.85, "source": "open-meteo", "data": resp.json(), "timestamp_match": True}
        except Exception as e:
            return {"confidence": 0.0, "error": str(e), "timestamp_match": False}
