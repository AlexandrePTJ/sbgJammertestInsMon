import json

from app.models.config import INSConfig
from typing import List


def get_ins_configs(json_path: str) -> List[INSConfig]:
    ins_configs = []
    with open(json_path, 'r') as f:
        configs_json_data = json.load(f)
        for config_json_data in configs_json_data:
            if config_json_data["connection_type"] == 'ethernet':
                ins_configs.append(INSConfig(
                    id=config_json_data["id"],
                    name=config_json_data["name"],
                    connection_type=config_json_data["connection_type"],
                    ip_address=config_json_data["ip_address"]
                ))
            elif config_json_data["connection_type"] == 'fake':
                ins_configs.append(INSConfig(
                    id=config_json_data["id"],
                    name=config_json_data["name"],
                    connection_type=config_json_data["connection_type"]
                ))
    return ins_configs
