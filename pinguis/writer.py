from __future__ import annotations

from typing import List

import numpy as np

try:
    import pyedflib
except Exception:  # pragma: no cover - pyedflib may not be present
    pyedflib = None


def write_edf(filename: str, signals: List[np.ndarray], sample_rate: int, gain: float = 1.0) -> None:
    """Write EEG data to an EDF+ file.

    Parameters
    ----------
    filename:
        Path of the EDF file to create.
    signals:
        List of 1-D numpy arrays containing raw 24-bit integer values.
    sample_rate:
        Sampling rate of the signals.
    gain:
        Conversion factor from raw integer values to microvolts.
    """
    if pyedflib is None:
        raise RuntimeError("pyedflib is required to write EDF files")
    n_channels = len(signals)
    with pyedflib.EdfWriter(
        filename,
        n_channels=n_channels,
        file_type=pyedflib.FILETYPE_EDFPLUS,
    ) as writer:
        headers = []

        digital_min = -(2 ** 23)
        digital_max = (2 ** 23) - 1
        physical_min = digital_min * gain
        physical_max = digital_max * gain

        for i in range(n_channels):
            headers.append(
                {
                    "label": f"Ch{i+1}",
                    "dimension": "uV",
                    "sample_frequency": sample_rate,
                    "digital_min": digital_min,
                    "digital_max": digital_max,
                    "physical_min": physical_min,
                    "physical_max": physical_max,
                }
            )
        writer.setSignalHeaders(headers)

        phys_signals = [sig.astype(np.float64) * gain for sig in signals]
        writer.writePhysicalSamples(phys_signals)
