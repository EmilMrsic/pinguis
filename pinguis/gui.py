from __future__ import annotations

import threading
import time
from collections import deque
from typing import List, Optional

import numpy as np

try:
    import streamlit as st
except Exception:  # pragma: no cover - streamlit may be missing in tests
    st = None

from .decoder import decode_frame, BYTES_PER_SAMPLE
from .serial_utils import list_serial_ports, open_serial_port


class SerialReader:
    """Background thread that reads EEG samples from a serial port."""

    def __init__(self, port: str, sample_rate: int = 256, buffer_seconds: int = 5, baudrate: int = 57600):
        self.port = port
        self.sample_rate = sample_rate
        self.buffer_seconds = buffer_seconds
        self.baudrate = baudrate
        self.num_channels: Optional[int] = None
        self._serial = None
        self._buffer = bytearray()
        self._deques: List[deque[int]] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
        self._thread = None
        self._serial = None

    def _detect_channels(self) -> Optional[int]:
        size = len(self._buffer)
        if size % 12 == 0:
            return 4
        if size % 6 == 0:
            return 2
        return None

    def _run(self) -> None:
        try:
            self._serial = open_serial_port(self.port, baudrate=self.baudrate, timeout=1)
        except Exception:
            return
        frame_size = None
        while not self._stop_event.is_set():
            chunk = self._serial.read(64)
            if not chunk:
                continue
            self._buffer.extend(chunk)
            if self.num_channels is None:
                self.num_channels = self._detect_channels()
                if self.num_channels:
                    frame_size = self.num_channels * BYTES_PER_SAMPLE
                    self._deques = [deque(maxlen=self.sample_rate * self.buffer_seconds) for _ in range(self.num_channels)]
            if not frame_size or len(self._buffer) < frame_size:
                continue
            while frame_size and len(self._buffer) >= frame_size:
                frame = bytes(self._buffer[:frame_size])
                del self._buffer[:frame_size]
                try:
                    decoded = decode_frame(frame, self.num_channels)
                except Exception:
                    continue
                for ch, value in enumerate(decoded):
                    self._deques[ch].append(value)

    def get_traces(self) -> List[np.ndarray]:
        return [np.array(d, dtype=np.int32) for d in self._deques]

    def get_rms(self) -> List[float]:
        traces = self.get_traces()
        rms: List[float] = []
        for arr in traces:
            if arr.size == 0:
                rms.append(0.0)
            else:
                rms.append(float(np.sqrt(np.mean(np.square(arr)))))
        return rms


def main() -> None:
    if st is None:
        raise RuntimeError("streamlit is required to run the GUI")

    st.title("Real-Time EEG Monitor")
    ports = list_serial_ports()
    port = st.selectbox("Serial Port", ports)
    update_ms = st.slider("Update rate (ms)", 100, 1000, 250, step=50)

    if "reader" not in st.session_state:
        st.session_state.reader = None
        st.session_state.running = False

    def toggle_stream() -> None:
        if st.session_state.running:
            reader = SerialReader(port)
            st.session_state.reader = reader
            reader.start()
        else:
            if st.session_state.reader:
                st.session_state.reader.stop()
                st.session_state.reader = None

    st.checkbox("Start Streaming", key="running", on_change=toggle_stream)
    plot_area = st.empty()
    status_area = st.empty()

    if st.session_state.running and st.session_state.reader:
        traces = st.session_state.reader.get_traces()
        if traces:
            data = np.column_stack(traces)
            plot_area.line_chart(data)
            rms = st.session_state.reader.get_rms()
            status_area.write(" ".join(f"Ch{i+1}:{r:.1f}" for i, r in enumerate(rms)))
        time.sleep(update_ms / 1000)
        st.experimental_rerun()


if __name__ == "__main__":  # pragma: no cover - manual launch
    main()

