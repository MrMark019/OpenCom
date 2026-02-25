# Serial Debugger

XCOM V2.6 compatible serial debugger with enhanced CLI functionality.

## Features

### GUI Mode (Web-based)
- **Real-time serial port scanning** with hardware descriptions
- **Complete UART parameter configuration**:
  - Baud rates: 300 to 1843200 bps (with custom input support)
  - Data bits: 5, 6, 7, 8
  - Stop bits: 1, 1.5, 2
  - Parity: None, Odd, Even, Mark, Space
  - Flow control: DTR, RTS
- **ASCII/Hex receive display** with timestamps and auto-scroll
- **Multi-tab send control**:
  - Single line send (with hex mode and newline support)
  - Multi-line presets table (10+ commands)
  - Protocol transmission (Modbus-RTU, custom protocol)
- **File sending** with progress tracking
- **Timer-based auto-send** (1-999999ms interval)
- **Status bar** with S/R counters and real-time clock
- **WebSocket real-time communication**

### CLI Mode
```bash
# List available serial ports
serial-tool list
serial-tool list -v  # verbose mode

# Open interactive REPL mode
serial-tool open -p COM3 -b 9600
serial-tool open -p /dev/ttyUSB0 --dtr --rts

# Send data (one-shot)
serial-tool send -p COM3 "Hello World"
serial-tool send -p COM3 "FF 01 02" --hex
serial-tool send -p COM3 "data" --wait-response --timeout 5

# Monitor serial port
serial-tool monitor -p COM3
serial-tool monitor -p COM3 --logfile rx.log --timestamp --hex
```

### Interactive REPL Commands
```
> send "Hello World"     # Send ASCII string
> sendhex FF 01 02       # Send hex bytes
> sendfile data.bin      # Send file
> listen                 # Start displaying received data
> stop                   # Stop displaying
> status                 # Show connection status and counters
> set baud 19200         # Change baudrate
> set dtr true           # Set DTR line
> clear                  # Clear screen
> close                  # Exit
```

## Installation

### From Source
```bash
# Clone the repository
git clone https://github.com/OpenCom/serial-tool.git
cd serial-tool

# Install dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Using Docker
```bash
# Build and run
docker-compose up --build

# Access the API at http://localhost:8000
```

## Usage

### Quick Start
```bash
# Start the complete application (backend + frontend)
python start.py

# Or start backend only
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points
- **Web Interface**: http://localhost:8000 (or open `frontend/dist/index.html`)
- **API Documentation**: http://localhost:8000/api/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/api/redoc (ReDoc)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/ports` | GET | List available serial ports |
| `/api/connect` | POST | Connect to serial port |
| `/api/disconnect` | POST | Disconnect from serial port |
| `/api/status` | GET | Get connection status |
| `/api/send` | POST | Send data |
| `/api/send/hex` | POST | Send hex data |
| `/api/send/file` | POST | Send file |
| `/api/counters` | GET | Get S/R counters |
| `/api/counters/reset` | POST | Reset counters |
| `/api/ws` | WebSocket | Real-time data stream |

## Project Structure

```
serial-tool/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── serial_manager.py    # Serial port management
│   ├── port_scanner.py      # Cross-platform port detection
│   ├── websocket_manager.py # WebSocket handling
│   └── cli/
│       ├── __init__.py
│       ├── main.py          # CLI entry point
│       └── commands.py      # CLI commands
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── App.css          # Styles
│   │   ├── main.tsx         # React entry point
│   │   └── index.css        # Global styles
│   ├── index.html
│   ├── package.json
│   └── tsconfig.json
├── tests/
│   ├── test_serial_manager.py
│   └── test_api.py
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Technology Stack

- **Backend**: Python, FastAPI, pyserial, asyncio, websockets, Click
- **Frontend**: React, TypeScript, Vite, Zustand (for state management)
- **Deployment**: Docker, PyInstaller (for single-file executable)

## Development

### Setup Development Environment
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black backend/
isort backend/

# Type checking
mypy backend/
```

### Build Frontend
```bash
cd frontend
npm install
npm run build
```

### Build Single-file Executable
```bash
# Using PyInstaller (optional)
pip install pyinstaller
pyinstaller --one-file --add-data "frontend/dist:frontend/dist" start.py
```

## Platform Support

- **Windows**: COM1-COM255, WMI for hardware descriptions
- **Linux**: ttyUSB*, ttyACM*, udev for device info
- **macOS**: cu.*, ioreg for USB device info

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Inspired by XCOM V2.6 serial debugger
- Built with FastAPI and React
