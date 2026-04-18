import os
import re
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

COILS = ["XP", "XM", "YP", "YM", "ZP", "ZM"]

log_file = os.path.normpath(os.path.join(os.path.dirname(__file__), 'mag_hyst.log'))

if not os.path.exists(log_file):
    print(f"Error: {log_file} not found")
    exit(1)

# ── Parse CSV rows from minicom log (strip control characters) ────────────────
header = None
rows = []
with open(log_file, 'r', errors='replace') as f:
    for line in f:
        line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)   # ANSI escapes
        line = re.sub(r'[^\x20-\x7e,.\-\n]', '', line).strip()
        if not line:
            continue
        parts = line.split(',')
        if header is None:
            if parts[0] == 'coil':
                header = parts
            continue
        if len(parts) != len(header):
            continue
        if parts[0] not in COILS:
            continue
        try:
            row = [parts[0]] + [float(x) for x in parts[1:]]
            rows.append(row)
        except ValueError:
            continue

if not rows:
    print("No valid data rows found.")
    exit(1)

col_idx = {name: i for i, name in enumerate(header)}

# Group rows by coil, sorted by step
by_coil = defaultdict(list)
for row in rows:
    by_coil[row[0]].append(row)
for coil in by_coil:
    by_coil[coil].sort(key=lambda r: r[col_idx['step']])

def col(rows, name):
    return np.array([r[col_idx[name]] for r in rows])

print(f"Loaded {len(rows)} rows across coils: {list(by_coil.keys())}")

out_dir = os.path.dirname(log_file)

# ── One figure per coil ───────────────────────────────────────────────────────
for coil in COILS:
    data = by_coil.get(coil)
    if not data:
        continue

    fig, axes = plt.subplots(3, 1, figsize=(10, 10))
    fig.suptitle(f'Coil {coil} — Hysteresis Sweep', fontsize=14)

    step = col(data, 'step')

    # Magnetometer
    ax = axes[0]
    ax.plot(step, col(data, 'mag_x'), label='mag_x', marker='o', markersize=3)
    ax.plot(step, col(data, 'mag_y'), label='mag_y', marker='s', markersize=3)
    ax.plot(step, col(data, 'mag_z'), label='mag_z', marker='^', markersize=3)
    ax.set_ylabel('Magnetic Field')
    ax.set_title('Magnetometer')
    ax.legend()
    ax.grid(True)

    # Voltages
    ax = axes[1]
    for c in COILS:
        ax.plot(step, col(data, f'voltage_{c.lower()}'), label=f'V_{c}',
                linewidth=2 if c == coil else 0.8,
                linestyle='-' if c == coil else '--')
    ax.set_ylabel('Voltage')
    ax.set_title('Voltages')
    ax.legend(ncol=3, fontsize=8)
    ax.grid(True)

    # Currents
    ax = axes[2]
    for c in COILS:
        ax.plot(step, col(data, f'current_{c.lower()}'), label=f'I_{c}',
                linewidth=2 if c == coil else 0.8,
                linestyle='-' if c == coil else '--')
    ax.set_ylabel('Current')
    ax.set_xlabel('Throttle Step')
    ax.set_title('Currents')
    ax.legend(ncol=3, fontsize=8)
    ax.grid(True)

    plt.tight_layout()
    out_path = os.path.join(out_dir, f'mag_hyst_{coil}.png')
    plt.savefig(out_path, dpi=150)
    print(f"Saved {out_path}")
    plt.close(fig)

# ── Cross-coil comparison: magnetometer response ──────────────────────────────
for mag_ax in ['mag_x', 'mag_y', 'mag_z']:
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharey=True)
    fig.suptitle(f'{mag_ax} response per coil', fontsize=14)
    for ax, coil in zip(axes.flat, COILS):
        data = by_coil.get(coil)
        if data:
            ax.plot(col(data, 'step'), col(data, mag_ax), marker='o', markersize=3)
        ax.set_title(f'Coil {coil}')
        ax.set_xlabel('Throttle Step')
        ax.set_ylabel(mag_ax)
        ax.grid(True)
    plt.tight_layout()
    out_path = os.path.join(out_dir, f'mag_hyst_{mag_ax}_all_coils.png')
    plt.savefig(out_path, dpi=150)
    print(f"Saved {out_path}")
    plt.close(fig)
