// Independent hardware safety cutoff, portable C++17 (runs on ESP32 and on the host for tests).
// The Pi's heater control is not trusted. This board breaks the heater supply when:
//   - the cell thermistor exceeds CELL_MAX_C,
//   - the Pi heartbeat stops toggling for HEARTBEAT_TIMEOUT_MS,
//   - the thermistor reading is implausible (open or short circuit).
// Once tripped it stays latched until a physical reset.
#pragma once
#include <cstdint>

namespace cutoff {

struct Config {
    float cell_max_c = 42.0f;
    float plausible_min_c = -55.0f;
    float plausible_max_c = 100.0f;
    uint32_t heartbeat_timeout_ms = 3000;
};

enum class Reason : uint8_t { None, OverTemp, SensorFault, HeartbeatLost };

class Cutoff {
public:
    explicit Cutoff(Config c = {}) : cfg_(c) {}

    // Call every loop. Returns true if the relay may stay closed (power allowed).
    bool update(uint32_t now_ms, float cell_c, bool heartbeat_level) {
        if (reason_ != Reason::None) return false;
        if (!started_) { started_ = true; last_edge_ms_ = now_ms; last_level_ = heartbeat_level; }
        if (heartbeat_level != last_level_) { last_level_ = heartbeat_level; last_edge_ms_ = now_ms; }
        if (cell_c < cfg_.plausible_min_c || cell_c > cfg_.plausible_max_c) return trip(Reason::SensorFault);
        if (cell_c >= cfg_.cell_max_c) return trip(Reason::OverTemp);
        if (now_ms - last_edge_ms_ > cfg_.heartbeat_timeout_ms) return trip(Reason::HeartbeatLost);
        return true;
    }

    Reason reason() const { return reason_; }

private:
    bool trip(Reason r) { reason_ = r; return false; }
    Config cfg_;
    Reason reason_ = Reason::None;
    bool started_ = false, last_level_ = false;
    uint32_t last_edge_ms_ = 0;
};

// NTC thermistor (10k, B=3950) in a divider with a fixed resistor to 3.3 V.
inline float ntc_celsius(uint16_t adc, uint16_t adc_max = 4095, float r_fixed = 10000.0f,
                         float r0 = 10000.0f, float beta = 3950.0f) {
    if (adc == 0 || adc >= adc_max) return -999.0f;   // open/short -> implausible
    float r = r_fixed * adc / float(adc_max - adc);
    float inv_t = 1.0f / 298.15f + (1.0f / beta) * __builtin_logf(r / r0);
    return 1.0f / inv_t - 273.15f;
}

}  // namespace cutoff
