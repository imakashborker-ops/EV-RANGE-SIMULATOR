"""Longitudinal EV simulation (quasi-static, backward-facing).

For each time step the speed profile is prescribed. The tractive force needed at
the wheels is computed, pushed backwards through driveline, motor and battery to
get battery power, and integrated to energy / SOC.
"""
from dataclasses import dataclass, replace
import numpy as np

from .vehicle import Vehicle, G, RHO_AIR


@dataclass
class Result:
    t: np.ndarray
    v: np.ndarray             # m/s
    a: np.ndarray             # m/s^2
    p_wheel: np.ndarray       # W, + traction / - braking
    p_batt: np.ndarray        # W, + discharge / - charge
    soc: np.ndarray           # 0..1
    motor_torque: np.ndarray  # Nm
    motor_speed: np.ndarray   # rad/s
    motor_eff: np.ndarray     # -
    unmet_power: np.ndarray   # bool, requested power above motor limit
    distance_km: float
    energy_kwh: float         # net battery energy used over the cycle
    regen_kwh: float          # energy returned to battery
    consumption_wh_km: float
    range_km: float


def simulate(veh: Vehicle, t: np.ndarray, v: np.ndarray, grade: float = 0.0,
             soc0: float = 1.0) -> Result:
    dt = np.gradient(t)
    a = np.gradient(v, t)

    # Resistance forces at the wheel
    f_aero = 0.5 * RHO_AIR * veh.cd * veh.frontal_area * v ** 2
    f_roll = np.where(v > 0.01, veh.c_rr * veh.mass * G * np.cos(np.arctan(grade)), 0.0)
    f_grade = veh.mass * G * np.sin(np.arctan(grade))
    f_inertia = veh.mass * veh.rotating_mass_factor * a
    f_total = f_aero + f_roll + f_grade + f_inertia
    p_wheel = f_total * v

    n = len(t)
    p_batt = np.zeros(n)
    torque = np.zeros(n)
    w_motor = v / veh.wheel_radius * veh.gear_ratio
    eta_m = np.zeros(n)
    unmet = np.zeros(n, dtype=bool)

    for i in range(n):
        pw = p_wheel[i]
        w = w_motor[i]
        if pw >= 0:  # traction
            p_shaft = pw / veh.driveline_eff
            if p_shaft > veh.max_motor_power:
                p_shaft = veh.max_motor_power
                unmet[i] = True
            if w > 0.1:
                tq = min(p_shaft / w, veh.max_motor_torque)
                p_shaft = tq * w
            else:
                tq = 0.0
                p_shaft = 0.0
            eta = veh.motor_efficiency(tq, w) if p_shaft > 0 else 1.0
            p_elec = p_shaft / eta
            p_batt[i] = p_elec / veh.battery_eff + veh.aux_power
            torque[i], eta_m[i] = tq, eta
        else:  # braking, part of it recuperated
            if v[i] >= veh.regen_min_speed and w > 0.1:
                p_reg_wheel = min(-pw * veh.regen_fraction, veh.max_regen_power)
                p_shaft = p_reg_wheel * veh.driveline_eff
                tq = min(p_shaft / w, veh.max_motor_torque)
                p_shaft = tq * w
                eta = veh.motor_efficiency(tq, w)
                p_elec = p_shaft * eta * veh.battery_eff
                p_batt[i] = -p_elec + veh.aux_power
                torque[i], eta_m[i] = -tq, eta
            else:
                p_batt[i] = veh.aux_power
                eta_m[i] = 1.0

    e_step_kwh = p_batt * dt / 3.6e6
    energy_kwh = float(e_step_kwh.sum())
    # energy flowing back into the battery (traction/regen only, aux excluded)
    regen_kwh = float(-np.minimum(e_step_kwh - veh.aux_power * dt / 3.6e6, 0).sum())
    soc = soc0 - np.cumsum(e_step_kwh) / veh.battery_capacity_kwh

    distance_km = float(np.sum(v * dt) / 1000)
    cons = energy_kwh * 1000 / distance_km
    return Result(t, v, a, p_wheel, p_batt, soc, torque, w_motor, eta_m, unmet,
                  distance_km, energy_kwh, regen_kwh, cons,
                  veh.battery_capacity_kwh * 1000 / cons)


def sensitivity(base: Vehicle, t, v, delta: float = 0.10):
    """Change in consumption (%) for +/- delta on key parameters."""
    base_c = simulate(base, t, v).consumption_wh_km
    params = {
        "Mass": "mass",
        "Drag coeff. Cd": "cd",
        "Rolling resist. Crr": "c_rr",
        "Aux. power": "aux_power",
        "Driveline losses": "driveline_eff",  # perturb losses (1 - eff), not eff
    }
    out = {}
    for label, attr in params.items():
        vals = []
        for sign in (-1, +1):
            if attr == "driveline_eff":
                x = 1 - (1 - getattr(base, attr)) * (1 + sign * delta)
            else:
                x = getattr(base, attr) * (1 + sign * delta)
            vals.append((simulate(replace(base, **{attr: x}), t, v).consumption_wh_km
                         / base_c - 1) * 100)
        out[label] = tuple(vals)  # (-delta, +delta)
    return out
