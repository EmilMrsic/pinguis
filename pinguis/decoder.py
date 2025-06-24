from __future__ import annotations

from typing import List

BYTES_PER_SAMPLE = 3
DEFAULT_SAMPLE_RATE = 256


def _decode_24bit_le(value: bytes) -> int:
    """Convert 3 little-endian bytes to a signed integer."""
    if len(value) != 3:
        raise ValueError("expected 3 bytes")
    # Expand to 4 bytes for signed conversion
    unsigned = int.from_bytes(value + (b"\x00" if value[2] < 0x80 else b"\xff"), "little", signed=True)
    return unsigned


def decode_frame(frame: bytes, num_channels: int) -> List[int]:
    """Decode a single frame into integer samples."""
    if len(frame) != num_channels * BYTES_PER_SAMPLE:
        raise ValueError("frame size mismatch")
    samples = []
    for ch in range(num_channels):
        start = ch * BYTES_PER_SAMPLE
        sample_bytes = frame[start : start + BYTES_PER_SAMPLE]
        samples.append(_decode_24bit_le(sample_bytes))
    return samples

