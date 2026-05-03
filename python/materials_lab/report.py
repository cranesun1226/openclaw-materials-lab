from __future__ import annotations

from pathlib import Path
from typing import Any


def write_markdown_report(payload: dict[str, Any]) -> tuple[str, list[str]]:
    output_path = Path(payload["outputPath"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    note_paths = payload.get("notePaths") or []
    artifact_paths = payload.get("artifactPaths") or []
    ranked_candidates = payload.get("rankedCandidates") or []
    screening_level = payload.get("screeningLevel") or _infer_screening_level(ranked_candidates)
    domain_warnings = list(payload.get("domainWarnings") or [])
    method_notes = list(payload.get("methodNotes") or [])
    provenance = payload.get("provenance") or {}
    if screening_level in {"technical-smoke", "proxy-screen"}:
        domain_warnings.append(
            "This report is a proxy screen. It does not establish transport performance, electrochemical stability, or experimental viability."
        )

    content = [
        f"# {payload['title']}",
        "",
        "## Confidence Level",
        "",
        f"- Screening level: `{screening_level}`",
        *[f"- Warning: {warning}" for warning in _dedupe(domain_warnings)],
        "",
        "## Research Goal",
        "",
        payload["goal"],
        "",
        "## Evaluation Criteria",
        "",
        *[f"- {item}" for item in payload.get("evaluationCriteria") or []],
        "",
        "## Candidate Table",
        "",
        _candidate_table(ranked_candidates),
        "",
        "## Ranked Candidates",
        "",
    ]

    for candidate in ranked_candidates:
        score_components = candidate.get("scoreComponents") or {}
        weighted = score_components.get("weighted") if isinstance(score_components, dict) else {}
        content.extend(
            [
                f"### {candidate['rank']}. {_candidate_link(candidate)} ({candidate['formula']})",
                "",
                f"- Score: {candidate['score']}",
                f"- Source: {candidate['source']}",
                f"- Family: {candidate.get('family', 'unknown')}",
                f"- Space group: {candidate.get('spacegroup', 'unknown')}",
                f"- eHull: {_format_value(candidate.get('energyAboveHullEv'))} eV",
                f"- Band gap: {_format_value(candidate.get('bandGapEv'))} eV",
                f"- Density: {_format_value(candidate.get('densityGcm3'))} g/cm3",
                f"- Duplicate group: {candidate.get('duplicateGroup', candidate.get('formula'))} ({candidate.get('duplicateCount', 1)} candidate(s))",
                *[f"- Weighted {key}: {_format_value(value)}" for key, value in (weighted or {}).items()],
                *[f"- {reason}" for reason in candidate.get("reasons") or []],
                *[f"- Warning: {warning}" for warning in _dedupe(candidate.get("warnings") or [])],
                "",
            ]
        )

    content.extend(
        [
            "## Method Notes",
            "",
            *([f"- {item}" for item in method_notes] or ["- No additional method notes were provided."]),
            "",
            "## Provenance",
            "",
            *(_provenance_lines(provenance) or ["- No provenance metadata was provided."]),
            "",
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
            "- Domain-specific properties such as ion mobility, defect chemistry, electrochemical windows, and interface reactivity require additional calculations or experiments.",
            "",
        ]
    )

    output_path.write_text("\n".join(content) + "\n", encoding="utf-8")
    references = [*note_paths, *artifact_paths]
    return str(output_path), references


def _candidate_table(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "No ranked candidates were provided."
    lines = [
        "| Rank | Material | Formula | Family | eHull eV | Gap eV | Density g/cm3 | Score | Flags |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for candidate in candidates:
        flags = []
        if int(candidate.get("duplicateCount") or 1) > 1:
            flags.append("duplicate-formula")
        if candidate.get("warnings"):
            flags.append("warning")
        lines.append(
            "| {rank} | {material} | {formula} | {family} | {ehull} | {gap} | {density} | {score} | {flags} |".format(
                rank=candidate.get("rank", ""),
                material=_candidate_link(candidate),
                formula=candidate.get("formula", ""),
                family=candidate.get("family", ""),
                ehull=_format_value(candidate.get("energyAboveHullEv")),
                gap=_format_value(candidate.get("bandGapEv")),
                density=_format_value(candidate.get("densityGcm3")),
                score=_format_value(candidate.get("score")),
                flags=", ".join(flags) if flags else "-",
            )
        )
    return "\n".join(lines)


def _candidate_link(candidate: dict[str, Any]) -> str:
    material_id = candidate.get("materialId", "unknown")
    url = candidate.get("materialsProjectUrl")
    if url:
        return f"[{material_id}]({url})"
    return str(material_id)


def _format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _infer_screening_level(candidates: list[dict[str, Any]]) -> str:
    for candidate in candidates:
        level = candidate.get("screeningLevel")
        if level:
            return str(level)
    return "proxy-screen"


def _dedupe(items: list[Any]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        text = str(item)
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _provenance_lines(provenance: dict[str, Any]) -> list[str]:
    lines = []
    for key, value in provenance.items():
        if isinstance(value, (dict, list)):
            lines.append(f"- {key}: `{value}`")
        else:
            lines.append(f"- {key}: {value}")
    return lines
