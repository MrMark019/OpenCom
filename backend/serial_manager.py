"""
Serial Port Manager - Handles serial port connection and communication
"""

import asyncio
import logging
import serial.tools.list_ports
from typing import Optional, Union, Callable

# Import pyserial
try:
    import serial
    from serial.tools.list_ports_common import ListPortInfo
except ImportError:
    serial = None
    ListPortInfo = None

logger = logging.getLogger(__name__)


class SerialManager:
    def __init__(self):
        self._serial_port: Optional[serial.Serial] = None
        self._is_connected: bool = False
        self._read_task: Optional[asyncio.Task] = None
        self._config: Optional[dict] = None
        self._data_callback: Optional[Callable[[bytes, str], None]] = None
        
        # Counters
        self.send_count: int = 0
        self.receive_count: int = 0

    def set_data_callback(self, callback: Callable[[bytes, str], None]):
        """
        Set callback function for received data
        callback(data: bytes, data_type: str)
        """
        self._data_callback = callback

    async def initialize(self):
        """
        Initialize the serial manager
        """
        logger.info("SerialManager initialized")

    async def cleanup(self):
        """
        Cleanup resources
        """
        await self.disconnect()
        logger.info("SerialManager cleaned up")

    async def connect(self, config: dict):
        """
        Connect to a serial port with given configuration
        """
        if self._is_connected:
            await self.disconnect()
        
        try:
            # Convert parity string to pyserial format
            parity_map = {
                "N": serial.PARITY_NONE,
                "O": serial.PARITY_ODD,
                "E": serial.PARITY_EVEN,
                "M": serial.PARITY_MARK,
                "S": serial.PARITY_SPACE,
            }
            
            parity = parity_map.get(config.get("parity", "N"), serial.PARITY_NONE)
            
            # Convert stopbits to float
            stopbits = float(config.get("stopbits", 1.0))
            if stopbits == 1:
                stopbits = serial.STOPBITS_ONE
            elif stopbits == 1.5:
                stopbits = serial.STOPBITS_ONE_POINT_FIVE
            elif stopbits == 2:
                stopbits = serial.STOPBITS_TWO
            else:
                stopbits = serial.STOPBITS_ONE
            
            # Convert bytesize
            bytesize_map = {
                5: serial.FIVEBITS,
                6: serial.SIXBITS,
                7: serial.SEVENBITS,
                8: serial.EIGHTBITS,
            }
            bytesize = bytesize_map.get(config.get("bytesize", 8), serial.EIGHTBITS)
            
            # Create serial connection
            self._serial_port = serial.Serial(
                port=config["port"],
                baudrate=config["baudrate"],
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=0.1,  # Non-blocking read
                write_timeout=1.0,
            )
            
            # Set DTR/RTS if specified
            if "dtr" in config:
                self._serial_port.dtr = config["dtr"]
            if "rts" in config:
                self._serial_port.rts = config["rts"]
            
            self._is_connected = True
            self._config = config
            
            # Start reading task
            self._read_task = asyncio.create_task(self._read_loop())
            
            logger.info(f"Connected to {config['port']} at {config['baudrate']} baud")
            
        except Exception as e:
            logger.error(f"Failed to connect to {config['port']}: {e}")
            raise e

    async def disconnect(self):
        """
        Disconnect from the serial port
        """
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self._serial_port and self._serial_port.is_open:
            try:
                self._serial_port.close()
                logger.info("Serial port closed")
            except Exception as e:
                logger.error(f"Error closing serial port: {e}")
        
        self._serial_port = None
        self._is_connected = False
        self._config = None
        logger.info("Disconnected from serial port")

    def is_connected(self) -> bool:
        """
        Check if serial port is connected
        """
        return self._is_connected and self._serial_port is not None and self._serial_port.is_open

    async def send(self, data: str, is_hex: bool = False):
        """
        Send data to serial port
        """
        if not self.is_connected():
            raise Exception("Not connected to serial port")
        
        try:
            if is_hex:
                # Parse hex string (remove spaces, convert to bytes)
                hex_data = data.replace(" ", "").replace("0x", "").replace(",", "")
                if len(hex_data) % 2 != 0:
                    raise ValueError("Hex string must have even number of characters")
                
                # Validate hex characters
                try:
                    int(hex_data, 16)
                except ValueError:
                    raise ValueError("Invalid hex string")
                
                byte_data = bytes.fromhex(hex_data)
            else:
                # Convert string to bytes
                byte_data = data.encode('utf-8')
            
            # Send data
            written = self._serial_port.write(byte_data)
            self._serial_port.flush()
            self.send_count += len(byte_data)
            
            # Notify callback about sent data
            if self._data_callback:
                self._data_callback(byte_data, "send")
            
            logger.debug(f"Sent {written} bytes: {byte_data}")
            
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            raise e

    async def send_raw(self, data: bytes):
        """
        Send raw bytes to serial port
        """
        if not self.is_connected():
            raise Exception("Not connected to serial port")
        
        try:
            written = self._serial_port.write(data)
            self._serial_port.flush()
            self.send_count += len(data)
            
            # Notify callback about sent data
            if self._data_callback:
                self._data_callback(data, "send")
            
            logger.debug(f"Sent {written} bytes (raw)")
            
        except Exception as e:
            logger.error(f"Error sending raw data: {e}")
            raise e

    async def _read_loop(self):
        """
        Background task to read from serial port
        """
        logger.info("Serial read loop started")
        
        while self._is_connected and self._serial_port and self._serial_port.is_open:
            try:
                # Read available data
                if self._serial_port.in_waiting > 0:
                    data = self._serial_port.read(self._serial_port.in_waiting)
                    if data:
                        self.receive_count += len(data)
                        logger.debug(f"Received {len(data)} bytes: {data}")
                        
                        # Call data callback if set
                        if self._data_callback:
                            self._data_callback(data, "receive")
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                logger.info("Read loop cancelled")
                break
            except Exception as e:
                if "port is closed" in str(e).lower():
                    logger.warning("Serial port closed during read")
                    break
                logger.error(f"Error in read loop: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Serial read loop ended")

    async def get_status(self):
        """
        Get current serial port status
        """
        if not self.is_connected():
            return {
                "connected": False,
                "send_count": self.send_count,
                "receive_count": self.receive_count
            }
        
        return {
            "connected": True,
            "port": self._config["port"] if self._config else None,
            "baudrate": self._config["baudrate"] if self._config else None,
            "bytesize": self._config.get("bytesize", 8) if self._config else None,
            "parity": self._config.get("parity", "N") if self._config else None,
            "stopbits": self._config.get("stopbits", 1.0) if self._config else None,
            "dtr": self._config.get("dtr", False) if self._config else None,
            "rts": self._config.get("rts", False) if self._config else None,
            "send_count": self.send_count,
            "receive_count": self.receive_count
        }

    def reset_counters(self):
        """
        Reset send/receive counters
        """
        self.send_count = 0
        self.receive_count = 0
        logger.info("Counters reset")

    async def update_config(self, **kwargs):
        """
        Update serial port configuration without reconnecting
        """
        if not self._config:
            raise Exception("Not connected")
        
        # Update config
        self._config.update(kwargs)
        
        # Apply changes to serial port
        if "baudrate" in kwargs and self._serial_port:
            self._serial_port.baudrate = kwargs["baudrate"]
        if "dtr" in kwargs and self._serial_port:
            self._serial_port.dtr = kwargs["dtr"]
        if "rts" in kwargs and self._serial_port:
            self._serial_port.rts = kwargs["rts"]
        
        logger.info(f"Updated config: {kwargs}")
