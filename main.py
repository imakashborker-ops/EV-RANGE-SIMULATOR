"""Command line entry point.

    python main.py                       # built-in custom cycle
    python main.py --cycle wltc.csv      # your own cycle (time_s,speed_kmh)
    python main.py --mass 1000 --cd 0.30 --battery 75 --aux 1500 --regen 0.5
"""
import argparse
import os
from dataclasses import replace

from ev_sim.vehicle import Vehicle
from ev_sim.cycles import custom_cycle, load_cycle_csv
from ev_sim.simulate import simulate, sensitivity
from ev_sim.plots import plot_timeseries, plot_motor_map, plot_sensitivity


def main():
    p = argparse.ArgumentParser(description="Simple longitudinal EV range simulator")
    p.add_argument("--cycle", help="CSV with columns time_s,speed_kmh")
    p.add_argument("--mass", type=float)
    p.add_argument("--cd", type=float)
    p.add_argument("--battery", type=float, help="usable battery capacity [kWh]")
    p.add_argument("--aux", type=float, help="auxiliary power [W]")
    p.add_argument("--regen", type=float, help="regen share of braking energy, 0..1")
    p.add_argument("--out", default="results")
    args = p.parse_args()

    veh = Vehicle()
    overrides = {
        "mass": args.mass, "cd": args.cd, "battery_capacity_kwh": args.battery,
        "aux_power": args.aux, "regen_fraction": args.regen,
    }
    veh = replace(veh, **{k: v for k, v in overrides.items() if v is not None})

    t, v = load_cycle_csv(args.cycle) if args.cycle else custom_cycle()
    res = simulate(veh, t, v)

    os.makedirs(args.out, exist_ok=True)
    plot_timeseries(res, os.path.join(args.out, "timeseries.png"))
    plot_motor_map(res, veh, os.path.join(args.out, "motor_operating_points.png"))
    sens = sensitivity(veh, t, v, delta=0.10)
    plot_sensitivity(sens, 0.10, os.path.join(args.out, "sensitivity.png"))

    traction_kwh = res.energy_kwh + res.regen_kwh
    print(f"Cycle distance:        {res.distance_km:.2f} km")
    print(f"Cycle duration:        {res.t[-1] - res.t[0]:.0f} s")
    print(f"Net battery energy:    {res.energy_kwh:.3f} kWh")
    print(f"Energy regenerated:    {res.regen_kwh:.3f} kWh "
          f"({res.regen_kwh / traction_kwh * 100:.1f}% of gross consumption)")
    print(f"Consumption:           {res.consumption_wh_km:.1f} Wh/km")
    print(f"Estimated range:       {res.range_km:.0f} km "
          f"({veh.battery_capacity_kwh:.0f} kWh usable)")
    print(f"Steps above power cap: {int(res.unmet_power.sum())}")
    print("Sensitivity (-10% / +10%) in consumption [%]:")
    for k, (lo, hi) in sens.items():
        print(f"  {k:<22s} {lo:+6.2f} / {hi:+6.2f}")


if __name__ == "__main__":
    main()
