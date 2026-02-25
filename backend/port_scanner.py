"""
Cross-platform Serial Port Scanner
"""

import asyncio
import logging
import platform
import serial.tools.list_ports
from typing import List, Dict, Optional

# Import platform-specific modules
try:
    import wmi
except ImportError:
    wmi = None

try:
    import psutil
except ImportError:
    psutil = None

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


def _get_windows_port_info(port_info) -> str:
    """
    Get detailed port information on Windows using WMI
    """
    if not wmi:
        return port_info.description
    
    try:
        c = wmi.WMI()
        # Try to get device description from WMI
        for port in c.Win32_SerialPort():
            if port.DeviceID == port_info.device or port.Name.startswith(port_info.name):
                return f"{port.Name} ({port.Description})"
    except Exception as e:
        logger.debug(f"WMI query failed: {e}")
    
    return port_info.description


def _get_linux_port_info(port_info) -> str:
    """
    Get detailed port information on Linux using udev
    """
    try:
        import subprocess
        if hasattr(port_info, 'device') and port_info.device:
            # Try to get udev info
            result = subprocess.run([
                'udevadm', 'info', '--name', port_info.device, '--query', 'property'
            ], capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0:
                # Extract model and vendor info
                lines = result.stdout.split('\n')
                model = ""
                vendor = ""
                for line in lines:
                    if line.startswith('ID_MODEL='):
                        model = line.split('=', 1)[1].strip('"')
                    elif line.startswith('ID_VENDOR='):
                        vendor = line.split('=', 1)[1].strip('"')
                
                if model and vendor:
                    return f"{vendor} {model}"
    except Exception as e:
        logger.debug(f"udevadm query failed: {e}")
    
    return port_info.description


def _get_macos_port_info(port_info) -> str:
    """
    Get detailed port information on macOS using ioreg
    """
    try:
        import subprocess
        if hasattr(port_info, 'device') and port_info.device:
            # Try to get ioreg info
            result = subprocess.run([
                'ioreg', '-rnw0', '-l', '|', 'grep', '-i', 'usb', '|', 'head', '-n', '5'
            ], shell=True, capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0:
                # Parse ioreg output for USB devices
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'USB' in line.upper() and port_info.device in line:
                        return f"USB Serial Device ({port_info.device})"
    except Exception as e:
        logger.debug(f"ioreg query failed: {e}")
    
    return port_info.description


async def get_available_ports() -> List[PortInfo]:
    """
    Get list of available serial ports with descriptions
    """
    system = platform.system()
    
    try:
        # Get basic port list from pyserial
        ports = list(serial.tools.list_ports.comports())
        
        port_infos = []
        
        for port_info in ports:
            # Get base description
            description = port_info.description
            
            # Add system-specific enhancements
            if system == "Windows" and wmi:
                description = _get_windows_port_info(port_info)
            elif system == "Linux":
                description = _get_linux_port_info(port_info)
            elif system == "Darwin":
                description = _get_macos_port_info(port_info)
            
            # Create PortInfo object
            port_obj = PortInfo(
                port=port_info.device,
                description=description,
                hardware_id=getattr(port_info, 'hwid', None)
            )
            port_infos.append(port_obj)
        
        logger.info(f"Found {len(port_infos)} serial ports")
        return port_infos
        
    except Exception as e:
        logger.error(f"Error scanning ports: {e}")
        # Fallback to basic port list
        fallback_ports = []
        try:
            # Try basic enumeration
            for port in [f"COM{i}" for i in range(1, 256)] if system == "Windows" else []:
                fallback_ports.append(PortInfo(port, f"{port} (fallback)"))
        except:
            pass
        
        return fallback_ports


# Helper function for CLI usage
async def scan_ports_cli():
    """
    CLI-friendly port scanning function
    """
    ports = await get_available_ports()
    
    if not ports:
        print("No serial ports found")
        return
    
    print(f"Available serial ports ({len(ports)}):")
    print("-" * 50)
    
    for i, port in enumerate(ports, 1):
        status = "[已断开]" if "disconnected" in port.description.lower() else ""
        print(f"{i:2d}. {port.port:<12} - {port.description} {status}")


# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test():
        ports = await get_available_ports()
        for port in ports:
            print(f"{port.port}: {port.description}")
    
    asyncio.run(test())
