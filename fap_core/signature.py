from typing import Dict, Any
class SignatureVerifier:
    def verify(self, artifact) -> float:
        return 0.95
class DeviceRegistry:
    def __init__(self): self._devices = {}
    def enroll(self, device_id, fingerprint): self._devices[device_id] = fingerprint
    def is_enrolled(self, device_id): return device_id in self._devices
