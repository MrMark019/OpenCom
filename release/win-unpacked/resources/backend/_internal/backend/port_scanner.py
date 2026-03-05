"""
Cross-platform Serial Port Scanner
"""

import asyncio
import logging
import serial.tools.list_ports
from typing import List, Optional

logger = logging.getLogger(__name__)


class PortInfo:
    def __init__(self, port: str, description: str, hardware_id: Optional[str] = None):
        self.port = port
        self.description = description
        self.hardware_id = hardware_id

    def to_dict(self):
        return {
            "port": self.port,
            "description": self.description,
            "hardware_id": self.hardware_id
        }


async def get_available_ports() -> List[PortInfo]:
    """
    Get list of available serial ports with descriptions
    """
    try:
        ports = list(serial.tools.list_ports.comports())
        port_infos = []

        for port_info in ports:
            port_obj = PortInfo(
                port=port_info.device,
                description=port_info.description,
                hardware_id=getattr(port_info, 'hwid', None)
            )
            port_infos.append(port_obj)

        logger.info(f"Found {len(port_infos)} serial ports")
        return port_infos

    except Exception as e:
        logger.error(f"Error scanning ports: {e}")
        return []


async def scan_ports_cli():
    """CLI-friendly port scanning function"""
    ports = await get_available_ports()
    if not ports:
        print("No serial ports found")
        return
    print(f"Available serial ports ({len(ports)}):")
    print("-" * 50)
    for i, port in enumerate(ports, 1):
        print(f"{i:2d}. {port.port:<12} - {port.description}")


if __name__ == "__main__":
    asyncio.run(scan_ports_cli())
