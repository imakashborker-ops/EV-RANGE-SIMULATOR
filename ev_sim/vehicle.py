"""Vehicle and powertrain parameters for a longitudinal EV model."""
from dataclasses import dataclass

G = 9.81          # m/s^2
RHO_AIR = 1.2     # kg/m^3


@dataclass
class Vehicle:
    # Body / chassis
    mass: float = 2500.0          # kg, curb mass + driver
    cd: float = 0.28              # drag coefficient
    frontal_area: float = 2.2     # m^2
    c_rr: float = 0.009           # rolling resistance coefficient
    wheel_radius: float = 0.32    # m
    rotating_mass_factor: float = 1.05  # accounts for rotational inertia

    # Powertrain
    gear_ratio: float = 9.0       # single-speed reduction
    driveline_eff: float = 0.97   # gearbox + driveshaft efficiency
    max_motor_power: float = 150e3    # W
    max_motor_torque: float = 310.0   # Nm
    max_regen_power: float = 60e3     # W
    regen_fraction: float = 0.6       # share of braking energy attempted via regen
    regen_min_speed: float = 5 / 3.6  # m/s, no regen below this

    # Motor/inverter efficiency (simple parametric map, see motor_efficiency)
    eta_peak: float = 0.95

    # Battery
    battery_capacity_kwh: float = 60.0   # usable
    battery_eff: float = 0.97            # round-trip share per direction (I^2R etc.)
    aux_power: float = 500.0             # W constant (HVAC, electronics)

    def motor_efficiency(self, torque: float, speed_rads: float) -> float:
        """Simple parametric motor+inverter efficiency.

        Efficiency drops at low torque (fixed losses dominate) and at high
        torque/speed (copper and iron losses). Not a measured map; replace with
        a lookup table from real data for higher fidelity.
        """
        t_rel = min(abs(torque) / self.max_motor_torque, 1.0)
        w_rel = min(abs(speed_rads) / 1200.0, 1.0)   # ~11,500 rpm base scale
        # Low-load penalty: fixed losses dominate below ~30% of max torque
        low_load = 1.0 - 0.12 * (1.0 - min(t_rel / 0.3, 1.0)) ** 2
        # High-load copper-loss penalty
        copper = 1.0 - 0.08 * t_rel ** 2
        # High-speed iron-loss penalty
        iron = 1.0 - 0.05 * w_rel ** 2
        return max(0.5, self.eta_peak * low_load * copper * iron)
