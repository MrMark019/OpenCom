"""
Tests for Serial Manager
"""

import asyncio
import pytest
from backend.serial_manager import SerialManager


@pytest.fixture
def serial_manager():
    return SerialManager()


@pytest.mark.asyncio
async def test_serial_manager_initialization(serial_manager):
    """Test that serial manager initializes correctly"""
    await serial_manager.initialize()
    assert serial_manager.send_count == 0
    assert serial_manager.receive_count == 0
    assert not serial_manager.is_connected()


@pytest.mark.asyncio
async def test_counter_reset(serial_manager):
    """Test counter reset functionality"""
    serial_manager.send_count = 100
    serial_manager.receive_count = 200
    serial_manager.reset_counters()
    assert serial_manager.send_count == 0
    assert serial_manager.receive_count == 0


def test_data_callback(serial_manager):
    """Test data callback registration"""
    def callback(data, data_type):
        pass
    
    serial_manager.set_data_callback(callback)
    assert serial_manager._data_callback == callback


@pytest.mark.asyncio
async def test_status_when_disconnected(serial_manager):
    """Test status when not connected"""
    status = await serial_manager.get_status()
    assert status["connected"] is False
    assert status["send_count"] == 0
    assert status["receive_count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
