"""Drive cycles.

`custom_cycle()` builds a synthetic urban + suburban + highway cycle from
piecewise-linear speed waypoints. It is NOT the official WLTP/WLTC cycle.
To use the official WLTC Class 3b (or any other cycle), download it as a CSV
with columns `time_s,speed_kmh` and load it with `load_cycle_csv()`.
"""
import csv
import numpy as np

# (time_s, speed_kmh) waypoints
_WAYPOINTS = [
    # urban stop-and-go
    (0, 0), (15, 0), (30, 40), (45, 50), (60, 0), (75, 0),
    (95, 45), (115, 30), (130, 0), (145, 0),
    (165, 50), (185, 50), (200, 0), (215, 0),
    # suburban
    (240, 70), (290, 70), (310, 55), (340, 80), (380, 80), (400, 0), (415, 0),
    # highway
    (460, 100), (520, 120), (640, 120), (680, 130), (760, 130), (800, 110),
    (860, 110), (900, 80), (940, 0),
]


def custom_cycle(dt: float = 1.0):
    """Return (t [s], v [m/s]) sampled at `dt`."""
    wp = np.array(_WAYPOINTS, dtype=float)
    t = np.arange(wp[0, 0], wp[-1, 0] + dt, dt)
    v = np.interp(t, wp[:, 0], wp[:, 1]) / 3.6
    return t, v


def load_cycle_csv(path: str):
    """Load a cycle from CSV with header `time_s,speed_kmh`; return (t, v[m/s])."""
    t, v = [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            t.append(float(row["time_s"]))
            v.append(float(row["speed_kmh"]) / 3.6)
    return np.array(t), np.array(v)
