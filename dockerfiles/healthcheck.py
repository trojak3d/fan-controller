import serial
import time
import sys
import os

SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyESP')  # Serial port for ESP8266
BAUD_RATE = int(os.getenv('BAUD_RATE', 115200))
TIMEOUT = 2  # seconds
MAX_RETRIES = 3  # number of connection attempts

def check_esp():
    """Check if ESP8266 serial port exists and is readable."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
                ser.reset_input_buffer()
                time.sleep(0.5)  # Give buffer time to fill

                # Try reading at least one line
                start = time.time()
                while time.time() - start < TIMEOUT:
                    if ser.in_waiting:
                        line = ser.readline().decode(errors="ignore").strip()
                        if line:
                            return True  # Got a line → healthy
                # No data read in timeout window
                return False
        except serial.SerialException:
            time.sleep(0.5)  # Wait before retrying
    return False

if check_esp():
    sys.exit(0)  # Healthy
else:
    sys.exit(1)  # Unhealthy
