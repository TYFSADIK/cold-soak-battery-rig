"""Raspberry Pi sensor drivers: DS18B20 (1-Wire sysfs) and INA228 (I2C).

Enable 1-Wire with `dtoverlay=w1-gpio` and I2C in raspi-config.
"""
import glob
import struct

W1_GLOB = "/sys/bus/w1/devices/28-*/temperature"


def read_ds18b20_all() -> dict[str, float]:
    out = {}
    for path in glob.glob(W1_GLOB):
        sid = path.split("/")[-2]
        try:
            with open(path) as fh:
                out[sid] = int(fh.read().strip()) / 1000.0
        except (OSError, ValueError):
            out[sid] = None
    return out


class INA228:
    """TI INA228 20-bit power monitor. Shunt value and max current set the scaling."""
    REG_CONFIG, REG_ADC_CONFIG, REG_SHUNT_CAL = 0x00, 0x01, 0x02
    REG_VBUS, REG_CURRENT, REG_DIETEMP = 0x05, 0x07, 0x06

    def __init__(self, bus, addr=0x40, r_shunt=0.002, max_current_a=40.0):
        self.bus, self.addr = bus, addr
        self.current_lsb = max_current_a / 2 ** 19
        shunt_cal = int(13107.2e6 * self.current_lsb * r_shunt)
        self._write16(self.REG_SHUNT_CAL, shunt_cal)

    def _write16(self, reg, val):
        self.bus.write_i2c_block_data(self.addr, reg, [(val >> 8) & 0xFF, val & 0xFF])

    def _read24(self, reg):
        b = self.bus.read_i2c_block_data(self.addr, reg, 3)
        return (b[0] << 16) | (b[1] << 8) | b[2]

    def bus_voltage(self) -> float:
        return (self._read24(self.REG_VBUS) >> 4) * 195.3125e-6

    def current(self) -> float:
        raw = self._read24(self.REG_CURRENT) >> 4
        if raw & 0x80000:
            raw -= 1 << 20
        return raw * self.current_lsb
