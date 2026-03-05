#!/usr/bin/env python3
import sys
import serial.tools.list_ports

ports = list(serial.tools.list_ports.comports())
print(f"Found {len(ports)} ports:")
for p in ports:
    print(f"  {p.device}: {p.description}")
