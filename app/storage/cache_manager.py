import threading

from app.storage.memory_store import HybridMemoryStore


class CacheManager:
    _instance = None
    _lock = threading.RLock()
    _store: HybridMemoryStore = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def get_or_create_cache(self) -> HybridMemoryStore:
        with self._lock:
            if self._store is None:
                self._store = HybridMemoryStore()
            return self._store


def get_or_create_cache() -> HybridMemoryStore:
    manager = CacheManager()
    return manager.get_or_create_cache()
