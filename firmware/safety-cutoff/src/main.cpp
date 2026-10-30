// ESP32 safety cutoff. Build: pio run -e esp32dev -t upload
#include <Arduino.h>
#include "cutoff.h"

constexpr int PIN_NTC = 34;        // ADC1, cell-surface thermistor
constexpr int PIN_HEARTBEAT = 27;  // from Pi GPIO23
constexpr int PIN_RELAY = 26;      // HIGH = heater supply allowed (relay/MOSFET has pull-down)
constexpr int PIN_LED = 2;

cutoff::Cutoff guard;

void setup() {
    pinMode(PIN_RELAY, OUTPUT);
    digitalWrite(PIN_RELAY, LOW);
    pinMode(PIN_HEARTBEAT, INPUT_PULLDOWN);
    pinMode(PIN_LED, OUTPUT);
    analogReadResolution(12);
    Serial.begin(115200);
}

void loop() {
    float cell = cutoff::ntc_celsius(analogRead(PIN_NTC));
    bool ok = guard.update(millis(), cell, digitalRead(PIN_HEARTBEAT));
    digitalWrite(PIN_RELAY, ok ? HIGH : LOW);
    digitalWrite(PIN_LED, ok ? LOW : (millis() / 200) % 2);
    static uint32_t last = 0;
    if (millis() - last > 1000) {
        last = millis();
        Serial.printf("cell=%.2f ok=%d reason=%d\n", cell, ok, int(guard.reason()));
    }
    delay(20);
}
