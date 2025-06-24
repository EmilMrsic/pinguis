import re
from typing import List

try:
    import serial
    from serial.tools import list_ports
except Exception:  # pragma: no cover - environment may not have pyserial
    serial = None
    list_ports = None


def list_serial_ports() -> List[str]:
    """Return a list of available serial port device names."""
    if list_ports is None:
        return []
    ports = [p.device for p in list_ports.comports()]
    # On macOS devices appear as /dev/tty.* or /dev/cu.*; filter accordingly
    mac_pattern = re.compile(r"/dev/(tty|cu)\..*")
    filtered = [p for p in ports if mac_pattern.match(p) or not p.startswith('/dev/')]
    return filtered


def open_serial_port(port: str, baudrate: int = 115200, timeout: float = 1.0):
    """Open a serial port if pyserial is available."""
    if serial is None:
        raise RuntimeError("pyserial is required to open serial ports")
    return serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
