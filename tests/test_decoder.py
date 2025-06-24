import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest

from pinguis.decoder import decode_frame, _decode_24bit_le


def test_decode_24bit_le_positive():
    assert _decode_24bit_le(b"\x00\x00\x00") == 0
    assert _decode_24bit_le(b"\xff\x7f\x00") == 32767


def test_decode_frame_two_channels():
    data = b"\x01\x00\x00\x02\x00\x00"
    assert decode_frame(data, 2) == [1, 2]

