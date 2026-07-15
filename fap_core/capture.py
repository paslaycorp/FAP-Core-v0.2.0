import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
class MediaCapture:
    def capture(self, file_path: str, metadata=None) -> Dict[str, Any]:
        with open(file_path, "rb") as f:
            data = f.read()
        return {"path": file_path, "hash": hashlib.sha256(data).hexdigest(), "size": len(data), "captured_at": datetime.now(timezone.utc).isoformat(), "metadata": metadata or {}}
