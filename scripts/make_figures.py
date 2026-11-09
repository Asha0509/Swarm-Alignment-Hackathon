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
    """Hero: capacity vs detection across channel/bits-per-op/noise configs, for the infra monitors.

    Capacity now varies (channels run at several noise levels), so this is a real frontier.
    """
    f2b = nums.get("F2b")
    if not f2b:
        return
    fig, ax = F.new_ax("Hidden bits per episode (capacity)", "Attacks caught (at 5% false-alarm rate)",
                       "Capacity vs. detection across covert configurations")
    for m in ("M2", "M4", "M*"):
        pts = f2b.get(m, [])
        ax.scatter([p["capacity"] for p in pts], [p["detect"] for p in pts], s=16,
                   color=F.MONITOR_COLOR[m], alpha=0.4, edgecolors="none", label=F.MONITOR_LABEL[m])
    ms = sorted(f2b.get("M*", []), key=lambda p: -p["capacity"])
    front, best = [], 1.1
    for p in ms:
        if p["detect"] < best:
            front.append((p["capacity"], p["detect"]))
            best = p["detect"]
    if front:
        fx, fy = zip(*sorted(front), strict=True)
        ax.plot(fx, fy, "-", color=F.MONITOR_COLOR["M*"], lw=2)
        F.label_line_end(ax, list(fx), list(fy), "M* frontier", F.MONITOR_COLOR["M*"])
    ax.legend(fontsize=8, frameon=False, loc="center left")
    ax.set_ylim(-0.05, 1.08)
    F.save(fig, "F2_frontier", "Figure 2. Each point is a covert configuration (channel, bits per operation, "
           "channel noise; 20 seeds each) scored under naive spoofing. Capacity varies because the channel is "
           "lossy. The line is the combined monitor's Pareto frontier: the most hidden capacity reached at each "
           "detection level. The metadata monitor leaves a low-detection corridor at high capacity that the "
           "combined monitor mostly closes against this clumsy attacker.")

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
        dy = {"M*": 9, "M3": -9, "M1": -9, "M2": 9}.get(m, 0)  # stagger co-located end labels
        F.label_line_end(ax, xs, ys, F.MONITOR_LABEL[m], F.MONITOR_COLOR[m], dy=dy)
    ax.set_ylim(-0.03, 1.08)
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


def f8_disguise(nums: dict) -> None:
    """Fabrication vs disguise: each monitor's AUROC against a clumsy spoofer and a consistent liar."""
    h6 = nums.get("H6")
    if not h6:
        return
    import numpy as np
    mons = [m for m in ("M1", "M2", "M3", "M4", "M*") if m in h6.get("naive", {}) and m in h6.get("hard", {})]
    fig, ax = F.new_ax("", "Separates attacks from benign (AUROC)",
                       "What survives a consistent liar")
    x = np.arange(len(mons))
    naive = [h6["naive"][m]["auroc"] for m in mons]
    hard = [h6["hard"][m]["auroc"] for m in mons]
    ax.bar(x - 0.2, naive, 0.38, label="clumsy spoofer (fabricates)", color="#BBBBBB")
    ax.bar(x + 0.2, hard, 0.38, label="consistent liar (disguises)",
           color=[F.MONITOR_COLOR[m] for m in mons])
    ax.axhline(0.5, ls="--", lw=1, color="#999")
    ax.text(len(mons) - 0.5, 0.52, "chance", fontsize=8, color="#999", ha="right")
    ax.set_xticks(x)
    ax.set_xticklabels([F.MONITOR_LABEL[m] for m in mons], rotation=20, ha="right", fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, frameon=False, loc="lower left")
    F.save(fig, "F8_disguise", "Figure 8. Grey bars: a spoofer that fabricates cover stories is caught by the "
           "consistency and combined monitors (AUROC 1.0). Colored bars: a consistent liar that backs its "
           "claims with real benign work defeats the consistency monitor (AUROC 0.50, chance) and degrades "
           f"the combined monitor, so no infrastructure monitor is robust. n={h6['hard']['M2']['n_att']} attacks.")


def f9_scaling(nums: dict) -> None:
    """Swarm scaling: undetected delivered capacity vs number of receivers (echoes one board, many readers)."""
    f9 = nums.get("F9")
    if not f9:
        return
    fig, ax = F.new_ax("Receivers in the swarm (N)", "Undetected bits delivered per broadcast",
                       "One covert broadcast scales to the whole swarm")
    colors = {"E2": F.MONITOR_COLOR["M2"], "E3": F.MONITOR_COLOR["M4"]}
    for ch, series in f9.items():
        xs = [s["n"] for s in series]
        ys = [s["undetected"] for s in series]
        ax.plot(xs, ys, "-o", color=colors.get(ch, "#555"), ms=5)
        F.label_line_end(ax, xs, ys, f"{ch} channel", colors.get(ch, "#555"))
    xs0 = sorted({s["n"] for series in f9.values() for s in series})
    ax.plot(xs0, [16 * x for x in xs0], "--", color="#999", lw=1)
    ax.annotate("16 bits x N (no detection)", (xs0[-1], 16 * xs0[-1]), xytext=(-6, 6),
                textcoords="offset points", ha="right", fontsize=8, color="#999", style="italic")
    F.save(fig, "F9_scaling", "Figure 9. A coordinator broadcasts a 16 bit secret to N receivers (30 seeds each). "
           "Undetected bits delivered, measured against the spoof-invariant metadata monitor, grow close to "
           "linearly with swarm size, because more readers do not raise the monitor's detection. One board "
           "reaches many agents nearly for free, as in the incident.")


def main() -> None:
    f1_schematic()
    nums = json.loads(NUMS.read_text()) if NUMS.exists() else {}
    for fn in (f2_frontier, f3_spoof, f5_adapt, f6_defenses, f8_disguise, f9_scaling):
        try:
            fn(nums)
        except Exception as e:  # noqa: BLE001 - a missing arm should not stop the others
            print(f"skip {fn.__name__}: {e}")
    print(f"figures written to {F.FIGDIR}")


if __name__ == "__main__":
    main()
