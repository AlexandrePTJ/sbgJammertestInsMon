#!/usr/bin/env python3
import logging

from app.utils.config import get_ins_configs
from app import create_app
from app.monitoring import create_monitor

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load app config
ins_configs = get_ins_configs('config.json')

# Create monitor
monitor = create_monitor(ins_configs=ins_configs)

# Create flask app
app = create_app(ins_configs=ins_configs)

# Start everything
if __name__ == '__main__':
    try:
        monitor.start()
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        monitor.stop()
