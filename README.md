# ESP8266 USB Fan Controller for TrueNAS
[![GitHub Repo](https://img.shields.io/badge/GitHub-trojak3d/fan--controller-blue?logo=github)](https://github.com/trojak3d/fan-controller)
[![Docker Hub](https://img.shields.io/badge/DockerHub-trojak3d%2Ffan--controller-blue?logo=docker)](https://hub.docker.com/repository/docker/trojak3d/fan-controller)

A compact hardware + software solution for adding PWM fan control to systems (such as TrueNAS servers) that **lack motherboard fan headers**.
An ESP8266 controls a 25 kHz PWM fan while a Docker container monitors temperatures and sends serial fan‑speed commands.

## 🚀 Features
- USB‑connected **ESP8266-based PWM fan controller**
- Reads temperatures from:
  - TrueNAS cached disk temperature API
  - `lm-sensors` system sensors
- Linear, configurable fan curve
- RPM feedback from the fan
- Automatic EMA smoothing
- Stable serial device mapping via `/dev/ttyESP`
- Docker healthcheck validation

## 🧩 Sample docker-compose (using Docker Hub image)
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

## 📁 Repository Structure
```
/
├── dockerfiles/
│   ├── dockerfile
│   ├── fan_control.py
│   └── healthcheck.py
├── fan_controller.ino/
│   └── fan_controller.ino.ino
├── docker-compose.yml
├── stack.env
└── truenas_init/
    ├── ttyESP.sh
    └── 99-esp-fan.rules
```

➡️ **[Dockerfiles README](dockerfiles/README.md)**
➡️ **[Compose README](compose/README.md)**

## 📜 License
MIT License.
