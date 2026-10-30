import csv
import os
import tempfile
import unittest

from coldsoak.analysis import load, summarise
from coldsoak.thermostat import State, Thermostat


class TestThermostat(unittest.TestCase):
    def test_hysteresis_no_chatter(self):
        th = Thermostat()
        self.assertTrue(th.update(0, 5, 0))
        self.assertTrue(th.update(1, 15, 5))     # inside band: stay on
        self.assertFalse(th.update(2, 19, 8))
        self.assertFalse(th.update(3, 15, 8))    # inside band: stay off
        self.assertTrue(th.update(4, 9, 8))

    def test_cell_overtemp_latches(self):
        th = Thermostat()
        self.assertFalse(th.update(0, 5, 41))
        self.assertIs(th.state, State.TRIPPED)
        self.assertFalse(th.update(1, 5, 10))

    def test_ds18b20_reset_value_trips(self):
        self.assertFalse(Thermostat().update(0, 85.0, 10))

    def test_sensor_timeout(self):
        th = Thermostat()
        th.update(0, 5, 5)
        self.assertTrue(th.update(2, None, None))
        self.assertFalse(th.update(10, None, None))


class TestAnalysis(unittest.TestCase):
    def test_summary(self):
        p = os.path.join(tempfile.mkdtemp(), "r.csv")
        with open(p, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["t_s", "cell_c", "pad_c", "ambient_c", "v", "i_a", "heater"])
            for i in range(601):
                w.writerow([i, -10, 12, -20, 16.8 - i * 0.005, 10.0, i % 2])
        s = summarise(load(p))
        self.assertAlmostEqual(s.capacity_mah, 10 * 600 / 3.6, delta=30)
        self.assertAlmostEqual(s.heater_duty, 0.5, delta=0.05)


if __name__ == "__main__":
    unittest.main()
