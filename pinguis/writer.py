from __future__ import annotations

from typing import List

import numpy as np

try:
    import pyedflib
except Exception:  # pragma: no cover - pyedflib may not be present
    pyedflib = None


def write_edf(filename: str, signals: List[np.ndarray], sample_rate: int) -> None:
    """Write EEG data to an EDF+ file."""
    if pyedflib is None:
        raise RuntimeError("pyedflib is required to write EDF files")
    n_channels = len(signals)
    with pyedflib.EdfWriter(
        filename,
        n_channels=n_channels,
        file_type=pyedflib.FILETYPE_EDFPLUS,
    ) as writer:
        headers = []
        for i in range(n_channels):
            headers.append({
                "label": f"Ch{i+1}",
                "dimension": "uV",
                "sample_frequency": sample_rate,
            })
        writer.setSignalHeaders(headers)
        writer.writeSamples(signals)
