from __future__ import annotations

import threading
import time
from collections import deque
from typing import List, Optional
import csv

import numpy as np

try:
    import streamlit as st
except Exception:  # pragma: no cover - streamlit may be missing in tests
    st = None

from pinguis.decoder import decode_frame, BYTES_PER_SAMPLE
from pinguis.serial_utils import list_serial_ports, open_serial_port
from pinguis.writer import write_edf


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
        # Recording / markers
        self.recording = False
        self.recorded: List[List[int]] = []
        self.start_time: Optional[float] = None
        self.markers: List[float] = []

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def start_recording(self) -> None:
        if not self.recording:
            self.recording = True
            self.recorded = [[] for _ in range(self.num_channels or 0)]
            self.start_time = time.time()
            self.markers = []

    def stop_recording(self) -> None:
        self.recording = False

    def add_marker(self) -> None:
        if self.recording and self.start_time is not None:
            self.markers.append(time.time() - self.start_time)

    def save_edf(self, path: str, gain: float = 1.0) -> None:
        if not self.recorded or self.num_channels is None:
            return
        signals = [np.array(ch, dtype=np.int32) for ch in self.recorded]
        write_edf(path, signals, self.sample_rate, gain=gain)

    def export_csv(self, path: str) -> None:
        if not self.recorded or self.num_channels is None:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([f"Ch{i+1}" for i in range(self.num_channels)])
            for row in zip(*self.recorded):
                writer.writerow(row)

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
                    if self.recording:
                        self.recorded[ch].append(value)

    def get_traces(self) -> List[np.ndarray]:
        return [np.array(d, dtype=np.int32) for d in self._deques]

    def get_rms(self) -> List[float]:
        traces = self.get_traces()
        rms: List[float] = []
        for arr in traces:
            if arr.size == 0:
                rms.append(0.0)
            else:
                value = np.mean(np.square(arr))
                rms.append(float(np.sqrt(value)) if value >= 0 else 0.0)
        return rms

    def get_quality(self) -> List[str]:
        rms = self.get_rms()
        quality: List[str] = []
        for val in rms:
            if val < 5:
                quality.append("flat")
            elif val > 5000:
                quality.append("noisy")
            else:
                quality.append("ok")
        return quality


def main() -> None:
    if st is None:
        raise RuntimeError("streamlit is required to run the GUI")

    st.title("Real-Time EEG Monitor")
    ports = list_serial_ports()
    port = st.selectbox("Serial Port", ports)
    update_ms = st.slider("Update rate (ms)", 100, 1000, 250, step=50)
    scale = st.slider("Amplitude scale", 0.1, 5.0, 1.0, step=0.1)

    if "reader" not in st.session_state:
        st.session_state.reader = None
        st.session_state.running = False
        st.session_state.recording = False
        st.session_state.csv_ready = False

    def toggle_stream() -> None:
        if st.session_state.running:
            reader = SerialReader(port)
            st.session_state.reader = reader
            reader.start()
        else:
            if st.session_state.reader:
                st.session_state.reader.stop()
                st.session_state.reader = None

    def toggle_recording() -> None:
        if not st.session_state.reader:
            st.session_state.recording = False
            return
        if st.session_state.recording:
            st.session_state.reader.start_recording()
        else:
            st.session_state.reader.stop_recording()
            st.session_state.reader.save_edf("output.edf")
            st.session_state.reader.export_csv("output.csv")
            st.session_state.csv_ready = True

    cols = st.columns(2)
    with cols[0]:
        st.checkbox("Start Streaming", key="running", on_change=toggle_stream)
        st.checkbox("Record EDF", key="recording", on_change=toggle_recording)
        if st.session_state.recording and st.session_state.running:
            if st.button("Add Marker"):
                st.session_state.reader.add_marker()
        if st.session_state.csv_ready:
            with open("output.csv", "r") as f:
                st.download_button("Download CSV", f, file_name="session.csv")
                st.session_state.csv_ready = False
    plot_area = cols[1].empty()
    status_area = st.empty()
    headmap_area = st.empty()

    if st.session_state.running and st.session_state.reader:
        traces = st.session_state.reader.get_traces()
        if traces:
            data = np.column_stack([t * scale for t in traces])
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            for ch in range(data.shape[1]):
                ax.plot(data[:, ch] + ch * 1000, label=f"Ch{ch+1}")
            for m in st.session_state.reader.markers:
                ax.axvline(m * st.session_state.reader.sample_rate, color="red", linestyle="--")
            ax.legend()
            plot_area.pyplot(fig)

            rms = st.session_state.reader.get_rms()
            quality = st.session_state.reader.get_quality()
            status_area.write(
                " ".join(
                    f"Ch{i+1}:{r:.1f}({q})" for i, (r, q) in enumerate(zip(rms, quality))
                )
            )

            # basic head map
            if st.session_state.reader.num_channels in (2, 4):
                coords = [(0.3, 0.8), (0.7, 0.8)]
                if st.session_state.reader.num_channels == 4:
                    coords += [(0.3, 0.2), (0.7, 0.2)]
                fig2, ax2 = plt.subplots()
                ax2.scatter(*zip(*coords), c=rms, s=200, cmap="viridis")
                ax2.set_xlim(0, 1)
                ax2.set_ylim(0, 1)
                ax2.axis("off")
                headmap_area.pyplot(fig2)
        time.sleep(update_ms / 1000)
        st.rerun()


if __name__ == "__main__":  # pragma: no cover - manual launch
    main()

