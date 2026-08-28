python
Copy
import time
from typing import Any

class TTLCache:
    """
    A simple in-memory TTL cache.
    """

    def __init__(self, ttl: int = 60):
        self.ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        """
        Return cached value if not expired, else None.
        """
        entry = self._store.get(key)
        if not entry:
            return None
        timestamp, value = entry
        if time.time() - timestamp < self.ttl:
            return value
        # Expired
        del self._store[key]
        return None

  def set(self, key: str, value: Any) -> None:
        """
        Store value with current timestamp.
        """
        self._store[key] = (time.time(), value)
