def decode_frame(frame: bytes, num_channels: int) -> list[int]:
    try:
        print(f"🔍 Decoding frame: {frame.hex()} (len={len(frame)})")
        values = []
        for i in range(num_channels):
            start = i * 3
            b = frame[start:start+3]
            # Decode 3-byte little-endian signed integer
            value = int.from_bytes(b, byteorder='little', signed=True)
            values.append(value)
        print(f"✅ Decoded values: {values}")
        return values
    except Exception as e:
        print(f"❌ Error decoding frame: {e}")
        return []


# --- EEGRecorder and record() reinstated below ---
import time
from typing import Optional
import numpy as np
from .serial_utils import list_serial_ports, open_serial_port
from .writer import write_edf

BYTES_PER_SAMPLE = 3
DEFAULT_SAMPLE_RATE = 256

class EEGRecorder:
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
        chunk_count = 0
        while time.time() < end_time:
            chunk = self._serial.read(64)
            print(f"📥 Read {len(chunk)} bytes: {chunk.hex()}")
            if not chunk:
                continue
            self._buffer.extend(chunk)
            if chunk_count < 5:
                print(f"Chunk {chunk_count}: {chunk.hex()}")
                chunk_count += 1
            if self.num_channels is None:
                self.num_channels = self._detect_channels()
                if self.num_channels:
                    frame_size = self.num_channels * BYTES_PER_SAMPLE
            if self.num_channels is None and len(self._buffer) > 1024:
                print("Channel auto-detection failed, defaulting to 4 channels")
                self.num_channels = 4
                frame_size = self.num_channels * BYTES_PER_SAMPLE
            print(f"🧪 Buffer size: {len(self._buffer)}, frame_size: {frame_size}")
            print(f"🔥 RAW BUFFER (first 32 bytes): {self._buffer[:32].hex()}")
            if not frame_size or len(self._buffer) < frame_size:
                print("🚫 Skipping frame decode loop — condition not met")
            else:
                print("🚨 Frame decode loop condition met")
            while frame_size and len(self._buffer) >= frame_size:
                frame = bytes(self._buffer[:frame_size])
                print(f"Decoding frame (size={len(frame)}, channels={self.num_channels}): {frame.hex()}")
                del self._buffer[:frame_size]
                decoded = decode_frame(frame, self.num_channels)
                if not decoded or len(decoded) != self.num_channels:
                    print(f"⚠️ Decode failed or unexpected shape: {decoded}")
                    continue
                print(f"✅ Decoded sample: {decoded}")
                samples.append(decoded)
        return samples

    def record_to_file(self, output_file: str, duration: float = 10, gain: float = 1.0) -> None:
        if self.port_name is None:
            ports = list_serial_ports()
            if not ports:
                raise RuntimeError("No serial ports found")
            self.port_name = ports[0]
        import serial
        with serial.Serial(self.port_name, baudrate=57600, timeout=1) as self._serial:
            sample_list = self._read_samples(duration)
        if not sample_list:
            raise RuntimeError("No samples captured")
        signals = []
        for ch in range(self.num_channels):
            signals.append(np.array([s[ch] for s in sample_list], dtype=np.int32))
        write_edf(output_file, signals, self.sample_rate, gain=gain)

def record(output_file: str, duration: float = 10, port: Optional[str] = None, gain: float = 1.0) -> None:
    EEGRecorder(port=port).record_to_file(output_file, duration, gain=gain)
