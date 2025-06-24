import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import os

import pytest
pytest.importorskip("numpy")
import numpy as np

from pinguis.writer import write_edf


def test_write_edf_requires_pyedflib(tmp_path):
    signals = [np.zeros(10, dtype=np.int32)]
    out = tmp_path / "out.edf"
    try:
        write_edf(str(out), signals, 256)
    except RuntimeError as e:
        assert "pyedflib" in str(e)
    else:
        assert out.exists()
        os.remove(out)
