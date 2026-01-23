#include <Arduino.h>

#define PWM_PIN 12      // D6
#define TACH_PIN 14     // D5

volatile uint32_t pulseCount = 0;
unsigned long lastRPMReport = 0;
int fanSpeed = 60; // 0–100
int lastRpm = 0;

void IRAM_ATTR countPulse() {
  pulseCount++;
}

void setup() {
  Serial.begin(115200);
  pinMode(PWM_PIN, OUTPUT);
  pinMode(TACH_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(TACH_PIN), countPulse, FALLING);
  analogWriteFreq(25000); // 25kHz PWM
  analogWriteRange(100);  // 0–100 for duty cycle
  analogWrite(PWM_PIN, fanSpeed);
}

void loop() {
  // Handle serial input
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

  // Report RPM every second
  if (millis() - lastRPMReport >= 1000) {
    noInterrupts();
    uint32_t count = pulseCount;
    pulseCount = 0;
    interrupts();
    // 2 pulses per revolution
    uint32_t rpm = (count * 60) / 2;
    Serial.print("RPM:");
    Serial.println(rpm);
    lastRPMReport = millis();
  }
}