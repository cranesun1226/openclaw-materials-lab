from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import matplotlib.pyplot as plt  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    plt = None


def write_candidate_score_plot(ranked: list[dict[str, Any]], output_path: str) -> str | None:
    if plt is None:
        return None

    labels = [candidate["materialId"] for candidate in ranked]
    scores = [candidate["score"] for candidate in ranked]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    figure = plt.figure(figsize=(8, 4.5))
    ax = figure.add_subplot(111)
    ax.bar(labels, scores, color="#2f5d62")
    ax.set_ylabel("Score")
    ax.set_title("Candidate Ranking")
    ax.tick_params(axis="x", labelrotation=30)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return str(path)


def write_metric_bar_chart(metrics: dict[str, Any], output_path: str) -> str | None:
    if plt is None:
        return None

    numeric_items = [(key, value) for key, value in metrics.items() if isinstance(value, (int, float))]
    if not numeric_items:
        return None

    labels = [item[0] for item in numeric_items]
    values = [item[1] for item in numeric_items]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    figure = plt.figure(figsize=(8, 4.5))
    ax = figure.add_subplot(111)
    ax.bar(labels, values, color="#7d9d9c")
    ax.set_title("Structure Metrics")
    ax.tick_params(axis="x", labelrotation=45)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return str(path)
