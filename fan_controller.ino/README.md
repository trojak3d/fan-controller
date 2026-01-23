# ESP8266 Fan Controller Firmware (`fan_controller.ino`)

This firmware runs on an **ESP8266** (such as a Wemos D1 Mini, NodeMCU, or similar) and provides high‑frequency PWM fan control and tachometer feedback for the TrueNAS Fan Controller project.

It receives simple commands over **USB serial** from the Docker-based fan controller, sets the fan speed via a 25 kHz PWM signal, and reports RPM every second.

---

## 🚀 Features
- 🔧 **25 kHz PWM output** compatible with 4‑pin PC fans
- 📉 **Tachometer pulse measurement** (2 pulses per revolution)
- 🔌 **USB serial interface** for communication with the host
- 📤 **RPM reporting every second**
- 📥 **Command-based fan control** (`FAN:<0–100>`) 
- ⚡ Interrupt-driven tach counting for accuracy 
- ⚙️ Lightweight, reliable, and designed for 24/7 operation

---

## 📡 Serial Protocol

### **Set fan speed**
```
FAN:<speed>
```
Example:
```
FAN:55
```

### **Firmware response**
```
Setting fan speed:55
```

### **RPM output (sent once per second)**
```
RPM:<value>
```
Example:
```
RPM:824
```

---

## ⚙️ Pin Assignments

| Function       | ESP8266 Pin | Notes |
|----------------|-------------|-------|
| PWM output     | **D6 (GPIO12)** | Drives PWM wire at 25 kHz |
| Tachometer     | **D5 (GPIO14)** | Interrupt pin, reads tach pulses |
| Serial USB     | Built‑in UART | 115200 baud |

---

## 🔧 Hardware Wiring

| 4‑pin PWM Fan | ESP8266           |
| ------------- | ----------------- |
| Pin 1: GND    | GND               |
| Pin 2: +12V   | **PSU (not ESP)** |
| Pin 3: Tach   | D5 (GPIO14)       |
| Pin 4: PWM    | D6 (GPIO12)       |


⚠️ **Important:** Do *not* power the fan from the ESP8266. PC fans require **12V**.

---

## 🔨 PWM Configuration
The firmware configures:
- **25 kHz PWM frequency**
- **0–100 duty cycle range**

```cpp
analogWriteFreq(25000);
analogWriteRange(100);
```

This aligns with Intel's official 4‑pin PWM fan specification.

---

## 🧠 Tachometer Measurement
- Tach pin triggers **falling‑edge interrupts**
- Counted pulses accumulate for one second
- RPM formula:
```
RPM = (pulseCount * 60) / 2
```
Most 4‑pin fans output **2 pulses per revolution**, matching this calculation.

---

## 🔌 Serial Configuration
```
115200 baud
8 data bits
No parity
1 stop bit
```

Fully compatible with Linux, macOS, Windows COM ports, and the Docker Python controller.

---

## 📝 Firmware Source Highlights

### Handling incoming commands
```cpp
if (Serial.available()) {
  String cmd = Serial.readStringUntil('\n');
  if (cmd.startsWith("FAN:")) {
    int val = cmd.substring(4).toInt();
    fanSpeed = constrain(val, 0, 100);
    analogWrite(PWM_PIN, fanSpeed);
    Serial.print("Setting fan speed:");
    Serial.println(fanSpeed);
  }
}
```

### Tach pulse interrupt
```cpp
void IRAM_ATTR countPulse() {
  pulseCount++;
}
```

### RPM reporting
```cpp
uint32_t rpm = (count * 60) / 2;
Serial.print("RPM:");
Serial.println(rpm);
```

---

## ▶️ Flashing Instructions

Use Arduino IDE, PlatformIO, or ESPTool.

### Arduino IDE settings:
- **Board:** NodeMCU 1.0 (ESP‑12E Module)
- **Flash Size:** Default
- **Upload Speed:** 921600 or 115200
- **Port:** Your ESP8266 USB serial port

Upload the firmware normally.

---

## 🧪 Manual Testing

To test without the Docker controller:

```bash
screen /dev/ttyUSB0 115200
```

Send:
```
FAN:40
```
Expected response:
```
Setting fan speed:40
RPM:815
RPM:802
...
```

---

## 📜 License
MIT License.
