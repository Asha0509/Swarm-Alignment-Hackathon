"""Figure helpers: one color per monitor everywhere, direct line labels, CI bands, plain-language axes (FR-14)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# colorblind-safe (Okabe-Ito); one color per monitor, used in every figure
MONITOR_COLOR = {"M1": "#D55E00", "M2": "#0072B2", "M3": "#009E73", "M4": "#CC79A7", "M*": "#000000"}
MONITOR_LABEL = {"M1": "M1 transcript", "M2": "M2 metadata", "M3": "M3 consistency",
                 "M4": "M4 learned", "M*": "M* combined"}
FIGDIR = Path(__file__).resolve().parents[2] / "figures"


def new_ax(xlabel: str, ylabel: str, title: str = "", figsize: tuple[float, float] = (6.2, 4.2)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    return fig, ax


def label_line_end(ax, x: list[float], y: list[float], text: str, color: str) -> None:
    """Direct label at the right end of a line, no legend hunting."""
    if x and y:
        ax.annotate(text, (x[-1], y[-1]), xytext=(4, 0), textcoords="offset points",
                    va="center", ha="left", color=color, fontsize=9, fontweight="bold")


def band(ax, x: list[float], lo: list[float], hi: list[float], color: str) -> None:
    ax.fill_between(x, lo, hi, color=color, alpha=0.15, linewidth=0)


def save(fig, name: str, caption: str = "") -> None:
    FIGDIR.mkdir(exist_ok=True)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(FIGDIR / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    if caption:
        (FIGDIR / f"{name}.caption.txt").write_text(caption)
    plt.close(fig)
