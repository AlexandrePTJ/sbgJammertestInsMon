import threading
import time
import logging

from app.monitoring.collectors.ins_rest_api_client import InsRestApiClient
from app.monitoring.collectors.fake import FakeIns
from app.storage.cache_manager import get_or_create_cache
from typing import List

from app.models.config import INSConfig

logger = logging.getLogger(__name__)

class MonitoringScheduler:
    def __init__(self):
        self._running = False
        self._monitor_thread = None
        self._update_interval_ns: float = 1e9
        self._clients = {}

    def setup(self, ins_configs: List[INSConfig] = None):
        for ins_config in ins_configs:
            if ins_config.connection_type == 'ethernet':
                self._clients[ins_config.id] = InsRestApiClient(ins_config.ip_address)
            elif ins_config.connection_type == 'fake':
                self._clients[ins_config.id] = FakeIns()

    def start(self):
        if self._running:
            return

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop(self):
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)

    def _monitor_loop(self):

        cache = get_or_create_cache()

        while self._running:
            start_time = time.time_ns()
            for ins_id, client in self._clients.items():
                try:
                    data = client.fetch_data()
                    cache.store_data(ins_id, data)
                except Exception as e:
                    logger.error(f"Error on fetching data for {ins_id}: {e}")

            # Adjust to update_interval
            elapsed = time.time_ns() - start_time
            sleep_time = max(0., self._update_interval_ns - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time * 1e-9)
