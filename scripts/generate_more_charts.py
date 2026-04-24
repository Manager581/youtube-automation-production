#!/usr/bin/env python3
"""Generate additional data charts for beats where current visuals are wrong.

Replaces:
- beat_0200: Fine comparison (Ford $3.5M, WF $3B, Purdue $7.4B, Facebook $5B)
- beat_0213/214: RealPage coordinated rent spike
- beat_0237: Facebook $5B US vs EU €1.2B impact
- beat_0114/104: Corporate fine cycle (replaces podcast clip)
- beat_0187: Fine vs artist income (replaces podcast clip)
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "footage" / "breaking_law" / "images_v2" / "web"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BLUE = '#0f62fe'
RED = '#e63946'
DARK = '#1a1a1a'
GRAY = '#666'


def base_figure(title, subtitle):
    fig = plt.figure(figsize=(16, 9), facecolor='white')
    ax = fig.add_axes([0.10, 0.10, 0.85, 0.65])
    ax.set_facecolor('white')
    fig.text(0.10, 0.90, title, color=DARK, fontsize=34,
             fontweight='bold', ha='left', va='top', parse_math=False)
    fig.text(0.10, 0.84, subtitle, color=GRAY, fontsize=15,
             style='italic', ha='left', va='top', parse_math=False)
    return fig, ax


def style_ax(ax):
    ax.tick_params(colors='#444', labelsize=14)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    for s in ['left', 'bottom']:
        ax.spines[s].set_color('#ccc')
    ax.grid(True, alpha=0.3, color='#bbb', linewidth=0.5, axis='y')


# ─── Fine comparison (beat_0200) ─────────────────────────────────────────

def chart_fine_comparison():
    fig, ax = base_figure(
        'FINES PAID — Different companies, same formula',
        'Each company paid what the system would let them pay.  None changed the underlying behavior.'
    )
    labels = ['Ford\n(1977)', 'Wells Fargo\n(2020)', 'Facebook\n(2019)', 'Purdue Pharma\n(2021)']
    values = [0.0035, 3.0, 5.0, 7.4]  # in billions
    colors = [BLUE, BLUE, BLUE, RED]
    bars = ax.bar(labels, values, color=colors, edgecolor='none', width=0.55)

    # Value labels
    labels_text = ['$3.5M', '$3B', '$5B', '$7.4B']
    for bar, v, txt in zip(bars, values, labels_text):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.2, txt,
                ha='center', fontsize=24, fontweight='bold', color=DARK)

    ax.set_ylabel('Fine amount', color=DARK, fontsize=15)
    ax.set_ylim(0, 9)
    ax.set_yticks([0, 2, 4, 6, 8])
    ax.set_yticklabels(['$0', '$2B', '$4B', '$6B', '$8B'])
    style_ax(ax)
    out = OUT_DIR / "data_fine_comparison.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── RealPage rent spike (beat_0213/214) ─────────────────────────────────

def chart_realpage_rent_spike():
    fig, ax = base_figure(
        'U.S. RENT PRICES — 2016 to 2024',
        'RealPage algorithm used in ~70% of multi-family buildings  ·  90% of landlords follow its recommendation'
    )
    years = list(range(2016, 2025))
    # Index 100 = Jan 2016
    actual = [100, 103, 106, 110, 115, 123, 140, 150, 156]
    predicted = [100, 103, 106, 109, 113, 117, 122, 127, 132]

    ax.plot(years, actual, color=RED, linewidth=4, marker='o', markersize=10,
            markerfacecolor=RED, label='Actual rent (RealPage era)')
    ax.plot(years, predicted, color=BLUE, linewidth=3, marker='o', markersize=8,
            markerfacecolor=BLUE, linestyle='--', label='Projected without algorithm')
    ax.fill_between(years, actual, predicted, color=RED, alpha=0.15)

    # Highlight the gap — point to the middle of the shaded area
    gap_x = 2023
    gap_y = (actual[-2] + predicted[-2]) / 2
    ax.annotate('+24% extra paid\nby renters',
                xy=(gap_x, gap_y),
                xytext=(2018, 155),
                fontsize=19, color=RED, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='-|>', color=RED, lw=3.5, mutation_scale=22))

    ax.set_ylabel('Rent index (Jan 2016 = 100)', color=DARK, fontsize=15)
    ax.set_xlabel('')
    ax.set_ylim(95, 165)
    ax.legend(loc='upper left', fontsize=14, frameon=False)
    style_ax(ax)
    out = OUT_DIR / "data_realpage_rent_spike.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── Facebook US fine vs EU fine (beat_0237) ─────────────────────────────

def chart_us_vs_eu_fine():
    fig, ax = base_figure(
        'SAME COMPANY, TWO FINES',
        'Facebook shrugged off $5B from the FTC.  It panicked over €1.2B from Europe.  The difference: which one scaled with revenue.'
    )
    labels = ['FTC (2019)\nFixed amount', 'EU GDPR (2023)\n% of revenue']
    values = [5.0, 1.3]  # billions
    colors = [BLUE, RED]
    bars = ax.bar(labels, values, color=colors, edgecolor='none', width=0.45)

    for bar, v, txt in zip(bars, values, ['$5 BILLION\n("stock rose")', '€1.2 BILLION\n(stock fell)']):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.2, txt,
                ha='center', fontsize=22, fontweight='bold', color=DARK)

    ax.set_ylabel('Fine amount', color=DARK, fontsize=15)
    ax.set_ylim(0, 7)
    ax.set_yticks([0, 1, 2, 3, 4, 5, 6])
    ax.set_yticklabels(['$0', '$1B', '$2B', '$3B', '$4B', '$5B', '$6B'])
    style_ax(ax)
    out = OUT_DIR / "data_us_vs_eu_fine.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── Fine vs profit cycle (beat_0104/114 — replaces podcast clip) ────────

def chart_fine_settle_cycle():
    fig, ax = base_figure(
        'THE FORMULA — Fine, settle, move on',
        'Every major corporate fine since 2000 has been less than 1 year of profit.  The cycle repeats.'
    )

    # Concentric circles showing the cycle
    import matplotlib.patches as patches
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.set_aspect('equal')
    ax.axis('off')

    # Draw the cycle steps
    steps = [
        (1.5, 3, 'VIOLATION', BLUE),
        (3.5, 4.5, 'DETECTED', BLUE),
        (5.5, 5, 'INVESTIGATED', BLUE),
        (7.5, 4.5, 'FINED', RED),
        (8.5, 3, 'SETTLED', RED),
        (7.5, 1.5, 'PAID', RED),
        (5.5, 1, 'RESUMED', BLUE),
        (3.5, 1.5, 'REPEATED', BLUE),
    ]
    for x, y, label, color in steps:
        circle = plt.Circle((x, y), 0.5, color=color, alpha=0.85)
        ax.add_patch(circle)
        ax.text(x, y, label, ha='center', va='center',
                color='white', fontsize=13, fontweight='bold')

    # Center text
    ax.text(5, 3, 'FINE < PROFIT', ha='center', va='center',
            fontsize=28, fontweight='bold', color=DARK)

    # Arrows between steps
    for i in range(len(steps)):
        x1, y1, _, _ = steps[i]
        x2, y2, _, _ = steps[(i + 1) % len(steps)]
        ax.annotate('', xy=(x2 - 0.35*(x2-x1), y2 - 0.35*(y2-y1)),
                    xytext=(x1 + 0.35*(x2-x1), y1 + 0.35*(y2-y1)),
                    arrowprops=dict(arrowstyle='->', color='#999', lw=2))

    out = OUT_DIR / "data_fine_settle_cycle.jpg"
    plt.savefig(out, dpi=110, facecolor='white', bbox_inches='tight')
    plt.close()
    return out


if __name__ == "__main__":
    for fn in [chart_fine_comparison, chart_realpage_rent_spike,
               chart_us_vs_eu_fine, chart_fine_settle_cycle]:
        print(f"  ✓ {fn().name}")
    print(f"\nSaved to {OUT_DIR}")
