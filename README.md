# Pinguis: EEG Toolkit for Serial Amplifiers

Pinguis is a cross-platform EEG toolkit for capturing, decoding, recording, and visualizing raw brain signals from USB-CDC serial amplifiers. It started as a command-line EDF+ recorder and now includes a live GUI for real-time signal monitoring.

---

## ✅ Milestone 1: Command-Line Recording Utility (Complete)

### Summary
We built a functioning command-line EEG recorder on macOS using standard USB-CDC serial amplifiers. The recorder identifies available ports, reads incoming 3-byte-per-channel frames, decodes the data, and writes it to a compliant EDF+ file.

### Highlights
- Supports 2 or 4 channels
- Auto-detects channel configuration from frame size
- Writes fully valid EDF+ files (checked against reference tools)
- Handles serial port detection dynamically
- Built in Python 3.13 using `pyserial`, `pyedflib`, and `numpy`

### Command to run:

```bash
python scripts/run_record.py /dev/tty.usbserial-*
```

---

## ✅ Milestone 2: Real-Time GUI with Streamlit (Complete)

### Summary
A real-time EEG GUI was implemented using Streamlit. It provides live visualization of EEG signals from the amplifier, with channel-specific RMS readouts and an adjustable update interval.

### Highlights
- Live EEG waveform plotting (2–4 channels)
- Drop-down serial port selection
- Adjustable refresh rate (100ms–1000ms)
- RMS indicator for each channel
- Auto-detects channel count and frame size
- Graceful start/stop streaming toggling

### Command to run:

```bash
streamlit run pinguis/gui.py
```

---

## 🚧 Milestone 3: Recording & Mapping Enhancements (Planned)

### Objectives
- Add real-time EDF+ recording toggle in the GUI
- Support EDF file saving while streaming
- Introduce CSV export for post-processing workflows
- Improve UI layout and channel scaling controls
- Add head-map style channel visualizer (basic scalp topology)
- Add timestamp overlay or marker injection system
- Add signal quality estimation (flatlines, high noise)

---

## Project Status

Pinguis is now capable of:
- Reading and decoding serial EEG signals
- Saving raw EEG data to industry-standard `.edf` files
- Visualizing signals in real-time with an interactive UI

---

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Dependencies

- Python ≥ 3.13
- `pyserial`
- `pyedflib`
- `numpy`
- `streamlit`

---

## License

MIT License.
