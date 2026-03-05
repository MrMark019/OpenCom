"""
WebSocket Manager - Handles real-time data streaming to clients
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.broadcast_queue = asyncio.Queue()
        self._broadcast_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket):
        """
        Connect a new WebSocket client
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket client
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients
        """
        # Add to broadcast queue
        await self.broadcast_queue.put(message)

    async def broadcast_loop(self):
        """
        Background task to process broadcast queue
        """
        while True:
            try:
                # Wait for message from queue
                message = await self.broadcast_queue.get()
                
                # Send to all connected clients
                if self.active_connections:
                    # Create tasks for each client
                    tasks = []
                    for connection in self.active_connections:
                        try:
                            # Send message to client
                            await connection.send_json(message)
                        except Exception as e:
                            logger.error(f"Error sending to client: {e}")
                            # Remove failed connection
                            if connection in self.active_connections:
                                self.active_connections.remove(connection)
                    
                self.broadcast_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("Broadcast loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send a personal message to a specific client
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    def get_connection_count(self) -> int:
        """
        Get number of active connections
        """
        return len(self.active_connections)

    async def cleanup(self):
        """
        Cleanup WebSocket manager
        """
        if self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for connection in self.active_connections[:]:
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        
        self.active_connections.clear()
        logger.info("WebSocket manager cleaned up")
