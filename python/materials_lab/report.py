from __future__ import annotations

from pathlib import Path
from typing import Any


def write_markdown_report(payload: dict[str, Any]) -> tuple[str, list[str]]:
    output_path = Path(payload["outputPath"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    note_paths = payload.get("notePaths") or []
    artifact_paths = payload.get("artifactPaths") or []
    ranked_candidates = payload.get("rankedCandidates") or []

    content = [
        f"# {payload['title']}",
        "",
        "## Research Goal",
        "",
        payload["goal"],
        "",
        "## Evaluation Criteria",
        "",
        *[f"- {item}" for item in payload.get("evaluationCriteria") or []],
        "",
        "## Ranked Candidates",
        "",
    ]

    for candidate in ranked_candidates:
        content.extend(
            [
                f"### {candidate['rank']}. {candidate['materialId']} ({candidate['formula']})",
                "",
                f"- Score: {candidate['score']}",
                f"- Source: {candidate['source']}",
                *[f"- {reason}" for reason in candidate.get("reasons") or []],
                "",
            ]
        )

    content.extend(
        [
            "## Notes",
            "",
            *([f"- {path}" for path in note_paths] or ["- No note files were provided."]),
            "",
            "## Artifacts",
            "",
            *([f"- {path}" for path in artifact_paths] or ["- No artifact paths were provided."]),
            "",
            "## Limitations",
            "",
            "- Ranking depends on the chosen criteria and available data.",
            "- Offline/mock mode should not be treated as equivalent to live database validation.",
            "",
        ]
    )

    output_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    references = [*note_paths, *artifact_paths]
    return str(output_path), references
