import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any


class MemoryCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()

        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_thread.start()

    def set(self, key: str, value: Any, ttl: int = 300):
        with self._lock:
            self._cache[key] = {
                'value': value,
                'ttl': ttl,
                'created_at': time.time()
            }
            self._timestamps[key] = time.time() + ttl

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None

            item = self._cache[key]
            if time.time() > item['created_at'] + item['ttl']:
                del self._cache[key]
                del self._timestamps[key]
                return None

            return item['value']

    def delete(self, key: str):
        with self._lock:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

    def keys(self) -> List[str]:
        with self._lock:
            current_time = time.time()
            valid_keys = []
            for key, expire_time in self._timestamps.items():
                if current_time <= expire_time:
                    valid_keys.append(key)
            return valid_keys

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def _cleanup_expired(self):
        while True:
            try:
                time.sleep(60)
                current_time = time.time()

                with self._lock:
                    expired_keys = [
                        key for key, expire_time in self._timestamps.items()
                        if current_time > expire_time
                    ]

                    for key in expired_keys:
                        self._cache.pop(key, None)
                        self._timestamps.pop(key, None)

            except Exception:
                pass


class TimeSeriesMemoryStore:
    def __init__(self, max_history_hours: int = 24):
        self._data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._latest: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._max_history_hours = max_history_hours

        self._cleanup_thread = threading.Thread(target=self._cleanup_old_data, daemon=True)
        self._cleanup_thread.start()

    def store_metrics(self, metric_type: str, data: Dict[str, Any]):
        timestamp = datetime.utcnow()

        entry = {
            'timestamp': timestamp,
            'data': data
        }

        with self._lock:
            self._data[metric_type].append(entry)
            self._latest[metric_type] = entry

    def get_latest(self, metric_type: str) -> Optional[Dict]:
        with self._lock:
            return self._latest.get(metric_type)

    def get_metrics_range(self, metric_type: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        with self._lock:
            if metric_type not in self._data:
                return []

            results = []
            for entry in self._data[metric_type]:
                if start_time <= entry['timestamp'] <= end_time:
                    results.append(entry)

            return sorted(results, key=lambda x: x['timestamp'])

    def get_recent_metrics(self, metric_type: str, minutes: int = 30) -> List[Dict]:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        return self.get_metrics_range(metric_type, start_time, end_time)

    def get_all_recent(self, minutes: int = 30) -> Dict[str, List]:
        return {k: self.get_recent_metrics(k, minutes) for k in self._data.keys()}

    def get_all_latest(self) -> Dict[str, Dict]:
        with self._lock:
            return self._latest.copy()

    def _cleanup_old_data(self):
        while True:
            try:
                time.sleep(300)
                cutoff_time = datetime.utcnow() - timedelta(hours=self._max_history_hours)

                with self._lock:
                    for metric_type in self._data:
                        while (self._data[metric_type] and
                               self._data[metric_type][0]['timestamp'] < cutoff_time):
                            self._data[metric_type].popleft()

            except Exception:
                pass


class HybridMemoryStore:
    def __init__(self):
        self._cache = MemoryCache()
        self._timeseries = TimeSeriesMemoryStore()

    def store_data(self, ins_id: str, data: Dict[str, Any]):
        self._cache.set(f"data:{ins_id}:latest", data, ttl=300)
        self._timeseries.store_metrics(ins_id, data)

    def get_latest(self, ins_id: str) -> Optional[Dict]:
        return self._cache.get(f"data:{ins_id}:latest")

    def get_all_latest(self) -> Dict[str, Dict]:
        return self._timeseries.get_all_latest()
    
    def get_positions(self, last_minutes: int = 5) -> Dict[str, List]:
        all_latest = self._timeseries.get_all_recent(minutes=last_minutes)
        positions = {}
        for k, d in all_latest.items():
            positions[k] = []
            for v in d:
                if v.get('data').get('online'):
                    ekf = v.get('data').get('ins_measurement').get('ekf')
                    positions[k].append([ekf.get('latitude'), ekf.get('longitude')])
        return positions
