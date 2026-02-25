import os
from pathlib import Path

# Application configuration
APP_NAME = "Serial Debugger"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "XCOM V2.6 compatible serial debugger with CLI enhancements"

# Default settings
DEFAULT_BAUD_RATE = 9600
DEFAULT_DATA_BITS = 8
DEFAULT_STOP_BITS = 1
DEFAULT_PARITY = "none"
DEFAULT_FLOW_CONTROL = "none"
DEFAULT_TIMEOUT = 1.0

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "serial-debugger.log"

# WebSocket configuration
WEBSOCKET_PING_INTERVAL = 30
WEBSOCKET_PING_TIMEOUT = 10

# CLI configuration
CLI_DEFAULT_PORT = os.getenv("SERIAL_PORT", "")
CLI_DEFAULT_BAUD_RATE = int(os.getenv("BAUD_RATE", str(DEFAULT_BAUD_RATE)))

# Frontend configuration
FRONTEND_BUILD_DIR = "frontend/build"
FRONTEND_STATIC_DIR = "frontend/static"

# Paths
ROOT_DIR = Path(__file__).parent
BACKEND_DIR = ROOT_DIR / "backend"
SHARED_DIR = ROOT_DIR / "shared"
FRONTEND_DIR = ROOT_DIR / "frontend"
TESTS_DIR = ROOT_DIR / "tests"