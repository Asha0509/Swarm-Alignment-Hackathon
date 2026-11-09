#!/usr/bin/env python
"""Regenerate all figures from results/processed/report_numbers.json (F1 needs no data)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import matplotlib.patches as mpatches  # noqa: E402

from cachewhisper import figures as F  # noqa: E402

NUMS = Path(__file__).resolve().parents[1] / "results" / "processed" / "report_numbers.json"


def f1_schematic() -> None:
    """System schematic: agents -> registry -> (infra log | transcript+spoof) -> monitors -> defenses."""
    fig, ax = F.new_ax("", "", figsize=(8.4, 4.4))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)

    def box(x, y, w, h, text, color):
        ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04", fc=color, ec="#333", lw=1.2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, wrap=True)

    def arrow(x1, y1, x2, y2, text=""):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.3))
        if text:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.15, text, ha="center", fontsize=7.5, color="#555")

    box(0.2, 2.4, 1.7, 1.2, "Colluding +\nhonest agents", "#E8E8E8")
    box(2.6, 2.4, 1.7, 1.2, "Shared package\nregistry (CacheGym)", "#DCEEF8")
    box(5.0, 3.7, 2.1, 1.0, "Infra log\n(hash-chained truth)", "#DFF2E6")
    box(5.0, 1.1, 2.1, 1.0, "Transcript\n(spoof layer swaps\nclaims)", "#FBE4E4")
    box(7.8, 3.4, 2.0, 1.6, "Monitors\nM1 transcript\nM2 metadata\nM3 consistency\nM4 learned", "#F5F0E1")
    box(7.8, 1.1, 2.0, 1.0, "Defenses\nD1 isolate\nD2 randomize\nD3 quota", "#EDE7F6")

    arrow(1.9, 3.0, 2.6, 3.0)
    arrow(4.3, 3.2, 5.0, 4.0, "every op")
    arrow(4.3, 2.8, 5.0, 1.8, "self-report")
    arrow(7.1, 4.2, 7.8, 4.2)
    arrow(7.1, 1.6, 7.8, 3.6)
    arrow(8.8, 3.4, 8.8, 2.1, "inform")
    ax.text(5.0, 5.6, "Capacity vs. detectability through shared infrastructure", ha="left", fontsize=11,
            fontweight="bold")
    F.save(fig, "F1_schematic", "Figure 1. CacheGym: agents coordinate only through a shared registry. "
           "Every operation is recorded in a hash-chained infrastructure log, while the agent transcript can "
           "be spoofed. Four monitors read these sources; three cheap defenses close the channel.")


def f2_frontier(nums: dict) -> None:
    fig, ax = F.new_ax("Hidden bits per episode (capacity)", "Caught at 5% false-alarm rate",
                       "Capacity vs. detection frontier (spoofed transcripts)")
    data = nums.get("F2", {})
    for m, pts in data.items():
        xs = [p["capacity"] for p in pts]
        ys = [p["detect"] for p in pts]
        ax.plot(xs, ys, "-o", color=F.MONITOR_COLOR[m], ms=4)
        F.label_line_end(ax, xs, ys, F.MONITOR_LABEL[m], F.MONITOR_COLOR[m])
    ax.set_ylim(-0.03, 1.03)
    F.save(fig, "F2_frontier", f"Figure 2. Each point is an attack configuration (n={nums.get('n_f2', '?')} "
           "seeds). Up and left is worse oversight: high capacity that goes uncaught.")


def f3_spoof(nums: dict) -> None:
    fig, ax = F.new_ax("Fraction of covert actions spoofed", "Caught at 5% false-alarm rate",
                       "Detection vs. spoof rate")
    for m, series in nums.get("F3", {}).items():
        xs = [p["s"] for p in series]
        ys = [p["tpr"] for p in series]
        lo = [p.get("lo", y) for p, y in zip(series, ys, strict=False)]
        hi = [p.get("hi", y) for p, y in zip(series, ys, strict=False)]
        ax.plot(xs, ys, "-o", color=F.MONITOR_COLOR[m], ms=4)
        F.band(ax, xs, lo, hi, F.MONITOR_COLOR[m])
        F.label_line_end(ax, xs, ys, F.MONITOR_LABEL[m], F.MONITOR_COLOR[m])
    ax.set_ylim(-0.03, 1.03)
    F.save(fig, "F3_spoof_sweep", "Figure 3. As more actions are spoofed, the transcript monitor (M1) "
           "degrades while the consistency monitor (M3) rises. 95% CIs shown.")


def f5_adapt(nums: dict) -> None:
    fig, ax = F.new_ax("Adaptation round", "Bits per episode",
                       "Adaptive attacker: undetected capacity over rounds")
    for aw, series in nums.get("F5", {}).items():
        xs = [p["round"] for p in series]
        ys = [p["undetected_capacity"] for p in series]
        style = "-o" if aw == "aware" else "--s"
        color = "#000000" if aw == "aware" else "#999999"
        ax.plot(xs, ys, style, color=color, ms=4)
        F.label_line_end(ax, xs, ys, aw, color)
    F.save(fig, "F5_adaptation", "Figure 5. The aware attacker drives undetected capacity up as it learns "
           "which configurations evade the monitors; the unaware attacker does not.")


def f6_defenses(nums: dict) -> None:
    fig, ax = F.new_ax("Honest utility lost (points)", "Channel capacity removed (%)",
                       "Defense cost vs. benefit")
    for d, p in nums.get("F6", {}).items():
        ax.errorbar(p["utility_loss"], p["capacity_removed"], xerr=p.get("ul_err", 0),
                    yerr=p.get("cr_err", 0), fmt="o", ms=6, capsize=3, color="#5B3A9B")
        ax.annotate(d, (p["utility_loss"], p["capacity_removed"]), xytext=(5, 2),
                    textcoords="offset points", fontsize=9)
    F.save(fig, "F6_defenses", "Figure 6. Top-left is best: removes most capacity for least honest cost. "
           "Error bars are 95% CIs.")


def main() -> None:
    f1_schematic()
    nums = json.loads(NUMS.read_text()) if NUMS.exists() else {}
    for fn in (f2_frontier, f3_spoof, f5_adapt, f6_defenses):
        try:
            fn(nums)
        except Exception as e:  # noqa: BLE001 - a missing arm should not stop the others
            print(f"skip {fn.__name__}: {e}")
    print(f"figures written to {F.FIGDIR}")


if __name__ == "__main__":
    main()
