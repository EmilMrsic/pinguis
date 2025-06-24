from __future__ import annotations

import time
from typing import Optional

import numpy as np

from .serial_utils import list_serial_ports, open_serial_port
from .decoder import BYTES_PER_SAMPLE, decode_frame, DEFAULT_SAMPLE_RATE
from .writer import write_edf


class EEGRecorder:
    """Simple EEG recorder that reads from a serial port and writes EDF."""

    def __init__(self, port: Optional[str] = None, sample_rate: int = DEFAULT_SAMPLE_RATE):
        self.port_name = port
        self.sample_rate = sample_rate
        self.num_channels: Optional[int] = None
        self._serial = None
        self._buffer = bytearray()

    def _detect_channels(self) -> Optional[int]:
        size = len(self._buffer)
        if size % 12 == 0:
            return 4
        if size % 6 == 0:
            return 2
        return None

    def _read_samples(self, duration: float) -> list[list[int]]:
        samples = []
        frame_size = None if self.num_channels is None else self.num_channels * BYTES_PER_SAMPLE
        end_time = time.time() + duration
        while time.time() < end_time:
            chunk = self._serial.read(64)
            if not chunk:
                continue
            self._buffer.extend(chunk)
            if self.num_channels is None:
                self.num_channels = self._detect_channels()
                if self.num_channels:
                    frame_size = self.num_channels * BYTES_PER_SAMPLE
            while frame_size and len(self._buffer) >= frame_size:
                frame = bytes(self._buffer[:frame_size])
                del self._buffer[:frame_size]
                samples.append(decode_frame(frame, self.num_channels))
        return samples

    def record_to_file(self, output_file: str, duration: float = 10) -> None:
        if self.port_name is None:
            ports = list_serial_ports()
            if not ports:
                raise RuntimeError("No serial ports found")
            self.port_name = ports[0]
        with open_serial_port(self.port_name) as self._serial:
            sample_list = self._read_samples(duration)
        if not sample_list:
            raise RuntimeError("No samples captured")
        signals = []
        for ch in range(self.num_channels):
            signals.append(np.array([s[ch] for s in sample_list], dtype=np.int32))
        write_edf(output_file, signals, self.sample_rate)


def record(output_file: str, duration: float = 10, port: Optional[str] = None) -> None:
    EEGRecorder(port=port).record_to_file(output_file, duration)
