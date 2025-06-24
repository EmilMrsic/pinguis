import serial
import time

port = "/dev/tty.usbserial-AB9PPTQZ"
baud = 57600  # Updated baud rate for testing

with serial.Serial(port, baudrate=baud, timeout=1) as ser:
    ser.write(b's')  # Attempt to wake/start the amplifier
    time.sleep(0.1)
    print(f"Reading from {port} at {baud} baud...")
    for _ in range(10):
        data = ser.read(64)
        print(f"{len(data)} bytes: {data.hex()}")
        time.sleep(0.5)
