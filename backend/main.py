"""
Serial Debugger Backend - FastAPI Entry Point
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import backend modules
from .serial_manager import SerialManager
from .port_scanner import get_available_ports
from .websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
serial_manager = SerialManager()
websocket_manager = WebSocketManager()


class SerialConfig(BaseModel):
    port: str
    baudrate: int = 115200
    bytesize: int = 8
    parity: str = "N"  # N=none, O=odd, E=even, M=mark, S=space
    stopbits: float = 1.0
    dtr: bool = False
    rts: bool = False
    timeout: float = 1.0


class PortInfo(BaseModel):
    port: str
    description: str
    hardware_id: Optional[str] = None


class SendData(BaseModel):
    data: str
    is_hex: bool = False
    add_newline: bool = False


class TimerConfig(BaseModel):
    enabled: bool
    interval: int = 1000


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting Serial Debugger Backend...")
    
    # Initialize serial manager with websocket callback
    serial_manager.set_data_callback(on_serial_data)
    await serial_manager.initialize()
    
    # Start background tasks
    asyncio.create_task(websocket_manager.broadcast_loop())
    
    yield
    
    # Shutdown logic
    logger.info("Shutting down Serial Debugger Backend...")
    await serial_manager.cleanup()


def on_serial_data(data: bytes, data_type: str = "receive"):
    """
    Callback function when serial data is received
    """
    try:
        # Convert bytes to hex string
        hex_str = ' '.join([f'{b:02X}' for b in data])
        
        # Try to decode as text
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            text = None
        
        # Create message
        message = {
            "type": data_type,
            "bytes": list(data),
            "hex": hex_str,
            "text": text,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Broadcast to all WebSocket clients
        asyncio.create_task(websocket_manager.broadcast(message))
        
    except Exception as e:
        logger.error(f"Error in data callback: {e}")


app = FastAPI(
    title="Serial Debugger API",
    description="XCOM V2.6 compatible serial debugger backend",
    version="3.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "3.1.0"}


@app.get("/")
async def root():
    """Serve frontend index.html"""
    frontend_index = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
    if frontend_index.exists():
        return FileResponse(str(frontend_index))
    return {"message": "Serial Debugger API - Frontend not built yet. Run: cd frontend && npm run build"}


@app.get("/api/ports", response_model=List[PortInfo])
async def list_ports():
    """
    List all available serial ports with descriptions
    """
    try:
        ports = await get_available_ports()
        return [PortInfo(port=p.port, description=p.description, hardware_id=p.hardware_id) for p in ports]
    except Exception as e:
        logger.error(f"Error listing ports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/connect")
async def connect_serial(config: SerialConfig):
    """
    Connect to a serial port with specified configuration
    """
    try:
        await serial_manager.connect(config.dict())
        return {"success": True, "message": f"Connected to {config.port}"}
    except Exception as e:
        logger.error(f"Error connecting to {config.port}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/disconnect")
async def disconnect_serial():
    """
    Disconnect from the currently connected serial port
    """
    try:
        await serial_manager.disconnect()
        return {"success": True, "message": "Disconnected successfully"}
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """
    Get current serial port status
    """
    try:
        status = await serial_manager.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send")
async def send_data(data: str, is_hex: bool = False, add_newline: bool = False):
    """
    Send data to the connected serial port
    """
    try:
        if not serial_manager.is_connected():
            raise HTTPException(status_code=400, detail="Not connected to any serial port")
        
        # Add newline if requested
        if add_newline and not is_hex:
            data += "\r\n"
        
        await serial_manager.send(data, is_hex)
        return {"success": True, "message": "Data sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send/hex")
async def send_hex_data(data: SendData):
    """
    Send hex data to the connected serial port
    """
    try:
        if not serial_manager.is_connected():
            raise HTTPException(status_code=400, detail="Not connected to any serial port")
        
        await serial_manager.send(data.data, is_hex=True)
        return {"success": True, "message": "Hex data sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending hex data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send/file")
async def send_file(file: UploadFile = File(...), chunk_size: int = 1024):
    """
    Send file to the connected serial port
    """
    try:
        if not serial_manager.is_connected():
            raise HTTPException(status_code=400, detail="Not connected to any serial port")
        
        content = await file.read()
        
        # Send file in chunks
        total_size = len(content)
        sent = 0
        
        for i in range(0, total_size, chunk_size):
            chunk = content[i:i + chunk_size]
            await serial_manager.send_raw(chunk)
            sent += len(chunk)
        
        return {
            "success": True,
            "message": f"File sent successfully",
            "filename": file.filename,
            "size": total_size
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/counters")
async def get_counters():
    """
    Get send/receive byte counters
    """
    return {
        "send_count": serial_manager.send_count,
        "receive_count": serial_manager.receive_count
    }


@app.post("/api/counters/reset")
async def reset_counters():
    """
    Reset send/receive byte counters
    """
    serial_manager.reset_counters()
    return {"success": True, "message": "Counters reset"}


@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time serial data streaming
    """
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle client commands if needed
                if message.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)


# Add a simple test endpoint for development
@app.get("/api/test")
async def test_endpoint():
    return {"message": "Test endpoint working"}


# Import json at the top if not already imported
import json

# Serve frontend static assets (must be after all API routes)
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")
