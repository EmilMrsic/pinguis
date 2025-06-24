# Pinguis: Command-Line EEG Recorder

Pinguis is a cross-platform EEG toolkit that can record from serial devices and now includes a simple real-time GUI built with Streamlit.

## Milestone 1: macOS CLI Prototype

This first milestone is focused on building a command-line EEG recording utility on macOS using standard USB-CDC EEG amplifiers. The goal is to capture real-time raw EEG data, decode it, and write it to EDF+ format, while designing for future cross-platform compatibility with Windows.

### Development Context
- Development is taking place on macOS.
- EEG amplifiers appear as USB-CDC (virtual COM) devices and are accessed using built-in drivers (`IOUSBHostCDC`) on macOS.
- Devices will also be supported on Windows where they show up as COM ports.
- Future hardware may use FTDI/D2XX drivers, but this is not in scope for Phase One.

### Phase One Tasks
1. **Environment Setup**
   - Python 3.13+ with a virtual environment
   - Dependencies: `pyserial`, `pyedflib`, `numpy`

2. **Serial Port Discovery**
   - List available `/dev/tty.*` and `/dev/cu.*` devices
   - Detect amplifier by plug/unplug testing and identifying stable ports

3. **Raw Byte Streaming**
   - Open serial port and dump incoming byte stream
   - Verify stable 256 Hz signal
   - Frame format is 3 bytes per channel, little-endian

4. **Signal Decoding**
   - Convert byte stream to integer values per sample
   - Auto-detect 2 vs 4 channel configuration based on frame size
   - Store decoded signal in memory

5. **EDF+ Writer**
   - Use `pyedflib` to construct valid EDF+ file
   - Include metadata headers, signal labels, and proper sample rate
   - Write samples as blocks with accurate timing

6. **Validation**
   - Compare generated EDF+ files against known-good reference
   - Confirm integrity of header and sample data

## Real-Time GUI

The `pinguis.gui` module offers a basic Streamlit application for monitoring
incoming EEG data live. Run the app with `streamlit run -m pinguis.gui` and
select the desired serial port. The GUI plots the most recent few seconds of
data for each channel and displays a simple RMS indicator.

---

MIT License.
