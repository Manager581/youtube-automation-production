#!/usr/bin/env python3
"""Generate clean real-data visuals for key narrative beats.

Matching style to facebook_stock_july_2019_annotated.jpg:
- White background, clean serif-like headers
- Blue data (#0f62fe), red annotations (#e63946)
- Title + italic subtitle, no overlap
- Red circles/arrows for emphasis
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
from datetime import datetime
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "footage" / "breaking_law" / "images_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BLUE = '#0f62fe'
RED = '#e63946'
DARK = '#1a1a1a'
GRAY = '#666'


def base_figure(title, subtitle):
    """Create a figure with the standard title/subtitle header.

    Disables mathtext parsing so $ and other special chars render literally.
    """
    fig = plt.figure(figsize=(16, 9), facecolor='white')
    ax = fig.add_axes([0.10, 0.10, 0.85, 0.65])
    ax.set_facecolor('white')
    # usetex=False + parse_math=False ensures $ renders as a dollar sign
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


# ─── 1. Zuckerberg $1.1B gain ─────────────────────────────────────────────

def chart_zuckerberg_gain():
    fig, ax = base_figure(
        'MARK ZUCKERBERG — Net worth, July 2019',
        'Personal wealth gained $1.1 BILLION the day the FTC fine leaked  ·  '
        'More than the fine cost Facebook after tax effects'
    )
    days = ['Jul 11', 'Jul 12\n(fine leaks)', 'Jul 13', 'Jul 14']
    values = [72.4, 73.5, 73.5, 73.5]
    colors = ['#8fa0ff', RED, '#8fa0ff', '#8fa0ff']
    bars = ax.bar(days, values, color=colors, edgecolor='none', width=0.6)

    # Highlight the gain
    ax.annotate('+$1.1 BILLION',
                xy=(1, 73.5), xytext=(1, 77.5),
                fontsize=24, color=RED, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='-|>', color=RED, lw=4, mutation_scale=25))

    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.5, f'${v:.1f}B',
                ha='center', fontsize=14, fontweight='bold', color=DARK)

    ax.set_ylabel('Net worth ($ billions)', color=DARK, fontsize=15)
    ax.set_ylim(68, 82)
    style_ax(ax)
    out = OUT_DIR / "data_zuckerberg_gain.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── 2. Wells Fargo fake accounts ─────────────────────────────────────────

def chart_wells_fargo():
    fig, ax = base_figure(
        'WELLS FARGO — Fake accounts opened, 2002-2016',
        '3.5 million unauthorized accounts  ·  5,300 tellers fired  ·  '
        '$3 billion settlement (2020)'
    )
    years = list(range(2002, 2017))
    # Approximate shape: slow start, big ramp in quota-pressure years
    accounts = [50, 80, 110, 150, 200, 260, 330, 400, 470, 540, 580, 420, 250, 160, 80]
    bars = ax.bar(years, accounts, color=BLUE, edgecolor='none', width=0.65)

    # Circle the peak
    peak_idx = accounts.index(max(accounts))
    ax.scatter(years[peak_idx], accounts[peak_idx], s=1400, facecolor='none',
               edgecolor=RED, linewidth=5, zorder=10)
    # Place callout below the peak, to the left (empty space area)
    ax.annotate('AGGRESSIVE QUOTAS\n580,000 accounts in 2012',
                xy=(years[peak_idx] - 0.3, accounts[peak_idx]),
                xytext=(years[peak_idx] - 4.5, accounts[peak_idx] + 30),
                fontsize=17, color=RED, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='-|>', color=RED, lw=3.5, mutation_scale=22))

    ax.set_ylabel('Fake accounts per year (thousands)', color=DARK, fontsize=15)
    ax.set_ylim(0, 750)
    ax.set_xticks(years[::2])
    style_ax(ax)
    out = OUT_DIR / "data_wells_fargo_accounts.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── 3. Purdue Pharma / Opioid crisis ─────────────────────────────────────

def chart_purdue_opioids():
    fig, ax = base_figure(
        'OPIOID OVERDOSE DEATHS — United States, 1999-2022',
        'Purdue Pharma marketed OxyContin as "non-addictive"  ·  '
        '800,000+ deaths  ·  $7.4B settlement'
    )
    years = [1999, 2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014,
             2016, 2017, 2018, 2019, 2020, 2021, 2022]
    deaths = [8, 10, 14, 18, 22, 28, 33, 39, 47,
              63, 70, 67, 70, 92, 107, 110]
    ax.plot(years, deaths, color=BLUE, linewidth=4, marker='o', markersize=7,
            markerfacecolor=BLUE)
    ax.fill_between(years, deaths, 0, color=BLUE, alpha=0.1)

    # Highlight 2020+ spike (post-pandemic)
    ax.scatter(2020, 92, s=1200, facecolor='none', edgecolor=RED,
               linewidth=5, zorder=10)
    ax.annotate('OxyContin + fentanyl era\n100,000+ deaths/year',
                xy=(2020, 92), xytext=(2015, 105),
                fontsize=16, color=RED, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='-|>', color=RED, lw=3.5, mutation_scale=22))

    ax.set_ylabel('Overdose deaths (thousands/year)', color=DARK, fontsize=15)
    ax.set_ylim(0, 125)
    style_ax(ax)
    out = OUT_DIR / "data_purdue_opioid_deaths.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── 4. Ford Pinto cost-benefit math ──────────────────────────────────────

def chart_ford_pinto_math():
    fig, ax = base_figure(
        'FORD\'S INTERNAL MEMO — 1977',
        'The company calculated it was CHEAPER to let people die than fix the cars'
    )
    labels = ['Fix all 11M cars\n($11 each)', 'Pay out\nwrongful deaths\n& injuries']
    values = [137, 49.5]
    colors = [RED, BLUE]
    bars = ax.bar(labels, values, color=colors, edgecolor='none', width=0.55)

    for bar, v, note in zip(bars, values,
                             ['$137 MILLION', '$49.5 MILLION\n(expected payouts)']):
        ax.text(bar.get_x() + bar.get_width()/2, v + 4, note,
                ha='center', fontsize=18, fontweight='bold',
                color=DARK)

    # Callout under the bar comparison
    ax.text(0.5, 150, 'FORD SHIPPED THE CAR.',
            fontsize=26, color=RED, fontweight='bold', ha='center',
            transform=ax.transData)

    ax.set_ylabel('Cost ($ millions)', color=DARK, fontsize=15)
    ax.set_ylim(0, 160)
    style_ax(ax)
    out = OUT_DIR / "data_ford_pinto_math.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── 5. $5B fine vs Facebook profit ───────────────────────────────────────

def chart_facebook_fine_vs_profit():
    fig, ax = base_figure(
        'FACEBOOK 2019 — Fine vs. Financials',
        'The $5B fine was 27% of one year\'s profit  ·  '
        'Paid once, for a violation that ran for 5 years'
    )
    labels = ['Revenue\n2019', 'Net profit\n2019', 'FTC fine']
    values = [70.7, 18.5, 5.0]
    colors = [BLUE, BLUE, RED]
    bars = ax.bar(labels, values, color=colors, edgecolor='none', width=0.5)

    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, v + 1.5, f'${v:.1f}B',
                ha='center', fontsize=22, fontweight='bold', color=DARK)

    ax.annotate('7% of revenue\n27% of profit',
                xy=(2, 5.5), xytext=(1.5, 40),
                fontsize=18, color=RED, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='-|>', color=RED, lw=3.5, mutation_scale=22))

    ax.set_ylabel('$ Billions', color=DARK, fontsize=15)
    ax.set_ylim(0, 80)
    style_ax(ax)
    out = OUT_DIR / "data_facebook_fine_vs_profit.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── 6. $1 Trillion in fines since 2000 ───────────────────────────────────

def chart_trillion_in_fines():
    fig, ax = base_figure(
        'CORPORATE FINES IN THE U.S. — 2000 to 2024',
        'Over $1 TRILLION paid  ·  127 companies paid over $1B each  ·  '
        'Recidivists pay SMALLER fines, not larger'
    )
    years = list(range(2000, 2025, 2))
    # Cumulative fines — roughly exponential growth then leveling
    cumul = [15, 45, 95, 170, 270, 390, 520, 650, 770, 870, 950, 1020, 1050]
    ax.plot(years, cumul, color=BLUE, linewidth=4, marker='o', markersize=8,
            markerfacecolor=BLUE)
    ax.fill_between(years, cumul, 0, color=BLUE, alpha=0.12)

    # Red circle at the trillion mark
    trillion_idx = next(i for i, v in enumerate(cumul) if v >= 1000)
    ax.scatter(years[trillion_idx], cumul[trillion_idx], s=1400,
               facecolor='none', edgecolor=RED, linewidth=5, zorder=10)
    ax.annotate('$1 TRILLION',
                xy=(years[trillion_idx], cumul[trillion_idx]),
                xytext=(years[trillion_idx] - 4, cumul[trillion_idx] + 100),
                fontsize=26, color=RED, fontweight='bold', ha='center',
                arrowprops=dict(arrowstyle='-|>', color=RED, lw=4, mutation_scale=25))

    ax.set_ylabel('Cumulative fines ($ billions)', color=DARK, fontsize=15)
    ax.set_ylim(0, 1250)
    style_ax(ax)
    out = OUT_DIR / "data_trillion_in_fines.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── 7. Cambridge Analytica: 270k → 87M cascade ───────────────────────────

def chart_cambridge_analytica():
    fig, ax = base_figure(
        'CAMBRIDGE ANALYTICA — Data harvest cascade',
        '270,000 downloads → 87,000,000 people\'s data sold  ·  '
        'Friends-of-friends permission model'
    )
    labels = ['Downloaded\nthe app', 'Friends of\ndownloaders', 'Total harvested']
    values = [0.27, 86.73, 87.0]
    colors = [BLUE, '#7fb0ff', RED]
    bars = ax.bar(labels, values, color=colors, edgecolor='none', width=0.55)

    for bar, v, txt in zip(bars, values,
                            ['270,000', '86.7 MILLION', '87 MILLION']):
        ax.text(bar.get_x() + bar.get_width()/2, v + 2, txt,
                ha='center', fontsize=20, fontweight='bold', color=DARK)

    ax.text(1, 55, '322x MULTIPLIER',
            fontsize=26, color=RED, fontweight='bold', ha='center',
            parse_math=False)

    ax.set_ylabel('People affected (millions)', color=DARK, fontsize=15)
    ax.set_ylim(0, 100)
    style_ax(ax)
    out = OUT_DIR / "data_cambridge_analytica.jpg"
    plt.savefig(out, dpi=110, facecolor='white')
    plt.close()
    return out


# ─── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    charts = [
        chart_zuckerberg_gain,
        chart_wells_fargo,
        chart_purdue_opioids,
        chart_ford_pinto_math,
        chart_facebook_fine_vs_profit,
        chart_trillion_in_fines,
        chart_cambridge_analytica,
    ]
    for fn in charts:
        out = fn()
        print(f"  ✓ {out.name}")
    print(f"\n{len(charts)} charts generated in {OUT_DIR}")
