from typing import List

from app.models.config import INSConfig
from app.monitoring.scheduler.monitoring_scheduler import MonitoringScheduler


def create_monitor(ins_configs: List[INSConfig] = None):
    monitoring_scheduler = MonitoringScheduler()
    monitoring_scheduler.setup(ins_configs)
    return monitoring_scheduler
