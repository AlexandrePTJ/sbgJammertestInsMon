from dataclasses import dataclass
from typing import Optional


@dataclass
class INSConfig:
    id: str
    name: str
    color: str
    connection_type: str
    ip_address: Optional[str] = None
    port: int = 80
    serial_port: Optional[str] = None
    serial_baudrate: int = 115200
    timeout: float = 5.0
