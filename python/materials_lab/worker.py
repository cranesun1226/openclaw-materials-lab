from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from . import __version__
from .ase_ops import run_relaxation
from .mp_client import fetch_material, search_materials
from .plotting import write_candidate_score_plot, write_metric_bar_chart
from .pymatgen_ops import analyze_structure, write_cif, write_structure_json
from .report import write_markdown_report
from .schemas import (
    WorkerError,
    ensure_bool,
    ensure_dict,
    ensure_number,
    ensure_string,
    ensure_string_list,
    success,
)

try:
    from pymatgen.core import Composition  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    Composition = None


def main() -> int:
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return _write_json(
            WorkerError("INVALID_REQUEST", "Worker expected JSON on stdin.").as_payload()
        )

    try:
        request = ensure_dict(json.loads(raw_input), field="request")
        action = ensure_string(request.get("action"), field="action")
        request_id = ensure_string(request.get("requestId"), field="requestId")
        payload = ensure_dict(request.get("payload") or {}, field="payload")
        response = dispatch(action=action, request_id=request_id, payload=payload)
    except WorkerError as exc:
        response = exc.as_payload()
    except Exception as exc:  # pragma: no cover - unhandled edge path
        response = WorkerError(
            "UNHANDLED_WORKER_ERROR",
            f"Unhandled worker error: {exc}",
            hint="Inspect the Python environment and worker stack traces.",
        ).as_payload(stderr=str(exc))

    return _write_json(response)


def dispatch(*, action: str, request_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("MATERIALS_PROJECT_API_KEY") or None
    handlers = {
        "ping": lambda: handle_ping(request_id=request_id),
        "search_materials": lambda: handle_search_materials(request_id=request_id, payload=payload, api_key=api_key),
        "fetch_structure": lambda: handle_fetch_structure(request_id=request_id, payload=payload, api_key=api_key),
        "analyze_structure": lambda: handle_analyze_structure(request_id=request_id, payload=payload, api_key=api_key),
        "compare_candidates": lambda: handle_compare_candidates(request_id=request_id, payload=payload),
        "ase_relax": lambda: handle_ase_relax(request_id=request_id, payload=payload, api_key=api_key),
        "batch_screen": lambda: handle_batch_screen(request_id=request_id, payload=payload, api_key=api_key),
        "export_report": lambda: handle_export_report(request_id=request_id, payload=payload),
    }
    if action not in handlers:
        raise WorkerError("UNKNOWN_ACTION", f"Unknown worker action '{action}'.")
    return handlers[action]()


def handle_ping(*, request_id: str) -> dict[str, Any]:
    return success(
        action="ping",
        request_id=request_id,
        summary=f"Materials Lab worker {__version__} is ready.",
        data={
            "worker": __version__,
            "python": sys.version.split()[0],
        },
    )


def handle_search_materials(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    candidates, used_offline = search_materials(payload, api_key=api_key)
    data = {
        "candidates": [_candidate_summary(item) for item in candidates],
        "usedOfflineData": used_offline,
    }
    mode = "offline mock data" if used_offline else "Materials Project"
    return success(
        action="search_materials",
        request_id=request_id,
        summary=f"Found {len(data['candidates'])} candidate materials using {mode}.",
        data=data,
        warnings=["Using offline mock data."] if used_offline else [],
    )


def handle_fetch_structure(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    material_id = ensure_string(payload.get("materialId"), field="materialId")
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    format_name = str(payload.get("format") or "both").lower()
    allow_offline = ensure_bool(payload.get("allowOffline"), field="allowOffline", default=True)
    material, used_offline = fetch_material(material_id, api_key=api_key, allow_offline=allow_offline)
    structure_data = material.get("structure")
    if not isinstance(structure_data, dict):
        raise WorkerError("STRUCTURE_UNAVAILABLE", f"No structure data is available for '{material_id}'.")

    json_path = write_structure_json(structure_data, str(artifact_dir / f"{material_id}.json"))
    artifacts = [json_path]
    cif_path = None
    warnings: list[str] = []

    if format_name in {"cif", "both"}:
        maybe_cif_path = write_cif(structure_data, str(artifact_dir / f"{material_id}.cif"))
        if maybe_cif_path:
            cif_path = maybe_cif_path
            artifacts.append(cif_path)
        else:
            warnings.append("CIF export was skipped because pymatgen is unavailable for this structure.")

    data = {
        "material": _candidate_summary(material),
        "structurePath": json_path,
        "cifPath": cif_path,
        "structure": structure_data,
        "usedOfflineData": used_offline,
    }
    return success(
        action="fetch_structure",
        request_id=request_id,
        summary=f"Fetched structure for {material_id} and wrote {len(artifacts)} artifact(s).",
        data=data,
        artifacts=artifacts,
        warnings=warnings,
    )


def handle_analyze_structure(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    allow_offline = ensure_bool(payload.get("allowOffline"), field="allowOffline", default=True)
    material_id = ensure_string(payload.get("materialId"), field="materialId", required=False)
    structure_path = ensure_string(payload.get("structurePath"), field="structurePath", required=False)

    structure_data = None
    used_offline = False
    warnings: list[str] = []

    if material_id and not structure_path:
        material, used_offline = fetch_material(material_id, api_key=api_key, allow_offline=allow_offline)
        structure_data = material.get("structure")
        if not isinstance(structure_data, dict):
            raise WorkerError("STRUCTURE_UNAVAILABLE", f"No structure data is available for '{material_id}'.")

    analysis = analyze_structure(structure_path=structure_path, structure_data=structure_data)
    plot_path = write_metric_bar_chart(analysis["summaryMetrics"], str(artifact_dir / "structure-metrics.png"))
    artifacts = [plot_path] if plot_path else []
    if plot_path is None:
        warnings.append("Metric plot was skipped because matplotlib is unavailable.")

    data = {
        "materialId": material_id,
        "formula": analysis["summaryMetrics"].get("formula"),
        "summaryMetrics": analysis["summaryMetrics"],
        "readableSummary": analysis["readableSummary"],
        "plotPath": plot_path,
        "usedOfflineData": used_offline,
    }
    return success(
        action="analyze_structure",
        request_id=request_id,
        summary=analysis["readableSummary"],
        data=data,
        artifacts=[artifact for artifact in artifacts if artifact],
        warnings=warnings,
    )


def handle_compare_candidates(*, request_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise WorkerError("INVALID_PARAMS", "compare_candidates requires at least two candidate objects.")

    criteria = ensure_dict(payload.get("criteria") or {}, field="criteria")
    merged_criteria = _prepare_compare_criteria(criteria)
    rankable_candidates, excluded_candidates = _filter_candidates_for_ranking(candidates, merged_criteria)
    if not rankable_candidates:
        raise WorkerError(
            "NO_RANKABLE_CANDIDATES",
            "All candidate materials were excluded by the requested chemistry filters.",
            hint="Relax excludeToxicElements, excludeRiskyChemistry, or filterMolecularSalts.",
        )

    ranked = _rank_candidates(rankable_candidates, merged_criteria)
    top_k = int(payload.get("topK") or len(ranked))
    ranked = ranked[:top_k]
    plot_path = write_candidate_score_plot(ranked, str(artifact_dir / "candidate-ranking.png"))
    table_paths = _write_candidate_table_artifacts(ranked, artifact_dir)
    warnings = _ranking_warnings(rankable_candidates, ranked, merged_criteria, excluded_candidates)
    if plot_path is None:
        warnings.append("Candidate ranking plot was skipped because matplotlib is unavailable.")

    data = {
        "ranked": ranked,
        "criteria": merged_criteria,
        "plotPath": plot_path,
        "tablePaths": table_paths,
        "screeningLevel": merged_criteria["screeningLevel"],
        "diversity": _diversity_report(rankable_candidates, ranked, merged_criteria),
        "excludedCandidates": excluded_candidates,
    }
    return success(
        action="compare_candidates",
        request_id=request_id,
        summary=f"Ranked {len(ranked)} candidate materials.",
        data=data,
        artifacts=[artifact for artifact in [plot_path, *table_paths] if artifact],
        warnings=warnings,
    )


def handle_ase_relax(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    artifact_dir = ensure_string(payload.get("artifactDir"), field="artifactDir")
    structure_path = ensure_string(payload.get("structurePath"), field="structurePath", required=False)
    material_id = ensure_string(payload.get("materialId"), field="materialId", required=False)
    allow_offline = ensure_bool(payload.get("allowOffline"), field="allowOffline", default=True)
    steps = int(ensure_number(payload.get("steps"), field="steps", default=100) or 100)
    fmax_ev_a = float(ensure_number(payload.get("fmaxEvA"), field="fmaxEvA", default=0.05) or 0.05)
    calculator = ensure_string(payload.get("calculator"), field="calculator", required=False) or "EMT"

    structure_data = None
    used_offline = False
    if structure_path:
        structure_data = json.loads(Path(structure_path).read_text("utf-8"))
    elif material_id:
        material, used_offline = fetch_material(material_id, api_key=api_key, allow_offline=allow_offline)
        structure_data = material.get("structure")

    if not isinstance(structure_data, dict):
        raise WorkerError("STRUCTURE_UNAVAILABLE", "ASE relaxation requires structurePath or materialId with available structure data.")

    summary_metrics, artifacts, warnings = run_relaxation(
        structure_data=structure_data,
        artifact_dir=artifact_dir,
        steps=steps,
        fmax_ev_a=fmax_ev_a,
        calculator=calculator,
    )
    data = {
        "summaryMetrics": summary_metrics,
        "relaxedStructurePath": next((artifact for artifact in artifacts if artifact.endswith(".xyz")), None),
        "trajectoryPath": None,
        "usedOfflineData": used_offline,
    }
    return success(
        action="ase_relax",
        request_id=request_id,
        summary="ASE relaxation workflow completed.",
        data=data,
        artifacts=artifacts,
        warnings=warnings,
    )


def handle_batch_screen(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    candidate_ids = ensure_string_list(payload.get("candidateIds"), field="candidateIds")
    limit = int(ensure_number(payload.get("limit"), field="limit", default=float(len(candidate_ids))) or len(candidate_ids))
    allow_offline = ensure_bool(payload.get("allowOffline"), field="allowOffline", default=True)
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)

    materials = []
    used_offline = False
    for material_id in candidate_ids[:limit]:
        material, offline = fetch_material(material_id, api_key=api_key, allow_offline=allow_offline)
        used_offline = used_offline or offline
        materials.append(_candidate_summary(material))

    batch_criteria = _prepare_compare_criteria({
        "stabilityWeight": 0.5,
        "bandGapWeight": 0.3,
        "densityWeight": 0.2,
        "bandGapTargetEv": 3.0,
        "densityTargetGcm3": 5.0,
    })
    rankable_materials, excluded_candidates = _filter_candidates_for_ranking(materials, batch_criteria)
    ranked = _rank_candidates(rankable_materials, batch_criteria)
    plot_path = write_candidate_score_plot(ranked, str(artifact_dir / "batch-screen-ranking.png"))
    table_paths = _write_candidate_table_artifacts(ranked, artifact_dir, prefix="batch-screen-ranking")
    return success(
        action="batch_screen",
        request_id=request_id,
        summary=f"Screened {len(materials)} candidates and produced a ranked shortlist.",
        data={
            "screened": materials,
            "ranked": ranked,
            "tablePaths": table_paths,
            "excludedCandidates": excluded_candidates,
            "usedOfflineData": used_offline,
        },
        artifacts=[artifact for artifact in [plot_path, *table_paths] if artifact],
        warnings=["Using offline mock data."] if used_offline else [],
    )


def handle_export_report(*, request_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    ensure_string(payload.get("title"), field="title")
    ensure_string(payload.get("goal"), field="goal")
    evaluation_criteria = ensure_string_list(payload.get("evaluationCriteria"), field="evaluationCriteria")
    output_path = ensure_string(payload.get("outputPath"), field="outputPath")
    ranked_candidates = payload.get("rankedCandidates")
    if not isinstance(ranked_candidates, list) or not ranked_candidates:
        raise WorkerError("INVALID_PARAMS", "export_report requires rankedCandidates.")

    output_file, references = write_markdown_report({
        "title": payload["title"],
        "goal": payload["goal"],
        "evaluationCriteria": evaluation_criteria,
        "rankedCandidates": ranked_candidates,
        "notePaths": payload.get("notePaths") or [],
        "artifactPaths": payload.get("artifactPaths") or [],
        "outputPath": output_path,
        "screeningLevel": payload.get("screeningLevel"),
        "domainWarnings": payload.get("domainWarnings") or [],
        "methodNotes": payload.get("methodNotes") or [],
        "provenance": payload.get("provenance") or {},
    })
    return success(
        action="export_report",
        request_id=request_id,
        summary=f"Exported markdown report to {output_file}.",
        data={"outputPath": output_file, "references": references},
        artifacts=[output_file],
    )


def _candidate_summary(item: dict[str, Any]) -> dict[str, Any]:
    material_id = item.get("material_id") or item.get("materialId")
    formula = item.get("formula")
    source = item.get("source", "mock")
    summary = {
        "materialId": item.get("material_id"),
        "formula": formula,
        "energyAboveHullEv": item.get("energy_above_hull_ev"),
        "bandGapEv": item.get("band_gap_ev"),
        "densityGcm3": item.get("density_gcm3"),
        "volume": item.get("volume"),
        "sites": item.get("sites"),
        "spacegroup": item.get("spacegroup"),
        "elements": item.get("elements") or [],
        "source": source,
        "notes": item.get("notes") or [],
    }
    if item.get("materialId") and not summary["materialId"]:
        summary["materialId"] = item.get("materialId")
    if source == "materials-project" and material_id:
        summary["materialsProjectUrl"] = f"https://materialsproject.org/materials/{material_id}"
    if formula:
        summary["family"] = _infer_material_family(summary)
    return summary


def _rank_candidates(candidates: list[dict[str, Any]], criteria: dict[str, Any]) -> list[dict[str, Any]]:
    formula_counts = Counter(_formula_group(candidate) for candidate in candidates)
    family_counts = Counter(_infer_material_family(candidate) for candidate in candidates)
    ranked = []
    stability_weight = float(criteria["stabilityWeight"])
    band_gap_weight = float(criteria["bandGapWeight"])
    density_weight = float(criteria["densityWeight"])

    for candidate in candidates:
        stability = _stability_score(candidate.get("energyAboveHullEv"))
        band_gap = _band_gap_score(candidate.get("bandGapEv"), criteria)
        density = _density_score(candidate.get("densityGcm3"), criteria)
        risk_profile = _candidate_risk_profile(candidate, criteria)
        secondary = _secondary_score(candidate, criteria, risk_profile)
        secondary_weight = max(0.0, min(float(criteria.get("secondaryWeight") or 0.0), 0.5))
        primary_scale = 1.0 - secondary_weight
        weighted = {
            "stability": round(stability * stability_weight * primary_scale, 6),
            "bandGap": round(band_gap * band_gap_weight * primary_scale, 6),
            "density": round(density * density_weight * primary_scale, 6),
            "secondary": round(secondary["score"] * secondary_weight, 6),
        }
        primary_score = stability * stability_weight + band_gap * band_gap_weight + density * density_weight
        score = _final_score(primary_score, secondary["score"], risk_profile["penalty"], criteria)
        family = _infer_material_family(candidate)
        formula_group = _formula_group(candidate)
        reasons = _score_reasons(stability, band_gap, density, secondary, risk_profile, criteria)
        warnings = list(candidate.get("warnings") or [])
        if formula_counts[formula_group] > 1:
            warnings.append(f"Duplicate reduced-formula group appears {formula_counts[formula_group]} times.")
        if family_counts[family] > 1:
            warnings.append(f"Material family '{family}' appears {family_counts[family]} times in the candidate pool.")
        warnings.extend(risk_profile["warnings"])
        enriched = dict(candidate)
        enriched["score"] = round(score, 6)
        enriched["primaryScore"] = round(primary_score, 6)
        enriched["secondaryScore"] = round(secondary["score"], 6)
        enriched["riskPenalty"] = round(risk_profile["penalty"], 6)
        enriched["scoreComponents"] = {
            "raw": {
                "stability": round(stability, 6),
                "bandGap": round(band_gap, 6),
                "density": round(density, 6),
                "secondary": round(secondary["score"], 6),
                "riskPenalty": round(risk_profile["penalty"], 6),
            },
            "weighted": weighted,
            "secondary": secondary["components"],
        }
        enriched["reasons"] = reasons
        enriched["warnings"] = warnings
        enriched["riskProfile"] = risk_profile
        enriched["compositionDescriptors"] = risk_profile["compositionDescriptors"]
        enriched["family"] = family
        enriched["duplicateGroup"] = formula_group
        enriched["duplicateCount"] = formula_counts[formula_group]
        enriched["screeningLevel"] = criteria["screeningLevel"]
        if enriched.get("source") == "materials-project" and enriched.get("materialId"):
            enriched["materialsProjectUrl"] = f"https://materialsproject.org/materials/{enriched['materialId']}"
        ranked.append(enriched)

    ranked.sort(
        key=lambda item: (
            item["score"],
            item.get("secondaryScore", 0),
            -float(item.get("energyAboveHullEv") or 0.0),
            item.get("bandGapEv") or 0.0,
        ),
        reverse=True,
    )
    for index, candidate in enumerate(ranked, start=1):
        candidate["rawRank"] = index
    ranked = _apply_diversity_controls(ranked, criteria)
    for index, candidate in enumerate(ranked, start=1):
        candidate["rank"] = index
    return ranked


def _prepare_compare_criteria(criteria: dict[str, Any]) -> dict[str, Any]:
    preset = str(criteria.get("preset") or "generic").strip().lower()
    if preset in {"solid-electrolyte", "solid_electrolyte", "solid electrolyte"}:
        defaults: dict[str, Any] = {
            "preset": "solid-electrolyte",
            "screeningLevel": "proxy-screen",
            "stabilityWeight": 0.65,
            "bandGapWeight": 0.35,
            "densityWeight": 0.0,
            "bandGapScoringMode": "minimum",
            "minimumBandGapEv": 2.0,
            "bandGapTargetEv": 5.0,
            "densityScoringMode": "advisory",
            "densityTargetGcm3": 3.0,
            "secondaryWeight": 0.10,
            "riskPenaltyWeight": 0.30,
            "preferredBandGapEv": 4.0,
            "preferredLiFractionMin": 0.10,
            "preferredLiFractionMax": 0.45,
            "excludeToxicElements": True,
            "excludeRiskyChemistry": True,
            "filterMolecularSalts": True,
            "requiresLithium": True,
            "excludedElements": ["Be", "Cd", "Hg", "Pb", "Tl", "Th", "U"],
            "flaggedElements": ["As", "Cr", "Sb", "Se"],
            "maxHydrogenAtomicFraction": 0.15,
            "diversifyBy": "formula",
            "maxPerFormula": 1,
            "maxPerFamily": 3,
        }
    else:
        defaults = {
            "preset": "generic",
            "screeningLevel": "proxy-screen",
            "stabilityWeight": 0.45,
            "bandGapWeight": 0.35,
            "densityWeight": 0.20,
            "bandGapScoringMode": "target",
            "minimumBandGapEv": 0.0,
            "bandGapTargetEv": 3.0,
            "densityScoringMode": "target",
            "densityTargetGcm3": 5.0,
            "secondaryWeight": 0.0,
            "riskPenaltyWeight": 0.0,
            "preferredBandGapEv": 3.0,
            "preferredLiFractionMin": 0.0,
            "preferredLiFractionMax": 1.0,
            "excludeToxicElements": False,
            "excludeRiskyChemistry": False,
            "filterMolecularSalts": False,
            "requiresLithium": False,
            "excludedElements": [],
            "flaggedElements": [],
            "maxHydrogenAtomicFraction": 1.0,
            "diversifyBy": "none",
            "maxPerFormula": 0,
            "maxPerFamily": 0,
        }
    merged = {key: criteria.get(key, value) for key, value in defaults.items()}
    for key in [
        "stabilityWeight",
        "bandGapWeight",
        "densityWeight",
        "minimumBandGapEv",
        "bandGapTargetEv",
        "densityTargetGcm3",
        "secondaryWeight",
        "riskPenaltyWeight",
        "preferredBandGapEv",
        "preferredLiFractionMin",
        "preferredLiFractionMax",
        "maxHydrogenAtomicFraction",
    ]:
        merged[key] = float(merged[key])
    for key in ["maxPerFormula", "maxPerFamily"]:
        merged[key] = int(merged[key] or 0)
    for key in ["excludeToxicElements", "excludeRiskyChemistry", "filterMolecularSalts", "requiresLithium"]:
        merged[key] = bool(merged[key])
    for key in ["excludedElements", "flaggedElements"]:
        merged[key] = [str(item) for item in (merged.get(key) or [])]
    return merged


def _band_gap_score(value: Any, criteria: dict[str, Any]) -> float:
    mode = str(criteria.get("bandGapScoringMode") or "target").lower()
    if mode == "minimum":
        return _minimum_score(value, float(criteria.get("minimumBandGapEv") or 0.0))
    return _target_score(value, float(criteria.get("bandGapTargetEv") or 0.0))


def _density_score(value: Any, criteria: dict[str, Any]) -> float:
    mode = str(criteria.get("densityScoringMode") or "target").lower()
    if mode in {"none", "advisory"} and float(criteria.get("densityWeight") or 0.0) <= 0:
        return _target_score(value, float(criteria.get("densityTargetGcm3") or 0.0))
    return _target_score(value, float(criteria.get("densityTargetGcm3") or 0.0))


def _filter_candidates_for_ranking(candidates: list[dict[str, Any]], criteria: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rankable = []
    excluded = []
    for candidate in candidates:
        risk_profile = _candidate_risk_profile(candidate, criteria)
        if risk_profile["excluded"]:
            excluded.append({
                "materialId": candidate.get("materialId"),
                "formula": candidate.get("formula"),
                "family": _infer_material_family(candidate),
                "riskFlags": risk_profile["riskFlags"],
                "exclusionReasons": risk_profile["exclusionReasons"],
            })
            continue
        rankable.append(candidate)
    return rankable, excluded


def _final_score(primary_score: float, secondary_score: float, risk_penalty: float, criteria: dict[str, Any]) -> float:
    secondary_weight = max(0.0, min(float(criteria.get("secondaryWeight") or 0.0), 0.5))
    risk_weight = max(0.0, float(criteria.get("riskPenaltyWeight") or 0.0))
    score = primary_score * (1.0 - secondary_weight) + secondary_score * secondary_weight
    score -= risk_penalty * risk_weight
    return max(0.0, min(score, 1.0))


def _secondary_score(candidate: dict[str, Any], criteria: dict[str, Any], risk_profile: dict[str, Any]) -> dict[str, Any]:
    family = _infer_material_family(candidate)
    descriptors = risk_profile["compositionDescriptors"]
    band_gap_margin = _target_score(candidate.get("bandGapEv"), float(criteria.get("preferredBandGapEv") or 4.0))
    li_fraction = descriptors.get("liAtomicFraction")
    li_fraction_score = _range_score(
        li_fraction,
        float(criteria.get("preferredLiFractionMin") or 0.0),
        float(criteria.get("preferredLiFractionMax") or 1.0),
    )
    family_prior = _family_prior_score(family)
    chemistry = 1.0 - min(risk_profile["penalty"], 1.0)
    components = {
        "bandGapMargin": round(band_gap_margin, 6),
        "liFraction": round(li_fraction_score, 6),
        "familyPrior": round(family_prior, 6),
        "chemistryRisk": round(chemistry, 6),
    }
    score = (
        band_gap_margin * 0.25
        + li_fraction_score * 0.30
        + family_prior * 0.30
        + chemistry * 0.15
    )
    return {"score": max(0.0, min(score, 1.0)), "components": components}


def _score_reasons(
    stability: float,
    band_gap: float,
    density: float,
    secondary: dict[str, Any],
    risk_profile: dict[str, Any],
    criteria: dict[str, Any],
) -> list[str]:
    reasons = [f"stability score {stability:.3f}"]
    if str(criteria.get("bandGapScoringMode")).lower() == "minimum":
        reasons.append(f"band-gap minimum screen {band_gap:.3f} (min {criteria['minimumBandGapEv']} eV)")
    else:
        reasons.append(f"band-gap alignment {band_gap:.3f} (target {criteria['bandGapTargetEv']} eV)")
    if float(criteria.get("densityWeight") or 0.0) > 0:
        reasons.append(f"density alignment {density:.3f} (target {criteria['densityTargetGcm3']} g/cm3)")
    else:
        reasons.append(f"density advisory {density:.3f} (not weighted)")
    if float(criteria.get("secondaryWeight") or 0.0) > 0:
        components = secondary.get("components") or {}
        reasons.append(
            "secondary tie-breaker "
            f"{secondary['score']:.3f} "
            f"(Li fraction {components.get('liFraction', 0):.3f}, "
            f"family prior {components.get('familyPrior', 0):.3f}, "
            f"gap margin {components.get('bandGapMargin', 0):.3f})"
        )
    if risk_profile["penalty"] > 0:
        reasons.append(f"chemistry risk penalty {risk_profile['penalty']:.3f}")
    return reasons


def _candidate_risk_profile(candidate: dict[str, Any], criteria: dict[str, Any]) -> dict[str, Any]:
    elements = set(_candidate_elements(candidate))
    descriptors = _composition_descriptors(candidate)
    risk_flags: list[str] = []
    warnings: list[str] = []
    exclusion_reasons: list[str] = []
    penalty = 0.0

    excluded_elements = set(criteria.get("excludedElements") or [])
    flagged_elements = set(criteria.get("flaggedElements") or [])
    toxic_hits = sorted(elements.intersection(excluded_elements))
    flagged_hits = sorted(elements.intersection(flagged_elements))
    if toxic_hits:
        risk_flags.append(f"excluded-toxic-elements:{','.join(toxic_hits)}")
        warnings.append(f"Contains excluded toxic/high-risk element(s): {', '.join(toxic_hits)}.")
        penalty += 1.0
        if criteria.get("excludeToxicElements"):
            exclusion_reasons.append(f"excluded toxic/high-risk element(s): {', '.join(toxic_hits)}")
    if flagged_hits:
        risk_flags.append(f"flagged-risk-elements:{','.join(flagged_hits)}")
        warnings.append(f"Contains flagged risk element(s): {', '.join(flagged_hits)}.")
        penalty += 0.35

    h_fraction = float(descriptors.get("hydrogenAtomicFraction") or 0.0)
    max_h_fraction = float(criteria.get("maxHydrogenAtomicFraction") or 1.0)
    if h_fraction > max_h_fraction:
        risk_flags.append("hydrogen-rich-composition")
        warnings.append(f"Hydrogen atomic fraction {h_fraction:.3f} exceeds configured limit {max_h_fraction:.3f}.")
        penalty += 0.65
        if criteria.get("excludeRiskyChemistry"):
            exclusion_reasons.append("hydrogen-rich composition is outside the default inorganic solid-electrolyte screen")

    if criteria.get("filterMolecularSalts") and _looks_like_molecular_salt(candidate, elements):
        risk_flags.append("molecular-salt-or-oxidizer-like")
        warnings.append("Composition looks like a molecular salt or oxidizer rather than a ceramic/glassy solid-electrolyte framework.")
        penalty += 0.75
        if criteria.get("excludeRiskyChemistry"):
            exclusion_reasons.append("molecular-salt or oxidizer-like composition")

    if criteria.get("requiresLithium") and "Li" not in elements:
        risk_flags.append("no-lithium")
        warnings.append("No Li was detected in the candidate composition.")
        penalty += 1.0
        if criteria.get("excludeRiskyChemistry"):
            exclusion_reasons.append("no lithium detected")

    penalty = max(0.0, min(penalty, 1.0))
    return {
        "riskFlags": risk_flags,
        "warnings": warnings,
        "penalty": penalty,
        "excluded": bool(exclusion_reasons),
        "exclusionReasons": exclusion_reasons,
        "compositionDescriptors": descriptors,
    }


def _candidate_elements(candidate: dict[str, Any]) -> list[str]:
    elements = [str(item) for item in candidate.get("elements") or [] if item]
    if elements:
        return elements
    descriptors = _composition_descriptors(candidate)
    return [str(item) for item in descriptors.get("elements") or []]


def _composition_descriptors(candidate: dict[str, Any]) -> dict[str, Any]:
    formula = str(candidate.get("formula") or "")
    if not formula:
        return {"elements": [], "liAtomicFraction": 0.0, "hydrogenAtomicFraction": 0.0}
    if Composition is not None:
        try:
            composition = Composition(formula)
            total = float(composition.num_atoms)
            elements = [str(element.symbol) for element in composition.elements]
            return {
                "elements": elements,
                "numAtoms": total,
                "liAtomicFraction": round(float(composition.get_atomic_fraction("Li")), 6),
                "hydrogenAtomicFraction": round(float(composition.get_atomic_fraction("H")), 6),
            }
        except Exception:
            pass
    elements = [str(item) for item in candidate.get("elements") or []]
    return {
        "elements": elements,
        "liAtomicFraction": 1.0 / max(len(elements), 1) if "Li" in elements else 0.0,
        "hydrogenAtomicFraction": 1.0 / max(len(elements), 1) if "H" in elements else 0.0,
    }


def _looks_like_molecular_salt(candidate: dict[str, Any], elements: set[str]) -> bool:
    family = _infer_material_family(candidate)
    if family in {"garnet-oxide", "lgps-like-sulfide", "nasicon-oxide", "thiophosphate-sulfide", "zirconium-phosphate"}:
        return False
    if {"Li", "Cl", "O"}.issubset(elements) and not {"P", "S", "B", "Si", "Ge", "La", "Zr", "Ti", "Al", "Y", "In", "Sc"}.intersection(elements):
        return True
    if {"Li", "N", "H"}.issubset(elements):
        return True
    return False


def _family_prior_score(family: str) -> float:
    return {
        "lgps-like-sulfide": 1.00,
        "garnet-oxide": 0.95,
        "nasicon-oxide": 0.92,
        "thiophosphate-sulfide": 0.90,
        "halide": 0.88,
        "zirconium-phosphate": 0.78,
        "lithium-containing": 0.55,
        "generic": 0.40,
    }.get(family, 0.45)


def _range_score(value: Any, lower: float, upper: float) -> float:
    if value is None:
        return 0.2
    try:
        numeric = float(value)
    except Exception:
        return 0.2
    if lower <= numeric <= upper:
        return 1.0
    if numeric < lower:
        return max(0.0, numeric / lower) if lower > 0 else 1.0
    if upper <= 0:
        return 1.0
    return max(0.0, 1.0 - min((numeric - upper) / upper, 1.0))


def _apply_diversity_controls(ranked: list[dict[str, Any]], criteria: dict[str, Any]) -> list[dict[str, Any]]:
    diversify_by = str(criteria.get("diversifyBy") or "none").lower()
    max_per_formula = int(criteria.get("maxPerFormula") or 0)
    max_per_family = int(criteria.get("maxPerFamily") or 0)
    if diversify_by == "none" and max_per_formula <= 0 and max_per_family <= 0:
        return ranked

    formula_seen: defaultdict[str, int] = defaultdict(int)
    family_seen: defaultdict[str, int] = defaultdict(int)
    selected: list[dict[str, Any]] = []
    for candidate in ranked:
        formula_group = str(candidate.get("duplicateGroup") or _formula_group(candidate))
        family = str(candidate.get("family") or _infer_material_family(candidate))
        formula_limited = max_per_formula > 0 and formula_seen[formula_group] >= max_per_formula
        family_limited = max_per_family > 0 and family_seen[family] >= max_per_family
        if formula_limited or family_limited:
            continue
        selected.append(candidate)
        formula_seen[formula_group] += 1
        family_seen[family] += 1
    return selected


def _diversity_report(original: list[dict[str, Any]], ranked: list[dict[str, Any]], criteria: dict[str, Any]) -> dict[str, Any]:
    original_formulas = Counter(_formula_group(candidate) for candidate in original)
    ranked_formulas = Counter(_formula_group(candidate) for candidate in ranked)
    return {
        "diversifyBy": criteria.get("diversifyBy"),
        "maxPerFormula": criteria.get("maxPerFormula"),
        "maxPerFamily": criteria.get("maxPerFamily"),
        "originalFormulaGroups": len(original_formulas),
        "rankedFormulaGroups": len(ranked_formulas),
        "excludedByDiversity": max(0, len(original) - len(ranked)),
        "largestOriginalFormulaGroup": max(original_formulas.values()) if original_formulas else 0,
    }


def _ranking_warnings(
    original: list[dict[str, Any]],
    ranked: list[dict[str, Any]],
    criteria: dict[str, Any],
    excluded_candidates: list[dict[str, Any]] | None = None,
) -> list[str]:
    warnings = []
    formula_counts = Counter(_formula_group(candidate) for candidate in original)
    largest_group = max(formula_counts.values()) if formula_counts else 0
    if largest_group > 1:
        warnings.append("Candidate pool contains repeated formulas; use diversity controls for research shortlists.")
    if criteria.get("preset") == "solid-electrolyte":
        warnings.append("Solid-electrolyte preset is a proxy screen and does not compute ionic conductivity, migration barriers, or electrochemical windows.")
    if len(ranked) < len(original) and (criteria.get("maxPerFormula") or criteria.get("maxPerFamily")):
        warnings.append("Some high raw-score candidates were excluded by formula/family diversity controls.")
    if excluded_candidates:
        warnings.append(f"{len(excluded_candidates)} candidate(s) were excluded by chemistry risk filters.")
    if _score_saturated(ranked):
        warnings.append("Several candidates still have nearly saturated primary scores; inspect secondaryScore and riskProfile for ordering.")
    return warnings


def _score_saturated(ranked: list[dict[str, Any]]) -> bool:
    saturated = [candidate for candidate in ranked if float(candidate.get("primaryScore") or candidate.get("score") or 0) >= 0.999]
    return len(saturated) >= 3


def _write_candidate_table_artifacts(ranked: list[dict[str, Any]], artifact_dir: Path, prefix: str = "candidate-ranking") -> list[str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    csv_path = artifact_dir / f"{prefix}.csv"
    jsonl_path = artifact_dir / f"{prefix}.jsonl"
    fields = [
        "rank",
        "rawRank",
        "materialId",
        "formula",
        "family",
        "spacegroup",
        "energyAboveHullEv",
        "bandGapEv",
        "densityGcm3",
        "score",
        "primaryScore",
        "secondaryScore",
        "riskPenalty",
        "stabilityComponent",
        "bandGapComponent",
        "densityComponent",
        "riskFlags",
        "liAtomicFraction",
        "hydrogenAtomicFraction",
        "duplicateGroup",
        "duplicateCount",
        "screeningLevel",
        "materialsProjectUrl",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for candidate in ranked:
            weighted = ((candidate.get("scoreComponents") or {}).get("weighted") or {})
            writer.writerow({
                "rank": candidate.get("rank"),
                "rawRank": candidate.get("rawRank"),
                "materialId": candidate.get("materialId"),
                "formula": candidate.get("formula"),
                "family": candidate.get("family"),
                "spacegroup": candidate.get("spacegroup"),
                "energyAboveHullEv": candidate.get("energyAboveHullEv"),
                "bandGapEv": candidate.get("bandGapEv"),
                "densityGcm3": candidate.get("densityGcm3"),
                "score": candidate.get("score"),
                "primaryScore": candidate.get("primaryScore"),
                "secondaryScore": candidate.get("secondaryScore"),
                "riskPenalty": candidate.get("riskPenalty"),
                "stabilityComponent": weighted.get("stability"),
                "bandGapComponent": weighted.get("bandGap"),
                "densityComponent": weighted.get("density"),
                "riskFlags": ",".join(((candidate.get("riskProfile") or {}).get("riskFlags") or [])),
                "liAtomicFraction": ((candidate.get("compositionDescriptors") or {}).get("liAtomicFraction")),
                "hydrogenAtomicFraction": ((candidate.get("compositionDescriptors") or {}).get("hydrogenAtomicFraction")),
                "duplicateGroup": candidate.get("duplicateGroup"),
                "duplicateCount": candidate.get("duplicateCount"),
                "screeningLevel": candidate.get("screeningLevel"),
                "materialsProjectUrl": candidate.get("materialsProjectUrl"),
            })
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for candidate in ranked:
            handle.write(json.dumps(candidate, sort_keys=True) + "\n")
    return [str(csv_path), str(jsonl_path)]


def _infer_material_family(candidate: dict[str, Any]) -> str:
    formula = str(candidate.get("formula") or "").lower()
    elements = {str(item) for item in candidate.get("elements") or []}
    if {"Li", "La", "Zr", "O"}.issubset(elements):
        return "garnet-oxide"
    if {"Li", "Ge", "P", "S"}.issubset(elements):
        return "lgps-like-sulfide"
    if {"Li", "P", "S"}.issubset(elements):
        return "thiophosphate-sulfide"
    if {"Li", "Al", "Ti", "P", "O"}.issubset(elements):
        return "nasicon-oxide"
    if {"Li", "Zr", "P", "O"}.issubset(elements):
        return "zirconium-phosphate"
    if {"Li", "Cl"}.issubset(elements) or {"Li", "Br"}.issubset(elements) or {"Li", "I"}.issubset(elements):
        return "halide"
    if "li" in formula:
        return "lithium-containing"
    return "generic"


def _formula_group(candidate: dict[str, Any]) -> str:
    return str(candidate.get("formula") or candidate.get("materialId") or "unknown").replace(" ", "")


def _stability_score(energy_above_hull: Any) -> float:
    if energy_above_hull is None:
        return 0.2
    try:
        value = float(energy_above_hull)
    except Exception:
        return 0.2
    return max(0.0, 1.0 - min(value, 0.2) / 0.2)


def _target_score(value: Any, target: float) -> float:
    if value is None:
        return 0.2
    try:
        numeric = float(value)
    except Exception:
        return 0.2
    if target <= 0:
        return 1.0
    delta = abs(numeric - target)
    return max(0.0, 1.0 - min(delta / target, 1.0))


def _minimum_score(value: Any, minimum: float) -> float:
    if value is None:
        return 0.2
    try:
        numeric = float(value)
    except Exception:
        return 0.2
    if minimum <= 0:
        return 1.0
    return max(0.0, min(numeric / minimum, 1.0))


def _write_json(payload: dict[str, Any]) -> int:
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
