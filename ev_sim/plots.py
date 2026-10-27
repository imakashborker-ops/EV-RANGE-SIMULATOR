"""Plots for the EV range simulator (matplotlib, static PNGs)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "sans-serif", "font.size": 10,
    "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": AXIS, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True,
})


def plot_timeseries(res, path, title="EV simulation over drive cycle"):
    fig, axes = plt.subplots(3, 1, figsize=(10, 7.5), sharex=True)
    ax = axes[0]
    ax.plot(res.t, res.v * 3.6, color=BLUE, lw=1.6)
    ax.set_ylabel("Speed [km/h]")
    ax.set_title("Vehicle speed", loc="left", color=INK, fontsize=11)

    ax = axes[1]
    ax.plot(res.t, res.p_batt / 1e3, color=ORANGE, lw=1.2)
    ax.axhline(0, color=AXIS, lw=0.8)
    ax.set_ylabel("Battery power [kW]")
    ax.set_title("Battery power (negative = regenerative braking)", loc="left",
                 color=INK, fontsize=11)

    ax = axes[2]
    ax.plot(res.t, res.soc * 100, color=AQUA, lw=1.8)
    ax.set_ylabel("SOC [%]")
    ax.set_xlabel("Time [s]")
    ax.set_title("State of charge", loc="left", color=INK, fontsize=11)

    fig.suptitle(title, x=0.01, ha="left", fontsize=13, color=INK, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_motor_map(res, veh, path):
    m = (res.motor_speed > 0.1) & (np.abs(res.motor_torque) > 0.5)
    rpm = res.motor_speed[m] * 60 / (2 * np.pi)
    tq = res.motor_torque[m]
    eff = res.motor_eff[m] * 100
    fig, ax = plt.subplots(figsize=(8, 5))
    sc = ax.scatter(rpm, tq, c=eff, cmap="Blues", vmin=80, vmax=100, s=18,
                    edgecolors="#2a78d6", linewidths=0.3, zorder=3)
    # torque limits: constant-torque region + constant-power region
    w = np.linspace(20, res.motor_speed.max() * 1.1, 300)
    r = w * 60 / (2 * np.pi)
    t_drive = np.minimum(veh.max_motor_torque, veh.max_motor_power / w)
    t_regen = -np.minimum(veh.max_motor_torque, veh.max_regen_power / w)
    ax.plot(r, t_drive, color=INK2, lw=1.2, ls="--", zorder=2)
    ax.plot(r, t_regen, color=INK2, lw=1.2, ls="--", zorder=2)
    ax.text(r[-1], t_drive[-1] + 15, "motor limit", color=INK2, ha="right",
            va="bottom", fontsize=9)
    ax.axhline(0, color=AXIS, lw=0.8)
    ax.set_xlabel("Motor speed [rpm]")
    ax.set_ylabel("Motor torque [Nm]")
    ax.set_title("Motor operating points (colour = efficiency)", loc="left",
                 color=INK, fontsize=12, fontweight="bold")
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label("Efficiency [%]", color=INK2)
    cb.outline.set_edgecolor(AXIS)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_sensitivity(sens, delta, path):
    labels = list(sens.keys())
    lo = [sens[k][0] for k in labels]
    hi = [sens[k][1] for k in labels]
    order = np.argsort([max(abs(a), abs(b)) for a, b in zip(lo, hi)])
    labels = [labels[i] for i in order]
    lo = [lo[i] for i in order]
    hi = [hi[i] for i in order]
    y = np.arange(len(labels))
    h = 0.36
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(y + h / 2, lo, h, color=BLUE, label=f"-{delta:.0%}")
    ax.barh(y - h / 2, hi, h, color=ORANGE, label=f"+{delta:.0%}")
    ax.axvline(0, color=AXIS, lw=0.9)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=INK2)
    ax.set_xlabel("Change in energy consumption [%]")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"Sensitivity of consumption to a ±{delta:.0%} parameter change",
                 loc="left", color=INK, fontsize=12, fontweight="bold")
    ax.legend(frameon=False, title="Parameter change", title_fontsize=9,
              loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
