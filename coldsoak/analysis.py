"""Turn run logs (CSV) into the numbers on the project page.

CSV columns: t_s, cell_c, pad_c, ambient_c, v, i_a, heater
"""
import csv
from dataclasses import dataclass


@dataclass
class RunSummary:
    runtime_min: float
    capacity_mah: float
    energy_wh: float
    min_v: float
    max_sag_v: float          # biggest drop between resting and loaded voltage
    mean_cell_c: float
    heater_duty: float
    heater_wh: float


def load(path):
    with open(path) as fh:
        return [{k: float(v) for k, v in r.items()} for r in csv.DictReader(fh)]


def summarise(rows, cutoff_v_per_cell=3.3, cells=4, heater_w=10.0) -> RunSummary:
    cutoff = cutoff_v_per_cell * cells
    mah = wh = heater_s = 0.0
    end_t = rows[-1]["t_s"]
    rest_v = rows[0]["v"]
    sag = 0.0
    for a, b in zip(rows, rows[1:]):
        dt = b["t_s"] - a["t_s"]
        mah += a["i_a"] * dt / 3.6
        wh += a["i_a"] * a["v"] * dt / 3600
        heater_s += dt if a["heater"] else 0
        if a["i_a"] < 0.2:
            rest_v = a["v"]
        else:
            sag = max(sag, rest_v - a["v"])
        if b["v"] <= cutoff:
            end_t = b["t_s"]
            break
    span = end_t - rows[0]["t_s"]
    return RunSummary(span / 60, mah, wh, min(r["v"] for r in rows), sag,
                      sum(r["cell_c"] for r in rows) / len(rows),
                      heater_s / span if span else 0, heater_w * heater_s / 3600)


def compare(summaries: dict[str, RunSummary], baseline: str):
    """Runtime retained vs the warm baseline, e.g. {'+20C': s1, '-20C unheated': s2, '-20C heated': s3}."""
    base = summaries[baseline].runtime_min
    return {k: round(100 * s.runtime_min / base, 1) for k, s in summaries.items()}
