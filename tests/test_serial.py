import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pinguis.serial_utils import list_serial_ports


def test_list_serial_ports_runs():
    ports = list_serial_ports()
    assert isinstance(ports, list)
