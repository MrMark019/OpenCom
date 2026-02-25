"""
Serial Debugger CLI Entry Point
"""

import sys
import click

# Fix Windows console encoding for Chinese characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Import CLI commands
from .commands import list_ports, open_interactive, send_data, monitor_serial


@click.group()
@click.version_option("3.1.0", prog_name="serial-tool")
def cli():
    """
    Serial Debugger Command Line Interface
    
    XCOM V2.6 compatible serial debugger with enhanced CLI functionality.
    
    \b
    Examples:
        serial-tool list                    # List available ports
        serial-tool open -p COM3 -b 9600    # Open interactive mode
        serial-tool send -p COM3 "Hello"    # Send data
        serial-tool monitor -p COM3         # Monitor serial port
    
    For more information, visit: https://github.com/OpenCom/serial-tool
    """
    pass


# Register commands
cli.add_command(list_ports, name="list")
cli.add_command(open_interactive, name="open")
cli.add_command(send_data, name="send")
cli.add_command(monitor_serial, name="monitor")


# Main entry point for development
if __name__ == "__main__":
    cli()
