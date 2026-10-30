# Cold-Soak Characterization Rig

Private research repo. A heated, instrumented drone battery bay, tested in a lab freezer and in real Canadian winter. Runtime, voltage sag, and failure modes are logged against temperature.

Full write-up: [`docs/project-page.md`](docs/project-page.md)

## Architecture

```
 DS18B20 x6 ─┐                      ┌─> MOSFET ─> Kapton heater
 INA228 x2 ──┼─> Raspberry Pi (Python): thermostat + CSV logger
             │        │ heartbeat (GPIO23)
             │        v
 NTC on cell ───> ESP32 (C++): independent latched cutoff ──> relay in heater supply
```

There are two layers of protection. The Pi software can crash. The ESP32 cutoff is separate hardware, latches when it trips, and cuts the heater if the Pi stops sending its heartbeat.

## What's here

| Path | Language | Purpose |
|---|---|---|
| `coldsoak/thermostat.py` | Python | Hysteresis control on the pad sensor, latched cell over-temp, DS18B20 fault values (85 / -127), sensor timeout |
| `coldsoak/sensors.py` | Python | DS18B20 1-Wire and INA228 I²C drivers |
| `coldsoak/rig.py` | Python | Pi main loop: sensors, thermostat, MOSFET, heartbeat, CSV |
| `coldsoak/analysis.py` | Python | Runtime, mAh, Wh, voltage sag, heater duty, and runtime retained vs the warm baseline |
| `firmware/safety-cutoff/` | C++17 / PlatformIO | ESP32 independent cutoff (`cutoff.h` is portable and host-tested) |

## Quickstart

```bash
python -m unittest -v
cd firmware/safety-cutoff && c++ -std=c++17 -Iinclude test/test_cutoff.cpp -o /tmp/t && /tmp/t
pio run -e esp32dev -t upload      # flash the ESP32
```

## Next steps
- [ ] Run plan: +20 °C baseline, then -10/-20/-30 °C unheated vs heated, three runs each
- [ ] Feed the measured curve into `arctic-isr-drone/isr/cold_ops.py`
- [ ] Add an internal-resistance estimate (ΔV/ΔI at load steps) per temperature
- [ ] Fire-safe enclosure (LiPo bag or ammo can) for every cold test
