# 🌡️ ESP8266 USB Fan Controller for TrueNAS

[![GitHub Repo](https://img.shields.io/badge/GitHub-trojak3d/fan--controller-blue?logo=github)](https://github.com/trojak3d/fan-controller)  
[![GHCR](https://img.shields.io/badge/GHCR-ghcr.io%2Ftrojak3d%2Ffan--controller-blue?logo=github)](https://ghcr.io/trojak3d/fan-controller)

A modular hardware + software system that adds **PWM fan control** to TrueNAS servers that *don’t have motherboard fan headers*. The system uses an **ESP8266 connected via USB**, controlled by a **Dockerized Python service** that reads temperatures from TrueNAS and the host system, computes a smoothed fan curve, and sends PWM commands to the fan.

---

# 🚀 Features

### **Core functionality**
- 🔧 Full 4‑pin PWM fan control (25 kHz PWM)
- 🔄 Temperature inputs:
  - TrueNAS cached disk temperatures (does *not* wake disks)
  - Host system temperatures via `lm-sensors`
- 📈 Configurable linear fan curve with min/max thresholds
- 🧮 EMA temperature smoothing to prevent rapid oscillation
- 🔁 Auto‑recovery if ESP disconnects or reboots
- 📉 RPM feedback logging from fan tach pin
- 🩺 Docker healthcheck for serial communication reliability
- 🔗 Predictable USB device mapping (`/dev/ttyESP`) via udev

### **Modular architecture**
- ESP8266 firmware for PWM + tachometer
- Python fan controller running in Docker
- TrueNAS init scripts ensuring persistent device naming
- docker-compose stack for one‑command deployment
- Clear separation of responsibilities & easy troubleshooting

---

# 🧩 System Architecture Overview

```
+------------------------------+
|        TrueNAS Host          |
|------------------------------|
| Docker Container             |
|  - fan_control.py            |
|  - healthcheck.py            |
|                              |
| Reads:                       |
|  • Disk temps (API)          |
|  • System temps (sensors)    |
|                              |
| Computes fan speed           |
| Sends FAN:{x} commands       |
| Reads RPM feedback           |
+--------------+---------------+
               |
               | USB Serial (/dev/ttyESP)
               |
+--------------v---------------+
|          ESP8266             |
|------------------------------|
| 25kHz PWM → Fan PWM pin      |
| Tach read ← Fan tach pin     |
| Parses FAN:{x} commands      |
| Reports RPM periodically     |
+------------------------------+
```

---

# 📁 Repository Structure

```
/
├── dockerfiles/                # Docker image + controller implementation
│   ├── dockerfile
│   ├── fan_control.py
│   └── healthcheck.py
│
├── fan_controller.ino/         # ESP8266 firmware
│   └── fan_controller.ino.ino
│
├── docker-compose.yml          # Deployment configuration
├── stack.env                   # User-configurable environment variables
│
└── truenas_scripts/               # TrueNAS init script + udev rule
    ├── ttyESP.sh
    └── 99-esp-fan.rules
```

### More detailed documentation:
- 📦 **[Docker Image Documentation](dockerfiles/README.md)**
- 📦 **[ESP8266 Fan Controller](fan_controller.ino/README.md)**
- 🔌 **ESP8266 Firmware** → `fan_controller.ino/`
- 🧵 **TrueNAS Init Scripts** → `truenas_init/`

---

# ⚠️ Security Warning — Do NOT Publish Your TrueNAS API Key

This system requires a TrueNAS API key to read cached disk temperatures.  
**Never commit your real API key to GitHub or share it publicly.**

Always use placeholder values:

```env
TRUENAS_API_KEY=your_api_key_here
```

If a real key becomes public, revoke it immediately in TrueNAS.

---

# 🛠️ Installation & Setup

## **1. Flash the ESP8266 Firmware**
Upload `fan_controller.ino` using the Arduino IDE or PlatformIO.

Fan wiring:
```
Fan PWM  → D6 (GPIO12)
Fan Tach → D5 (GPIO14)
Fan GND  → GND
Fan +12V → PSU (normal fan power)
```

---

## **2. Enable Stable `/dev/ttyESP` on TrueNAS**
Copy:
- `99-esp-fan.rules` → your scripts dataset
- `ttyESP.sh` → your scripts dataset

> `99-esp-fan.rules` are specific to my device, you might have to tweak accordingly

**TODO:** *Add instructions for setting up the rules*

Then configure:
**System → Init/Shutdown Scripts**
- Type: Script
- When: Post Init
- Path: `/mnt/<pool>/scripts/ttyESP.sh`

This ensures the ESP is always available at a predictable serial path.

---

## **3. Run the container**
## 🧩 Full docker-compose example
```yaml
version: '3.8'
services:
  fan-controller:
    image: ghcr.io/trojak3d/fan-controller:latest
    container_name: fan-controller
    restart: unless-stopped
    working_dir: /app
    command: python -u fan_control.py
    network_mode: host
    privileged: true
    volumes:
      - ${SERIAL_PORT}:${SERIAL_PORT}
    environment:
      - MIN_TEMP=${MIN_TEMP}
      - MAX_TEMP=${MAX_TEMP}
      - MIN_FAN=${MIN_FAN}
      - MAX_FAN=${MAX_FAN}
      - BAUD_RATE=${BAUD_RATE}
      - LOG_DETAIL=${LOG_DETAIL}
      - SERIAL_PORT=${SERIAL_PORT}
      - TRUENAS_HOST=http://localhost
      - TRUENAS_API_KEY=${TRUENAS_API_KEY}
    labels:
      com.example.stack: "fan-controller"
      com.example.service: "fan-controller"
      com.fan-controller.description: "ESP8266 fan controller with RPM feedback"
    healthcheck:
      test: ["CMD", "python", "healthcheck.py"]
      interval: 30s
      timeout: 5s
      retries: 3
```

## 📄 stack.env Example
```
MIN_TEMP=30
MAX_TEMP=70
MIN_FAN=20
MAX_FAN=80
BAUD_RATE=115200
LOG_DETAIL=true
SERIAL_PORT=/dev/ttyESP
TRUENAS_API_KEY=your_api_key
```
---

# 📊 Monitoring the System

The simplest and most effective way to verify things are working is to **watch the container logs**:

```bash
docker logs -f fan-controller
```

You should see:
- Temperature readings
- Smoothed temperature values
- Computed fan speed percentages
- ESP responses, e.g.:
  ```
  Setting fan speed:55
  RPM:820
  ```
- Reconnection attempts if the ESP is unplugged
- Healthcheck status messages

If the container stops printing RPMs, you may have:
- Tach wire disconnected
- ESP rebooting
- USB cable issue

---

# 📜 License
MIT License.
