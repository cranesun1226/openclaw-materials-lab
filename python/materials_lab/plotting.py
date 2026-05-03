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

    labels = [_candidate_label(candidate) for candidate in ranked]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    figure = plt.figure(figsize=(10, 5.5))
    ax = figure.add_subplot(111)
    weighted_components = [_weighted_components(candidate) for candidate in ranked]
    if any(weighted_components):
        bottoms = [0.0 for _ in ranked]
        colors = {
            "stability": "#2f5d62",
            "bandGap": "#5f8d4e",
            "density": "#d9a441",
            "secondary": "#6c8ebf",
        }
        labels_seen: set[str] = set()
        for key in ["stability", "bandGap", "density", "secondary"]:
            values = [components.get(key, 0.0) for components in weighted_components]
            if not any(values):
                continue
            legend_label = _component_label(key)
            ax.bar(
                labels,
                values,
                bottom=bottoms,
                color=colors.get(key, "#8c8c8c"),
                label=legend_label if legend_label not in labels_seen else None,
            )
            labels_seen.add(legend_label)
            bottoms = [bottom + value for bottom, value in zip(bottoms, values)]
        ax.legend(loc="upper right")
    else:
        scores = [candidate["score"] for candidate in ranked]
        ax.bar(labels, scores, color="#2f5d62")
    ax.set_ylabel("Score")
    ax.set_title("Candidate Ranking")
    ax.tick_params(axis="x", labelrotation=35)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return str(path)


def write_metric_bar_chart(metrics: dict[str, Any], output_path: str) -> str | None:
    if plt is None:
        return None

    groups = _metric_groups(metrics)
    if not groups:
        return None

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    figure, axes = plt.subplots(len(groups), 1, figsize=(9, max(4.5, 2.1 * len(groups))))
    if len(groups) == 1:
        axes = [axes]
    figure.suptitle("Structure Metrics", fontsize=14)
    for ax, (title, items) in zip(axes, groups):
        labels = [key for key, _ in items]
        values = [value for _, value in items]
        ax.bar(labels, values, color="#7d9d9c")
        ax.set_title(title, loc="left", fontsize=10)
        ax.tick_params(axis="x", labelrotation=25)
        ax.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return str(path)


def _candidate_label(candidate: dict[str, Any]) -> str:
    formula = str(candidate.get("formula") or "").strip()
    material_id = str(candidate.get("materialId") or "").strip()
    return f"{material_id}\n{formula}" if formula else material_id


def _weighted_components(candidate: dict[str, Any]) -> dict[str, float]:
    components = candidate.get("scoreComponents")
    if not isinstance(components, dict):
        return {}
    weighted = components.get("weighted")
    if not isinstance(weighted, dict):
        return {}
    result: dict[str, float] = {}
    for key, value in weighted.items():
        if isinstance(value, (int, float)):
            result[str(key)] = float(value)
    return result


def _component_label(key: str) -> str:
    return {
        "stability": "Stability",
        "bandGap": "Band gap",
        "density": "Density",
        "secondary": "Secondary",
    }.get(key, key)


def _metric_groups(metrics: dict[str, Any]) -> list[tuple[str, list[tuple[str, float]]]]:
    group_specs = [
        ("Counts", ["numSites", "numElements", "liCount", "liNearestNeighborCountWithin3A"]),
        ("Li transport proxies", ["liFraction", "avgLiNeighborsWithin3A"]),
        ("Lengths (A)", ["a", "b", "c", "minLiLiDistanceA", "medianLiLiDistanceA"]),
        ("Angles (deg)", ["alpha", "beta", "gamma"]),
        ("Volume (A^3)", ["volume"]),
        ("Densities", ["densityGcm3", "liNumberDensityPerA3"]),
    ]
    groups: list[tuple[str, list[tuple[str, float]]]] = []
    for title, keys in group_specs:
        items = [
            (key, float(metrics[key]))
            for key in keys
            if isinstance(metrics.get(key), (int, float))
        ]
        if items:
            groups.append((title, items))
    return groups
