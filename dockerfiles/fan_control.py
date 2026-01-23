import os
import serial
import time
import logging
import requests
import subprocess
import json

# =========================
# Configuration via Environment Variables
# =========================
SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyESP')  # Serial port for ESP8266
BAUD_RATE = int(os.getenv('BAUD_RATE', 115200))
TRUENAS_HOST = os.environ["TRUENAS_HOST"]
API_KEY = os.environ["TRUENAS_API_KEY"]

# Fan curve limits
MIN_TEMP = int(os.getenv('MIN_TEMP', 30))  # Minimum temperature
MAX_TEMP = int(os.getenv('MAX_TEMP', 70))  # Maximum temperature
MIN_FAN = int(os.getenv('MIN_FAN', 20))   # Minimum fan speed (%)
MAX_FAN = int(os.getenv('MAX_FAN', 100))  # Maximum fan speed (%)

# Enable detailed logging
LOG_DETAIL = os.getenv('LOG_DETAIL', 'false').lower() == 'true'

# EMA smoothing factor for fan curve (0=slow, 1=instant)
EMA_ALPHA = 0.3
ema_temp = None  # Smoothed temperature value

# =========================
# Logging configuration
# =========================
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# =========================
# Function: Calculate fan speed
# =========================
def calculate_fan_speed(temp: float) -> int:
    """
    Calculate fan speed based on smoothed temperature using a linear fan curve.

    Args:
        temp (float): Smoothed temperature in Celsius

    Returns:
        int: Fan speed percentage (MIN_FAN-MAX_FAN)
    """
    if temp <= MIN_TEMP:
        return MIN_FAN
    elif temp >= MAX_TEMP:
        return MAX_FAN
    else:
        scale = (temp - MIN_TEMP) / (MAX_TEMP - MIN_TEMP)
        return int(MIN_FAN + scale * (MAX_FAN - MIN_FAN))

# =========================
# Function: Get drive temperatures
# =========================
def get_drive_temperatures() -> list[int]:
    """
    Get cached disk temperatures from TrueNAS API.
    Disks are never woken from standby.
    """
    try:
        url = f"{TRUENAS_HOST}/api/v2.0/disk/temperatures"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        resp = requests.get(url, headers=headers, verify=False)
        resp.raise_for_status()
        disk_temps = resp.json()  # e.g., {"sda": 27, "sdb": 23, ...}
        temps = list(disk_temps.values())
        if os.environ.get("LOG_DETAIL", "false").lower() == "true":
            for dev, temp in disk_temps.items():
                print(f"{dev}: {temp}°C (cached)")
        return temps
    except Exception as e:
        print(f"Failed to get cached disk temperatures: {e}")
        return []

# =========================
# Function: Get system temperatures
# =========================
def get_system_temperatures() -> list[int]:
    """
    Collect system temperatures using `sensors` command
    while ignoring high/crit/max limit values.
    Logs each sensor and temperature found.
    """
    temps = []
    try:
        output = os.popen('sensors').read()
        for line in output.splitlines():
            if "temp" in line.lower() and "°C" in line and "(" not in line:
                parts = line.split()
                for part in parts:
                    if part.endswith("°C") and part.startswith(("+", "-")):
                        try:
                            temp = int(float(part[:-2]))
                            temps.append(temp)
                            logging.info(f'Sensor reading: {line.strip()} -> {temp}°C')
                        except:
                            continue
    except Exception as e:
        logging.warning(f'Failed to read system sensors: {e}')
    return temps

# =========================
# Function: Connect to ESP
# =========================
def connect_esp() -> serial.Serial:
    """
    Attempt to connect to the ESP device. Retry indefinitely if not present.

    Returns:
        serial.Serial: Opened serial connection
    """
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            logging.info(f'Connected to ESP on {SERIAL_PORT}')
            return ser
        except serial.SerialException:
            logging.warning(f'ESP not found on {SERIAL_PORT}. Retrying in 5s...')
            time.sleep(5)

# =========================
# Main fan control loop
# =========================
def main_loop():
    """
    Main loop for reading temperatures, calculating fan speed,
    sending commands to ESP, and handling reconnections.
    """
    global ema_temp
    ser = connect_esp()

    while True:
        try:
            # Get all temperatures
            all_temps = get_drive_temperatures() + get_system_temperatures()

            if all_temps:
                # Smooth maximum temperature
                max_temp = max(all_temps)
                if ema_temp is None:
                    ema_temp = max_temp
                else:
                    ema_temp = EMA_ALPHA * max_temp + (1 - EMA_ALPHA) * ema_temp

                # Calculate fan speed
                fan_speed = calculate_fan_speed(ema_temp)

                logging.info(f'Max Temp: {max_temp}°C | Smoothed: {int(ema_temp)}°C -> Fan Speed: {fan_speed}%')
                if LOG_DETAIL:
                    logging.debug(f'Individual Temps: {all_temps}')

                # Send fan speed to ESP
                try:
                    ser.write(f'FAN:{fan_speed}\n'.encode())
                except serial.SerialException:
                    logging.warning('Lost ESP connection. Reconnecting...')
                    ser = connect_esp()

                # Read ESP response
                time.sleep(0.1)
                while ser.in_waiting:
                    response = ser.readline().decode(errors='ignore').strip()
                    logging.info(f'ESP: {response}')

            else:
                # No temperature data, default fan to MAX_FAN
                logging.warning(f'No temperature data. Setting fan to {MAX_FAN}%')
                try:
                    ser.write(f'FAN:{MAX_FAN}\n'.encode())
                except serial.SerialException:
                    logging.warning('Lost ESP connection. Reconnecting...')
                    ser = connect_esp()

            # Wait before next loop iteration
            time.sleep(2)

        except KeyboardInterrupt:
            logging.info('Stopping fan controller gracefully')
            ser.close()
            break
        except Exception as e:
            logging.error(f'Runtime error: {e}')
            time.sleep(5)  # Avoid tight loop on error

# =========================
# Script entry point
# =========================
if __name__ == '__main__':
    main_loop()
