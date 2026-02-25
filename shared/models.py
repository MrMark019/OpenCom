from pydantic import BaseModel
from typing import Optional, Literal


class UARTConfig(BaseModel):
    """UART configuration model"""
    baud_rate: int = 9600
    data_bits: Literal[5, 6, 7, 8] = 8
    stop_bits: Literal[1, 1.5, 2] = 1
    parity: Literal['none', 'even', 'odd', 'mark', 'space'] = 'none'
    flow_control: Literal['none', 'hardware', 'software'] = 'none'
    timeout: float = 1.0


class SerialPortInfo(BaseModel):
    """Serial port information model"""
    device: str
    name: str
    description: str
    hwid: str
    vendor_id: Optional[str] = None
    product_id: Optional[str] = None


class SerialMessage(BaseModel):
    """Serial message model for WebSocket communication"""
    type: Literal['receive', 'send', 'status', 'error']
    data: str
    timestamp: float
    port: Optional[str] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None