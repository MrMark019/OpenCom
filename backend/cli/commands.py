"""
Serial Debugger CLI Commands
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional

import click

# Import backend modules
from ..port_scanner import get_available_ports
from ..serial_manager import SerialManager


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def list_ports(verbose: bool = False):
    """
    List all available serial ports with descriptions
    
    Shows COM ports on Windows, ttyUSB* on Linux, and cu.* on macOS.
    """
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        ports = loop.run_until_complete(get_available_ports())
        
        if not ports:
            click.echo("No serial ports found")
            return
        
        click.echo(f"Available serial ports ({len(ports)}):")
        click.echo("-" * 60)
        
        for i, port in enumerate(ports, 1):
            status = "[已断开]" if "disconnected" in port.description.lower() else ""
            click.echo(f"{i:2d}. {port.port:<15} - {port.description} {status}")
            
            if verbose and port.hardware_id:
                click.echo(f"     Hardware ID: {port.hardware_id}")
        
        loop.close()
        
    except Exception as e:
        click.echo(f"Error listing ports: {e}", err=True)
        sys.exit(1)


@click.command()
@click.option('--port', '-p', help='Serial port to connect to (e.g., COM3, /dev/ttyUSB0)')
@click.option('--baud', '-b', default=115200, type=int, help='Baud rate (default: 115200)')
@click.option('--bytesize', default=8, type=click.Choice(['5', '6', '7', '8']), help='Data bits (default: 8)')
@click.option('--parity', default='none',
              type=click.Choice(['none', 'odd', 'even', 'mark', 'space'], case_sensitive=False),
              help='Parity (default: none)')
@click.option('--stopbits', default='1', type=click.Choice(['1', '1.5', '2']), help='Stop bits (default: 1)')
@click.option('--dtr', is_flag=True, help='Enable DTR control')
@click.option('--rts', is_flag=True, help='Enable RTS control')
@click.option('--hex', 'hex_mode', is_flag=True, help='Force hex mode display')
def open_interactive(port: Optional[str], baud: int, bytesize: str, parity: str,
                     stopbits: str, dtr: bool, rts: bool, hex_mode: bool):
    """
    Open serial port in interactive REPL mode
    
    Enter commands like:
      > send "Hello World"
      > sendhex FF 01 02
      > sendfile data.bin
      > listen
      > stop
      > status
      > set baud 19200
      > close
    """
    serial_manager = SerialManager()
    listening = False
    listen_task = None
    
    try:
        # If no port specified, auto-detect first available
        if not port:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            ports = loop.run_until_complete(get_available_ports())
            loop.close()
            
            if not ports:
                click.echo("No available serial ports found", err=True)
                return
            port = ports[0].port
            click.echo(f"Auto-selected port: {port}")
        
        # Connect to serial port
        config = {
            "port": port,
            "baudrate": baud,
            "bytesize": bytesize,
            "parity": parity.upper()[0] if parity != 'none' else 'N',
            "stopbits": stopbits,
            "dtr": dtr,
            "rts": rts,
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(serial_manager.connect(config))
        click.echo(click.style(f"Connected to {port} at {baud} baud", fg='green'))
        
        # Data callback for listening
        received_data = []
        
        def on_data(data: bytes, data_type: str):
            if data_type == "receive":
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                if hex_mode:
                    hex_str = ' '.join([f'{b:02X}' for b in data])
                    click.echo(click.style(f"[{timestamp}] [RX][HEX] {hex_str}", fg='cyan'))
                else:
                    try:
                        text = data.decode('utf-8')
                        click.echo(click.style(f"[{timestamp}] [RX][ASCII] {text}", fg='cyan'))
                    except UnicodeDecodeError:
                        hex_str = ' '.join([f'{b:02X}' for b in data])
                        click.echo(click.style(f"[{timestamp}] [RX][HEX] {hex_str}", fg='cyan'))
                received_data.append(data)
        
        serial_manager.set_data_callback(on_data)
        
        # Interactive REPL
        click.echo("\nEnter commands (type 'help' for list, 'close' to exit):\n")
        
        while True:
            try:
                # Read command
                cmd_line = input("> ").strip()
                
                if not cmd_line:
                    continue
                
                parts = cmd_line.split(None, 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == "help":
                    click.echo("Available commands:")
                    click.echo("  send <string>       - Send ASCII string")
                    click.echo("  sendhex <hex>       - Send hex string (e.g., 'FF 01 02')")
                    click.echo("  sendfile <file>     - Send file with progress")
                    click.echo("  listen              - Start receiving and displaying")
                    click.echo("  stop                - Stop receiving display")
                    click.echo("  status              - Show S/R counters and status")
                    click.echo("  set <param> <val>   - Set parameter (baud, dtr, rts)")
                    click.echo("  clear               - Clear screen")
                    click.echo("  close               - Close connection and exit")
                    
                elif command == "send":
                    if not args:
                        click.echo("Usage: send <string>")
                        continue
                    
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    loop.run_until_complete(serial_manager.send(args))
                    if hex_mode:
                        hex_str = ' '.join([f'{b:02X}' for b in args.encode()])
                        click.echo(click.style(f"[{timestamp}] [TX][HEX] {hex_str}", fg='blue'))
                    else:
                        click.echo(click.style(f"[{timestamp}] [TX][ASCII] {args}", fg='blue'))
                    
                elif command == "sendhex":
                    if not args:
                        click.echo("Usage: sendhex <hex string>")
                        continue
                    
                    loop.run_until_complete(serial_manager.send(args, is_hex=True))
                    hex_clean = args.replace(" ", "").replace("0x", "")
                    hex_formatted = ' '.join(hex_clean[i:i+2] for i in range(0, len(hex_clean), 2))
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    click.echo(click.style(f"[{timestamp}] [TX][HEX] {hex_formatted}", fg='blue'))
                    
                elif command == "sendfile":
                    if not args:
                        click.echo("Usage: sendfile <filename>")
                        continue
                    
                    if not os.path.exists(args):
                        click.echo(click.style(f"File not found: {args}", fg='red'))
                        continue
                    
                    try:
                        with open(args, 'rb') as f:
                            content = f.read()
                        
                        # Send in chunks
                        chunk_size = 1024
                        total_size = len(content)
                        sent = 0
                        
                        click.echo(f"Sending {args} ({total_size} bytes)...")
                        
                        for i in range(0, total_size, chunk_size):
                            chunk = content[i:i + chunk_size]
                            loop.run_until_complete(serial_manager.send_raw(chunk))
                            sent += len(chunk)
                            progress = (sent / total_size) * 100
                            click.echo(f"\rProgress: {progress:.1f}%", nl=False)
                        
                        click.echo(f"\nFile sent successfully!")
                        
                    except Exception as e:
                        click.echo(click.style(f"Error sending file: {e}", fg='red'))
                    
                elif command == "listen":
                    listening = True
                    click.echo("Listening for incoming data... (type 'stop' to stop displaying)")
                    
                elif command == "stop":
                    listening = False
                    click.echo("Stopped listening")
                    
                elif command == "status":
                    status = loop.run_until_complete(serial_manager.get_status())
                    click.echo("Status:")
                    click.echo(f"  Connected: {status['connected']}")
                    if status['connected']:
                        click.echo(f"  Port: {status['port']}")
                        click.echo(f"  Baudrate: {status['baudrate']}")
                        click.echo(f"  Data bits: {status['bytesize']}")
                        click.echo(f"  Parity: {status['parity']}")
                        click.echo(f"  Stop bits: {status['stopbits']}")
                    click.echo(f"  Sent bytes: {status['send_count']}")
                    click.echo(f"  Received bytes: {status['receive_count']}")
                    
                elif command == "set":
                    if not args:
                        click.echo("Usage: set <parameter> <value>")
                        continue
                    
                    set_parts = args.split()
                    if len(set_parts) < 2:
                        click.echo("Usage: set <parameter> <value>")
                        continue
                    
                    param, value = set_parts[0], set_parts[1]
                    
                    if param == "baud":
                        try:
                            new_baud = int(value)
                            loop.run_until_complete(serial_manager.update_config(baudrate=new_baud))
                            click.echo(f"Baudrate changed to {new_baud}")
                        except ValueError:
                            click.echo("Invalid baudrate value")
                    elif param == "dtr":
                        new_dtr = value.lower() in ('true', '1', 'yes', 'on')
                        loop.run_until_complete(serial_manager.update_config(dtr=new_dtr))
                        click.echo(f"DTR set to {new_dtr}")
                    elif param == "rts":
                        new_rts = value.lower() in ('true', '1', 'yes', 'on')
                        loop.run_until_complete(serial_manager.update_config(rts=new_rts))
                        click.echo(f"RTS set to {new_rts}")
                    else:
                        click.echo(f"Unknown parameter: {param}")
                    
                elif command == "clear":
                    click.clear()
                    
                elif command == "close":
                    loop.run_until_complete(serial_manager.disconnect())
                    click.echo("Connection closed")
                    break
                    
                else:
                    click.echo(f"Unknown command: {command}")
                    
            except KeyboardInterrupt:
                click.echo("\nExiting...")
                break
            except EOFError:
                click.echo("\nExiting...")
                break
            except Exception as e:
                click.echo(click.style(f"Error: {e}", fg='red'))
        
        loop.run_until_complete(serial_manager.disconnect())
        loop.close()
                
    except Exception as e:
        click.echo(click.style(f"Error in interactive mode: {e}", fg='red'), err=True)
        sys.exit(1)


@click.command()
@click.option('--port', '-p', required=True, help='Serial port to use (e.g., COM3, /dev/ttyUSB0)')
@click.option('--baud', '-b', default=115200, type=int, help='Baud rate (default: 115200)')
@click.option('--bytesize', default='8', type=click.Choice(['5', '6', '7', '8']), help='Data bits (default: 8)')
@click.option('--parity', default='none',
              type=click.Choice(['none', 'odd', 'even', 'mark', 'space'], case_sensitive=False),
              help='Parity (default: none)')
@click.option('--stopbits', default='1', type=click.Choice(['1', '1.5', '2']), help='Stop bits (default: 1)')
@click.option('--dtr', is_flag=True, help='Enable DTR control')
@click.option('--rts', is_flag=True, help='Enable RTS control')
@click.option('--wait-response', is_flag=True, help='Wait for response before exiting')
@click.option('--timeout', default=5.0, type=float, help='Response timeout in seconds (default: 5)')
@click.option('--hex', 'hex_mode', is_flag=True, help='Send as hex')
@click.argument('data', required=False)
def send_data(port: str, baud: int, bytesize: str, parity: str, stopbits: str,
               dtr: bool, rts: bool, wait_response: bool, timeout: float,
               hex_mode: bool, data: Optional[str]):
    """
    Send data to serial port and exit
    
    Example: serial-tool send -p COM3 "Hello World" --wait-response --timeout 5
    """
    try:
        # Create serial manager
        serial_manager = SerialManager()

        # Connect
        config = {
            "port": port,
            "baudrate": baud,
            "bytesize": int(bytesize),
            "parity": parity.upper()[0] if parity != 'none' else 'N',
            "stopbits": float(stopbits),
            "dtr": dtr,
            "rts": rts,
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(serial_manager.connect(config))

        # Get data to send
        if not data:
            # Try to get data from stdin
            if not sys.stdin.isatty():
                data = sys.stdin.read().strip()
        
        if not data:
            click.echo("No data to send", err=True)
            sys.exit(1)
        
        # Send data
        loop.run_until_complete(serial_manager.send(data, is_hex=hex_mode))
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if hex_mode:
            hex_clean = data.replace(" ", "").replace("0x", "")
            hex_formatted = ' '.join(hex_clean[i:i+2] for i in range(0, len(hex_clean), 2))
            click.echo(click.style(f"[{timestamp}] [TX][HEX] {hex_formatted}", fg='blue'))
        else:
            click.echo(click.style(f"[{timestamp}] [TX][ASCII] {data}", fg='blue'))
        
        if wait_response:
            click.echo(f"Waiting for response (timeout: {timeout}s)...")
            
            received = []
            
            def on_data(data: bytes, data_type: str):
                if data_type == "receive":
                    received.append(data)
            
            serial_manager.set_data_callback(on_data)
            
            # Wait for data or timeout
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                if received:
                    break
                loop.run_until_complete(asyncio.sleep(0.1))
            
            if received:
                click.echo("Response received!")
            else:
                click.echo("No response received (timeout)")
        
        # Disconnect
        loop.run_until_complete(serial_manager.disconnect())
        loop.close()
        
    except Exception as e:
        click.echo(click.style(f"Error sending data: {e}", fg='red'), err=True)
        sys.exit(1)


@click.command()
@click.option('--port', '-p', required=True, help='Serial port to monitor (e.g., COM3, /dev/ttyUSB0)')
@click.option('--baud', '-b', default=115200, type=int, help='Baud rate (default: 115200)')
@click.option('--logfile', '-l', help='Log file to write received data')
@click.option('--timestamp', '-t', is_flag=True, help='Add timestamps to log entries')
@click.option('--hex', 'hex_mode', is_flag=True, help='Display in hex mode')
def monitor_serial(port: str, baud: int, logfile: Optional[str], timestamp: bool, hex_mode: bool):
    """
    Monitor serial port and display/log received data
    
    Example: serial-tool monitor -p COM3 --logfile rx.log --timestamp
    """
    try:
        # Create serial manager
        serial_manager = SerialManager()
        
        # Connect
        config = {
            "port": port,
            "baudrate": baud,
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(serial_manager.connect(config))
        
        click.echo(click.style(f"Monitoring {port} at {baud} baud...", fg='green'))
        click.echo("Press Ctrl+C to stop\n")
        
        # Open log file if specified
        log_file = None
        if logfile:
            log_file = open(logfile, 'a')
            click.echo(f"Logging to: {logfile}")
        
        # Data callback
        def on_data(data: bytes, data_type: str):
            if data_type == "receive":
                time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                if hex_mode:
                    hex_str = ' '.join([f'{b:02X}' for b in data])
                    output = f"[{time_str}] [RX][HEX] {hex_str}"
                    click.echo(click.style(output, fg='cyan'))
                else:
                    try:
                        text = data.decode('utf-8')
                        output = f"[{time_str}] [RX][ASCII] {text}"
                        click.echo(click.style(output, fg='cyan'))
                    except UnicodeDecodeError:
                        hex_str = ' '.join([f'{b:02X}' for b in data])
                        output = f"[{time_str}] [RX][HEX] {hex_str}"
                        click.echo(click.style(output, fg='cyan'))
                
                if log_file:
                    log_file.write(output + "\n")
                    log_file.flush()
        
        serial_manager.set_data_callback(on_data)
        
        # Monitor loop
        try:
            while True:
                loop.run_until_complete(asyncio.sleep(0.1))
                
        except KeyboardInterrupt:
            click.echo("\n\nStopped monitoring")
            
        finally:
            if log_file:
                log_file.close()
            
            # Show summary
            status = loop.run_until_complete(serial_manager.get_status())
            click.echo(f"\nSummary:")
            click.echo(f"  Received bytes: {status['receive_count']}")
        
        # Disconnect
        loop.run_until_complete(serial_manager.disconnect())
        loop.close()
        
    except Exception as e:
        click.echo(click.style(f"Error monitoring serial: {e}", fg='red'), err=True)
        sys.exit(1)
