"""Main loop on the Pi: read sensors, run thermostat, drive MOSFET, log CSV, heartbeat the ESP32 cutoff.

    python -m coldsoak.rig --pad 28-xxxx --cell 28-yyyy --ambient 28-zzzz --out data/run01.csv
"""
import argparse
import csv
import time

from .thermostat import Thermostat

# Pin map matches the build page wiring table (docs/project-page.md, HARDWARE.md)
HEATER_GPIO = 17      # pin 11 -> 100 R -> MOSFET gate, 10 k pull-down (heater fails OFF at boot)
HEARTBEAT_GPIO = 23   # pin 16 -> ESP32 safety cutoff GPIO27; toggled every loop, ESP32 cuts power if it stops
INA_PACK_ADDR = 0x40  # INA228 #1, discharge path (A0/A1 = GND)
INA_HEATER_ADDR = 0x41  # INA228 #2, heater branch (A0 = VS+)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pad", required=True)
    ap.add_argument("--cell", required=True)
    ap.add_argument("--ambient", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--period", type=float, default=1.0)
    a = ap.parse_args()

    from gpiozero import DigitalOutputDevice   # Pi only
    from smbus2 import SMBus
    from .sensors import INA228, read_ds18b20_all

    heater = DigitalOutputDevice(HEATER_GPIO, initial_value=False)
    beat = DigitalOutputDevice(HEARTBEAT_GPIO)
    bus = SMBus(1)
    ina = INA228(bus, INA_PACK_ADDR)
    ina_heater = INA228(bus, INA_HEATER_ADDR, max_current_a=10.0)
    th = Thermostat()
    t0 = time.monotonic()
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["t_s", "cell_c", "pad_c", "ambient_c", "v", "i_a", "heater", "heater_v", "heater_a"])
        try:
            while True:
                now = time.monotonic() - t0
                temps = read_ds18b20_all()
                on = th.update(now, temps.get(a.pad), temps.get(a.cell))
                heater.value = on
                beat.toggle()
                w.writerow([round(now, 2), temps.get(a.cell), temps.get(a.pad), temps.get(a.ambient),
                            round(ina.bus_voltage(), 4), round(ina.current(), 4), int(on),
                            round(ina_heater.bus_voltage(), 4), round(ina_heater.current(), 4)])
                fh.flush()
                if th.trip_reason:
                    print("TRIPPED:", th.trip_reason)
                time.sleep(a.period)
        finally:
            heater.off()


if __name__ == "__main__":
    main()
