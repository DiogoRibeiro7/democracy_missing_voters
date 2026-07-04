from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure


def export_current_figure(figure: Figure, output_path: Path, *, dpi: int = 220) -> Path:
    """Export a Matplotlib figure with stable high-resolution defaults."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    return output_path
