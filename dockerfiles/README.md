# Fan Controller — Docker Image

[![GitHub Repo](https://img.shields.io/badge/GitHub-trojak3d/fan--controller-blue?logo=github)](https://github.com/trojak3d/fan-controller)  
[![Docker Hub](https://img.shields.io/badge/DockerHub-trojak3d%2Ffan--controller-blue?logo=docker)](https://hub.docker.com/repository/docker/trojak3d/fan-controller)


[⬅ Back to main README](../README.md)  

A lightweight Python service that monitors temperatures on a TrueNAS host and controls a PWM fan via an ESP8266 connected over USB serial. The controller is designed for systems without a motherboard fan header, providing a configurable fan curve, temperature smoothing to prevent oscillation, and RPM feedback logging for visibility.

---

## What it does

### 1) Reads temperature inputs (non-invasive)
Two sources are used to build a “best available” temperature picture:

- **TrueNAS cached disk temperatures** via the `/api/v2.0/disk/temperatures` endpoint  
  This uses cached values and is intended to avoid waking disks from standby.
- **System sensor temperatures** via `lm-sensors` (`sensors` output)

The controller combines all readings and uses the **maximum** value as the control input.

---

### 2) Stabilises readings with smoothing (EMA)
Instead of reacting instantly to every spike, the controller applies **exponential moving average (EMA)** smoothing to the maximum temperature. This reduces “fan hunting” (rapid up/down speed changes) and makes the output feel more stable in real-world workloads.

---

### 3) Computes fan speed using a simple, configurable fan curve
A linear fan curve maps temperature to PWM duty:

- At or below `MIN_TEMP` → `MIN_FAN`
- At or above `MAX_TEMP` → `MAX_FAN`
- Between the two → interpolated speed

All thresholds are controlled via environment variables so behaviour can be tuned for your enclosure, fan, and noise tolerance.

---

### 4) Sends commands to the ESP8266 over USB serial
The controller writes a simple command protocol to the ESP8266:

```text
FAN:<speed>
```

Example:

```text
FAN:55
```

The ESP8266 firmware applies a **25 kHz PWM signal** (ideal for 4‑pin PWM fans) and reports back status such as the currently set speed and measured RPM.

---

### 5) Logs RPM feedback (useful for validation and troubleshooting)
The ESP8266 periodically reports:

```text
RPM:<value>
```

This makes it easy to confirm the fan is physically spinning, see whether PWM changes are taking effect, and catch wiring issues early (e.g., missing tach line, wrong pin mapping).

---

### 6) Provides a Docker healthcheck based on serial responsiveness
A dedicated healthcheck script attempts to open the serial device and read output. If the ESP is unplugged, stops responding, or the serial mapping breaks, Docker marks the container as unhealthy. This pairs well with restart policies or orchestration tooling.

---

## Image contents (summary)

The image is built from a slim Python base and includes:

- Python runtime for the control loop
- `pyserial` for USB serial communication
- common system temperature tooling (`lm-sensors`, plus supporting utilities)
- the controller and healthcheck scripts placed under `/app`

The container runs `fan_control.py` by default.

---

## Environment variables

Required:

- `TRUENAS_HOST` — base URL (commonly `http://localhost` on TrueNAS when using host networking)
- `TRUENAS_API_KEY` — API key used to query cached disk temperatures

Fan curve / behaviour:

- `MIN_TEMP` / `MAX_TEMP` — temperature range used by the curve
- `MIN_FAN` / `MAX_FAN` — PWM bounds (0–100)
- `LOG_DETAIL` — `true` enables verbose temperature logging
- `SERIAL_PORT` — serial device path (default `/dev/ttyESP`)
- `BAUD_RATE` — serial speed (default `115200`)

---

## ⚠️ Security warning — do NOT publish your TrueNAS API key

This service requires a TrueNAS API key to read cached disk temperatures.  
**Never commit your real API key to GitHub or include it in any public files.**

Use placeholders in examples:

```env
TRUENAS_API_KEY=your_api_key_here
```

If you accidentally expose a key, revoke it immediately in TrueNAS and generate a new one.

---

## Sample docker-compose (production-style, using Docker Hub image)

```yaml
version: '3.8'

services:
  fan-controller:
    image: trojak3d/fan-controller:latest
    container_name: fan-controller
    restart: unless-stopped
    privileged: true
    network_mode: host
    volumes:
      - /dev/ttyESP:/dev/ttyESP
    environment:
      MIN_TEMP: 30
      MAX_TEMP: 70
      MIN_FAN: 20
      MAX_FAN: 80
      BAUD_RATE: 115200
      LOG_DETAIL: "true"
      SERIAL_PORT: /dev/ttyESP
      TRUENAS_HOST: http://localhost
      TRUENAS_API_KEY: "your_api_key_here"
    healthcheck:
      test: ["CMD", "python", "healthcheck.py"]
      interval: 30s
      timeout: 5s
      retries: 3
```

Notes:
- `privileged: true` is used to ensure serial device access is permitted.
- `/dev/ttyESP` should be a stable symlink (commonly provided by a udev rule) so USB enumeration order doesn’t break the setup.

---

## Local build (for development)

```bash
docker build -t fan-controller -f dockerfile .
```

---

## License
MIT License.
