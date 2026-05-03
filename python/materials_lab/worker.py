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
from .plotting import write_candidate_score_plot, write_domain_evidence_plot, write_metric_bar_chart
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
    evidence_plot_path = write_domain_evidence_plot(ranked, str(artifact_dir / "domain-evidence.png"))
    table_paths = _write_candidate_table_artifacts(ranked, artifact_dir)
    warnings = _ranking_warnings(rankable_candidates, ranked, merged_criteria, excluded_candidates)
    if plot_path is None:
        warnings.append("Candidate ranking plot was skipped because matplotlib is unavailable.")
    if evidence_plot_path is None:
        warnings.append("Domain evidence plot was skipped because matplotlib is unavailable or evidence scores were unavailable.")

    data = {
        "ranked": ranked,
        "criteria": merged_criteria,
        "plotPath": plot_path,
        "evidencePlotPath": evidence_plot_path,
        "tablePaths": table_paths,
        "screeningLevel": merged_criteria["screeningLevel"],
        "diversity": _diversity_report(rankable_candidates, ranked, merged_criteria),
        "domainCoverage": _domain_coverage_report(ranked),
        "excludedCandidates": excluded_candidates,
    }
    return success(
        action="compare_candidates",
        request_id=request_id,
        summary=f"Ranked {len(ranked)} candidate materials.",
        data=data,
        artifacts=[artifact for artifact in [plot_path, evidence_plot_path, *table_paths] if artifact],
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
    family_counts = Counter(_infer_material_family(candidate, criteria) for candidate in candidates)
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
        evidence_weight = max(0.0, min(float(criteria.get("evidenceWeight") or 0.0), 0.35))
        primary_scale = max(0.0, 1.0 - secondary_weight - evidence_weight)
        family = _infer_material_family(candidate, criteria)
        domain_evidence = _domain_evidence_profile(
            candidate,
            criteria,
            family=family,
            risk_profile=risk_profile,
            raw_scores={"stability": stability, "bandGap": band_gap, "density": density, "secondary": secondary["score"]},
        )
        weighted = {
            "stability": round(stability * stability_weight * primary_scale, 6),
            "bandGap": round(band_gap * band_gap_weight * primary_scale, 6),
            "density": round(density * density_weight * primary_scale, 6),
            "secondary": round(secondary["score"] * secondary_weight, 6),
            "domainEvidence": round(domain_evidence["score"] * evidence_weight, 6),
        }
        primary_score = stability * stability_weight + band_gap * band_gap_weight + density * density_weight
        score = _final_score(primary_score, secondary["score"], domain_evidence["score"], risk_profile["penalty"], criteria)
        formula_group = _formula_group(candidate)
        reasons = _score_reasons(stability, band_gap, density, secondary, domain_evidence, risk_profile, criteria)
        warnings = list(candidate.get("warnings") or [])
        if formula_counts[formula_group] > 1:
            warnings.append(f"Duplicate reduced-formula group appears {formula_counts[formula_group]} times.")
        if family_counts[family] > 1:
            warnings.append(f"Material family '{family}' appears {family_counts[family]} times in the candidate pool.")
        warnings.extend(risk_profile["warnings"])
        warnings.extend(domain_evidence["warnings"])
        enriched = dict(candidate)
        enriched["score"] = round(score, 6)
        enriched["primaryScore"] = round(primary_score, 6)
        enriched["secondaryScore"] = round(secondary["score"], 6)
        enriched["domainEvidenceScore"] = round(domain_evidence["score"], 6)
        enriched["riskPenalty"] = round(risk_profile["penalty"], 6)
        enriched["scoreComponents"] = {
            "raw": {
                "stability": round(stability, 6),
                "bandGap": round(band_gap, 6),
                "density": round(density, 6),
                "secondary": round(secondary["score"], 6),
                "domainEvidence": round(domain_evidence["score"], 6),
                "riskPenalty": round(risk_profile["penalty"], 6),
            },
            "weighted": weighted,
            "secondary": secondary["components"],
            "domainEvidence": domain_evidence["components"],
        }
        enriched["reasons"] = reasons
        enriched["warnings"] = warnings
        enriched["riskProfile"] = risk_profile
        enriched["compositionDescriptors"] = risk_profile["compositionDescriptors"]
        enriched["domainEvidence"] = domain_evidence
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
            item.get("domainEvidenceScore", 0),
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
    preset = _normalize_preset(criteria.get("preset"))
    if preset == "solid-electrolyte":
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
            "evidenceWeight": 0.10,
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
    elif preset == "high-k-dielectric":
        defaults = {
            "preset": "high-k-dielectric",
            "screeningLevel": "proxy-screen",
            "stabilityWeight": 0.45,
            "bandGapWeight": 0.40,
            "densityWeight": 0.15,
            "bandGapScoringMode": "target",
            "minimumBandGapEv": 2.0,
            "bandGapTargetEv": 5.5,
            "densityScoringMode": "target",
            "densityTargetGcm3": 6.0,
            "secondaryWeight": 0.06,
            "evidenceWeight": 0.12,
            "riskPenaltyWeight": 0.20,
            "preferredBandGapEv": 5.5,
            "preferredLiFractionMin": 0.0,
            "preferredLiFractionMax": 1.0,
            "excludeToxicElements": True,
            "excludeRiskyChemistry": True,
            "filterMolecularSalts": False,
            "requiresLithium": False,
            "excludedElements": ["Cd", "Hg", "Pb", "Tl", "Th", "U"],
            "flaggedElements": ["As", "Be", "Cr", "Sb", "Se"],
            "maxHydrogenAtomicFraction": 0.05,
            "diversifyBy": "formula",
            "maxPerFormula": 1,
            "maxPerFamily": 8,
        }
    elif preset == "photovoltaic-absorber":
        defaults = {
            "preset": "photovoltaic-absorber",
            "screeningLevel": "proxy-screen",
            "stabilityWeight": 0.45,
            "bandGapWeight": 0.45,
            "densityWeight": 0.10,
            "bandGapScoringMode": "target",
            "minimumBandGapEv": 0.7,
            "bandGapTargetEv": 1.45,
            "densityScoringMode": "advisory",
            "densityTargetGcm3": 5.0,
            "secondaryWeight": 0.08,
            "evidenceWeight": 0.12,
            "riskPenaltyWeight": 0.20,
            "preferredBandGapEv": 1.45,
            "preferredLiFractionMin": 0.0,
            "preferredLiFractionMax": 1.0,
            "excludeToxicElements": False,
            "excludeRiskyChemistry": True,
            "filterMolecularSalts": True,
            "requiresLithium": False,
            "excludedElements": ["Hg", "Tl", "Th", "U"],
            "flaggedElements": ["As", "Cd", "Cr", "Pb", "Sb", "Se"],
            "maxHydrogenAtomicFraction": 0.10,
            "diversifyBy": "formula",
            "maxPerFormula": 1,
            "maxPerFamily": 4,
        }
    elif preset == "thermoelectric":
        defaults = {
            "preset": "thermoelectric",
            "screeningLevel": "proxy-screen",
            "stabilityWeight": 0.50,
            "bandGapWeight": 0.30,
            "densityWeight": 0.20,
            "bandGapScoringMode": "target",
            "minimumBandGapEv": 0.0,
            "bandGapTargetEv": 0.35,
            "densityScoringMode": "target",
            "densityTargetGcm3": 7.0,
            "secondaryWeight": 0.10,
            "evidenceWeight": 0.12,
            "riskPenaltyWeight": 0.15,
            "preferredBandGapEv": 0.35,
            "preferredLiFractionMin": 0.0,
            "preferredLiFractionMax": 1.0,
            "excludeToxicElements": False,
            "excludeRiskyChemistry": False,
            "filterMolecularSalts": False,
            "requiresLithium": False,
            "excludedElements": ["Hg", "Tl", "Th", "U"],
            "flaggedElements": ["As", "Cd", "Pb", "Sb", "Se"],
            "maxHydrogenAtomicFraction": 0.05,
            "diversifyBy": "formula",
            "maxPerFormula": 1,
            "maxPerFamily": 4,
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
            "evidenceWeight": 0.0,
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
        "evidenceWeight",
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


def _normalize_preset(value: Any) -> str:
    preset = str(value or "generic").strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "solid-electrolyte": "solid-electrolyte",
        "battery-electrolyte": "solid-electrolyte",
        "li-solid-electrolyte": "solid-electrolyte",
        "high-k": "high-k-dielectric",
        "high-k-dielectric": "high-k-dielectric",
        "gate-dielectric": "high-k-dielectric",
        "dielectric": "high-k-dielectric",
        "photovoltaic": "photovoltaic-absorber",
        "photovoltaic-absorber": "photovoltaic-absorber",
        "solar-absorber": "photovoltaic-absorber",
        "pv-absorber": "photovoltaic-absorber",
        "thermoelectric": "thermoelectric",
        "thermoelectric-material": "thermoelectric",
        "generic": "generic",
    }
    return aliases.get(preset, "generic")


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
                "family": _infer_material_family(candidate, criteria),
                "riskFlags": risk_profile["riskFlags"],
                "exclusionReasons": risk_profile["exclusionReasons"],
            })
            continue
        rankable.append(candidate)
    return rankable, excluded


def _final_score(primary_score: float, secondary_score: float, evidence_score: float, risk_penalty: float, criteria: dict[str, Any]) -> float:
    secondary_weight = max(0.0, min(float(criteria.get("secondaryWeight") or 0.0), 0.5))
    evidence_weight = max(0.0, min(float(criteria.get("evidenceWeight") or 0.0), 0.35))
    risk_weight = max(0.0, float(criteria.get("riskPenaltyWeight") or 0.0))
    score = primary_score * max(0.0, 1.0 - secondary_weight - evidence_weight)
    score += secondary_score * secondary_weight
    score += evidence_score * evidence_weight
    score -= risk_penalty * risk_weight
    return max(0.0, min(score, 1.0))


def _secondary_score(candidate: dict[str, Any], criteria: dict[str, Any], risk_profile: dict[str, Any]) -> dict[str, Any]:
    family = _infer_material_family(candidate, criteria)
    descriptors = risk_profile["compositionDescriptors"]
    band_gap_margin = _target_score(candidate.get("bandGapEv"), float(criteria.get("preferredBandGapEv") or 4.0))
    preset = str(criteria.get("preset") or "generic")
    family_prior = _family_prior_score(family, preset)
    chemistry = 1.0 - min(risk_profile["penalty"], 1.0)

    if preset == "solid-electrolyte":
        li_fraction_score = _range_score(
            descriptors.get("liAtomicFraction"),
            float(criteria.get("preferredLiFractionMin") or 0.0),
            float(criteria.get("preferredLiFractionMax") or 1.0),
        )
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

    if preset == "high-k-dielectric":
        oxide_score = 1.0 if descriptors.get("oxygenAtomicFraction", 0) > 0.35 else 0.35
        density_score = _target_score(candidate.get("densityGcm3"), float(criteria.get("densityTargetGcm3") or 6.0))
        components = {
            "bandGapMargin": round(band_gap_margin, 6),
            "oxideFramework": round(oxide_score, 6),
            "densityAlignment": round(density_score, 6),
            "familyPrior": round(family_prior, 6),
            "chemistryRisk": round(chemistry, 6),
        }
        score = (
            band_gap_margin * 0.30
            + oxide_score * 0.20
            + density_score * 0.20
            + family_prior * 0.20
            + chemistry * 0.10
        )
        return {"score": max(0.0, min(score, 1.0)), "components": components}

    if preset == "photovoltaic-absorber":
        absorber_score = max(
            descriptors.get("chalcogenideAtomicFraction", 0.0),
            descriptors.get("halogenAtomicFraction", 0.0) * 0.8,
            descriptors.get("oxygenAtomicFraction", 0.0) * 0.55,
        )
        components = {
            "bandGapMargin": round(band_gap_margin, 6),
            "absorberChemistry": round(absorber_score, 6),
            "familyPrior": round(family_prior, 6),
            "chemistryRisk": round(chemistry, 6),
        }
        score = (
            band_gap_margin * 0.40
            + absorber_score * 0.20
            + family_prior * 0.25
            + chemistry * 0.15
        )
        return {"score": max(0.0, min(score, 1.0)), "components": components}

    if preset == "thermoelectric":
        heavy_score = descriptors.get("heavyAtomicFraction", 0.0)
        narrow_gap_score = band_gap_margin
        components = {
            "bandGapMargin": round(narrow_gap_score, 6),
            "heavyElementFraction": round(heavy_score, 6),
            "familyPrior": round(family_prior, 6),
            "chemistryRisk": round(chemistry, 6),
        }
        score = (
            narrow_gap_score * 0.35
            + heavy_score * 0.25
            + family_prior * 0.25
            + chemistry * 0.15
        )
        return {"score": max(0.0, min(score, 1.0)), "components": components}

    domain_score = _domain_descriptor_score(descriptors, preset)
    components = {
        "bandGapMargin": round(band_gap_margin, 6),
        "domainDescriptor": round(domain_score, 6),
        "familyPrior": round(family_prior, 6),
        "chemistryRisk": round(chemistry, 6),
    }
    score = (
        band_gap_margin * 0.25
        + domain_score * 0.30
        + family_prior * 0.30
        + chemistry * 0.15
    )
    return {"score": max(0.0, min(score, 1.0)), "components": components}


def _score_reasons(
    stability: float,
    band_gap: float,
    density: float,
    secondary: dict[str, Any],
    domain_evidence: dict[str, Any],
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
        descriptor_value = _secondary_descriptor_value(components)
        reasons.append(
            "secondary tie-breaker "
            f"{secondary['score']:.3f} "
            f"(domain descriptor {descriptor_value:.3f}, "
            f"family prior {components.get('familyPrior', 0):.3f}, "
            f"gap margin {components.get('bandGapMargin', 0):.3f})"
        )
    if float(criteria.get("evidenceWeight") or 0.0) > 0:
        reasons.append(
            "research evidence "
            f"{domain_evidence['score']:.3f} "
            f"({domain_evidence.get('tier', 'unknown')}, "
            f"{domain_evidence.get('sourceLevel', 'proxy')})"
        )
    if risk_profile["penalty"] > 0:
        reasons.append(f"chemistry risk penalty {risk_profile['penalty']:.3f}")
    return reasons


def _secondary_descriptor_value(components: dict[str, Any]) -> float:
    for key in ["liFraction", "domainDescriptor", "oxideFramework", "absorberChemistry", "heavyElementFraction"]:
        value = components.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0


def _domain_evidence_profile(
    candidate: dict[str, Any],
    criteria: dict[str, Any],
    *,
    family: str,
    risk_profile: dict[str, Any],
    raw_scores: dict[str, float],
) -> dict[str, Any]:
    preset = str(criteria.get("preset") or "generic")
    descriptors = risk_profile.get("compositionDescriptors") or {}
    elements = set(str(item) for item in descriptors.get("elements") or _candidate_elements(candidate))

    if preset == "solid-electrolyte":
        profile = _solid_electrolyte_evidence(candidate, descriptors, risk_profile, raw_scores)
    elif preset == "high-k-dielectric":
        profile = _high_k_evidence(candidate, descriptors, elements, family, risk_profile, raw_scores)
    elif preset == "photovoltaic-absorber":
        profile = _photovoltaic_evidence(candidate, descriptors, elements, family, risk_profile, raw_scores)
    elif preset == "thermoelectric":
        profile = _thermoelectric_evidence(candidate, descriptors, elements, family, risk_profile, raw_scores)
    else:
        profile = _generic_evidence(candidate, risk_profile, raw_scores)

    profile["preset"] = preset
    profile["score"] = round(float(profile.get("score") or 0.0), 6)
    profile["components"] = {
        str(gate["id"]): round(float(gate.get("score") or 0.0), 6)
        for gate in profile.get("gates") or []
    }
    profile["passCount"] = sum(1 for gate in profile.get("gates") or [] if gate.get("status") == "pass")
    profile["watchCount"] = sum(1 for gate in profile.get("gates") or [] if gate.get("status") == "watch")
    profile["failCount"] = sum(1 for gate in profile.get("gates") or [] if gate.get("status") == "fail")
    profile["missingCount"] = len(profile.get("missingProperties") or [])
    profile["tier"] = _evidence_tier(profile)
    profile["sourceLevel"] = _evidence_source_level(profile.get("gates") or [])
    profile["interpretation"] = _evidence_interpretation(profile, candidate, family)
    return profile


def _solid_electrolyte_evidence(
    candidate: dict[str, Any],
    descriptors: dict[str, Any],
    risk_profile: dict[str, Any],
    raw_scores: dict[str, float],
) -> dict[str, Any]:
    ionic_conductivity = _candidate_number(candidate, "ionicConductivityScm", "ionic_conductivity_scm")
    migration_barrier = _candidate_number(candidate, "migrationBarrierEv", "migration_barrier_ev")
    electrochemical_window = _candidate_number(candidate, "electrochemicalWindowV", "electrochemical_window_v")
    li_fraction = float(descriptors.get("liAtomicFraction") or 0.0)
    framework_score = max(
        float(descriptors.get("oxygenAtomicFraction") or 0.0) * 0.85,
        float(descriptors.get("chalcogenideAtomicFraction") or 0.0),
        float(descriptors.get("halogenAtomicFraction") or 0.0) * 0.75,
    )
    gates = [
        _evidence_gate("phaseStability", "Phase stability", candidate.get("energyAboveHullEv"), raw_scores["stability"], "mp-summary", "<=0.05 eV preferred"),
        _evidence_gate("wideGapProxy", "Electronic insulation proxy", candidate.get("bandGapEv"), raw_scores["bandGap"], "mp-summary", ">=2 eV minimum proxy"),
        _evidence_gate("liContent", "Li carrier content", li_fraction, _range_score(li_fraction, 0.10, 0.45), "composition", "0.10-0.45 Li atomic fraction"),
        _evidence_gate("frameworkChemistry", "Framework chemistry", None, framework_score, "composition-proxy", "oxide/sulfide/halide framework proxy"),
        _evidence_gate(
            "ionicConductivity",
            "Ionic conductivity",
            ionic_conductivity,
            _minimum_score(ionic_conductivity, 1e-4) if ionic_conductivity is not None else 0.35,
            "property" if ionic_conductivity is not None else "missing-proxy",
            ">=1e-4 S/cm screen; >=1e-3 S/cm target",
        ),
        _evidence_gate(
            "migrationBarrier",
            "Li migration barrier",
            migration_barrier,
            _maximum_score(migration_barrier, 0.50, 0.50) if migration_barrier is not None else 0.35,
            "property" if migration_barrier is not None else "missing-proxy",
            "<=0.50 eV preferred",
        ),
        _evidence_gate(
            "electrochemicalWindow",
            "Electrochemical window",
            electrochemical_window,
            _minimum_score(electrochemical_window, 4.0) if electrochemical_window is not None else 0.30,
            "property" if electrochemical_window is not None else "missing-proxy",
            ">=4 V preferred",
        ),
    ]
    missing = _missing_properties(
        {
            "ionicConductivityScm": ionic_conductivity,
            "migrationBarrierEv": migration_barrier,
            "electrochemicalWindowV": electrochemical_window,
            "interfaceStability": _candidate_number(candidate, "interfaceReactionEnergyEv", "interfaceStabilityEv"),
        }
    )
    return {
        "score": _weighted_gate_score(gates, [0.16, 0.12, 0.14, 0.12, 0.18, 0.14, 0.14]),
        "gates": gates,
        "missingProperties": missing,
        "nextCalculations": [
            "NEB or bond-valence migration barrier for mobile Li pathways",
            "AIMD ionic conductivity at target temperature",
            "grand-potential electrochemical window and electrode interface reactions",
            "phonon/dynamic stability check for shortlisted phases",
        ],
        "warnings": _evidence_warnings(risk_profile, missing),
    }


def _high_k_evidence(
    candidate: dict[str, Any],
    descriptors: dict[str, Any],
    elements: set[str],
    family: str,
    risk_profile: dict[str, Any],
    raw_scores: dict[str, float],
) -> dict[str, Any]:
    dielectric_total = _candidate_number(candidate, "dielectricTotal", "dielectricTotalK", "staticDielectric", "dielectricConstant")
    dielectric_electronic = _candidate_number(candidate, "dielectricElectronic", "electronicDielectric")
    electron_offset = _candidate_number(candidate, "bandOffsetElectronEv", "conductionBandOffsetEv")
    hole_offset = _candidate_number(candidate, "bandOffsetHoleEv", "valenceBandOffsetEv")
    dielectric_score = _minimum_score(dielectric_total, 15.0) if dielectric_total is not None else _high_k_chemistry_score(elements, descriptors, family)
    dielectric_label = "Static dielectric response" if dielectric_total is not None else "High-k chemistry proxy"
    dielectric_source = "property" if dielectric_total is not None else "composition-proxy"
    dielectric_threshold = "k_total >=15 preferred" if dielectric_total is not None else "Hf/Zr/Ti/Ta/Nb/rare-earth/perovskite oxide proxy"
    offset_score = _offset_score(electron_offset, hole_offset)
    interface_score = _high_k_interface_score(elements, family)
    gates = [
        _evidence_gate("phaseStability", "Phase stability", candidate.get("energyAboveHullEv"), _maximum_score(candidate.get("energyAboveHullEv"), 0.05, 0.15), "mp-summary", "<=0.05 eV preferred"),
        _evidence_gate("wideGap", "Leakage band gap proxy", candidate.get("bandGapEv"), _minimum_score(candidate.get("bandGapEv"), 5.0), "mp-summary", ">=5 eV preferred"),
        _evidence_gate(
            "dielectricResponse",
            dielectric_label,
            dielectric_total,
            dielectric_score,
            dielectric_source,
            dielectric_threshold,
        ),
        _evidence_gate("interfaceCompatibility", "Interface compatibility proxy", None, interface_score, "composition-proxy", "Si/channel interface risk proxy"),
        _evidence_gate("bandOffset", "Band offset leakage guard", _first_present(electron_offset, hole_offset), offset_score, "property" if electron_offset is not None or hole_offset is not None else "missing-proxy", "electron/hole offset >=1 eV"),
        _evidence_gate("densityPolarizability", "Density/polarizability proxy", candidate.get("densityGcm3"), raw_scores["density"], "mp-summary", "density near high-k oxide target"),
    ]
    missing = _missing_properties(
        {
            "dielectricTotal": dielectric_total,
            "dielectricElectronic": dielectric_electronic,
            "bandOffsetElectronEv": electron_offset,
            "bandOffsetHoleEv": hole_offset,
            "interfaceReactionEnergyEv": _candidate_number(candidate, "interfaceReactionEnergyEv"),
            "phononStability": _candidate_number(candidate, "imaginaryPhononFrequencyCm1", "phononStability"),
        }
    )
    return {
        "score": _weighted_gate_score(gates, [0.17, 0.18, 0.24, 0.16, 0.15, 0.10]),
        "gates": gates,
        "missingProperties": missing,
        "nextCalculations": [
            "DFPT dielectric tensor with electronic and ionic components",
            "band alignment against Si or the intended channel material",
            "interface reaction energy and oxygen vacancy formation energy",
            "phonon stability and leakage/effective-mass follow-up for top candidates",
        ],
        "warnings": _evidence_warnings(risk_profile, missing),
    }


def _photovoltaic_evidence(
    candidate: dict[str, Any],
    descriptors: dict[str, Any],
    elements: set[str],
    family: str,
    risk_profile: dict[str, Any],
    raw_scores: dict[str, float],
) -> dict[str, Any]:
    absorption = _candidate_number(candidate, "absorptionCoefficientCm1", "absorptionCm1")
    direct_gap = _candidate_number(candidate, "directBandGapEv", "direct_gap_ev")
    electron_mass = _candidate_number(candidate, "effectiveMassElectron", "electronEffectiveMass")
    hole_mass = _candidate_number(candidate, "effectiveMassHole", "holeEffectiveMass")
    gap_value = direct_gap if direct_gap is not None else candidate.get("bandGapEv")
    absorber_score = max(
        float(descriptors.get("chalcogenideAtomicFraction") or 0.0),
        float(descriptors.get("halogenAtomicFraction") or 0.0) * 0.85,
        float(descriptors.get("oxygenAtomicFraction") or 0.0) * 0.50,
    )
    transport_score = _carrier_mass_score(electron_mass, hole_mass)
    gates = [
        _evidence_gate("phaseStability", "Phase stability", candidate.get("energyAboveHullEv"), _maximum_score(candidate.get("energyAboveHullEv"), 0.05, 0.20), "mp-summary", "<=0.05 eV preferred"),
        _evidence_gate("opticalGap", "Optical gap alignment", gap_value, _target_score(gap_value, 1.45), "property" if direct_gap is not None else "mp-summary", "near 1.45 eV"),
        _evidence_gate(
            "absorption",
            "Absorption strength",
            absorption,
            _minimum_score(absorption, 1e4) if absorption is not None else absorber_score,
            "property" if absorption is not None else "composition-proxy",
            ">=1e4 cm^-1 preferred",
        ),
        _evidence_gate("absorberChemistry", "Absorber chemistry", None, absorber_score, "composition-proxy", "chalcogenide/halide/oxide absorber proxy"),
        _evidence_gate("carrierTransport", "Carrier transport proxy", _first_present(electron_mass, hole_mass), transport_score, "property" if electron_mass is not None or hole_mass is not None else "missing-proxy", "low balanced effective masses"),
        _evidence_gate("chemistryRisk", "Toxicity/supply risk", None, max(0.0, 1.0 - float(risk_profile.get("penalty") or 0.0)), "composition", "risk flags penalized"),
    ]
    missing = _missing_properties(
        {
            "absorptionCoefficientCm1": absorption,
            "directBandGapEv": direct_gap,
            "bandEdgeAlignment": _candidate_number(candidate, "cbmEv", "vbmEv"),
            "defectTolerance": _candidate_number(candidate, "defectToleranceScore"),
            "effectiveMassElectron": electron_mass,
            "effectiveMassHole": hole_mass,
        }
    )
    warnings = _evidence_warnings(risk_profile, missing)
    if "Pb" in elements or "Cd" in elements:
        warnings.append("PV absorber contains Pb or Cd; performance may be plausible but deployment risk needs explicit treatment.")
    if family == "oxide-absorber":
        warnings.append("Oxide absorber candidates often require absorption/defect validation because wide or indirect gaps are common.")
    return {
        "score": _weighted_gate_score(gates, [0.16, 0.24, 0.20, 0.12, 0.14, 0.14]),
        "gates": gates,
        "missingProperties": missing,
        "nextCalculations": [
            "optical absorption spectrum and direct/indirect gap confirmation",
            "absolute band-edge alignment for target device stack",
            "dominant defect formation energies and non-radiative recombination risk",
            "carrier effective masses and exciton binding energy for top candidates",
        ],
        "warnings": warnings,
    }


def _thermoelectric_evidence(
    candidate: dict[str, Any],
    descriptors: dict[str, Any],
    elements: set[str],
    family: str,
    risk_profile: dict[str, Any],
    raw_scores: dict[str, float],
) -> dict[str, Any]:
    seebeck = _candidate_number(candidate, "seebeckUvK", "seebeck_uV_K")
    power_factor = _candidate_number(candidate, "powerFactorUwCmK2", "powerFactor")
    thermal_conductivity = _candidate_number(candidate, "latticeThermalConductivityWmK", "kappaLatticeWmK")
    heavy_score = float(descriptors.get("heavyAtomicFraction") or 0.0)
    complexity_score = min(1.0, float(descriptors.get("numElements") or 0.0) / 4.0)
    transport_score = _transport_property_score(seebeck, power_factor, thermal_conductivity)
    gates = [
        _evidence_gate("phaseStability", "Phase/metastability", candidate.get("energyAboveHullEv"), _maximum_score(candidate.get("energyAboveHullEv"), 0.08, 0.25), "mp-summary", "<=0.08 eV preferred"),
        _evidence_gate("narrowGap", "Narrow-gap electronic structure", candidate.get("bandGapEv"), _target_score(candidate.get("bandGapEv"), 0.35), "mp-summary", "near 0.35 eV"),
        _evidence_gate("heavyElements", "Heavy-element phonon proxy", None, heavy_score, "composition-proxy", "heavy atoms favor low lattice thermal conductivity"),
        _evidence_gate("structuralComplexity", "Complexity proxy", descriptors.get("numElements"), complexity_score, "composition-proxy", "multi-element complexity proxy"),
        _evidence_gate("transport", "Transport coefficients", _first_present(power_factor, seebeck, thermal_conductivity), transport_score, "property" if any(value is not None for value in [seebeck, power_factor, thermal_conductivity]) else "missing-proxy", "Seebeck/power factor/kappa"),
        _evidence_gate("chemistryRisk", "Chemistry risk", None, max(0.0, 1.0 - float(risk_profile.get("penalty") or 0.0)), "composition", "risk flags penalized"),
    ]
    missing = _missing_properties(
        {
            "seebeckUvK": seebeck,
            "powerFactorUwCmK2": power_factor,
            "latticeThermalConductivityWmK": thermal_conductivity,
            "carrierConcentrationCm3": _candidate_number(candidate, "carrierConcentrationCm3"),
            "phononStability": _candidate_number(candidate, "imaginaryPhononFrequencyCm1", "phononStability"),
        }
    )
    warnings = _evidence_warnings(risk_profile, missing)
    if "Pb" in elements:
        warnings.append("Pb-containing thermoelectrics need explicit toxicity and regulation handling even when transport proxies are strong.")
    if family == "oxide-thermoelectric":
        warnings.append("Oxide thermoelectrics can be robust but often need high-temperature transport validation.")
    return {
        "score": _weighted_gate_score(gates, [0.16, 0.20, 0.18, 0.12, 0.22, 0.12]),
        "gates": gates,
        "missingProperties": missing,
        "nextCalculations": [
            "Boltzmann transport for Seebeck, conductivity, and power factor versus carrier concentration",
            "lattice thermal conductivity or phonon scattering proxy",
            "dopability and defect compensation analysis",
            "high-temperature phase stability and oxidation risk checks",
        ],
        "warnings": warnings,
    }


def _generic_evidence(candidate: dict[str, Any], risk_profile: dict[str, Any], raw_scores: dict[str, float]) -> dict[str, Any]:
    gates = [
        _evidence_gate("phaseStability", "Phase stability", candidate.get("energyAboveHullEv"), raw_scores["stability"], "mp-summary", "lower eHull preferred"),
        _evidence_gate("bandGap", "Band gap criterion", candidate.get("bandGapEv"), raw_scores["bandGap"], "mp-summary", "configured criterion"),
        _evidence_gate("density", "Density criterion", candidate.get("densityGcm3"), raw_scores["density"], "mp-summary", "configured criterion"),
        _evidence_gate("chemistryRisk", "Chemistry risk", None, max(0.0, 1.0 - float(risk_profile.get("penalty") or 0.0)), "composition", "risk flags penalized"),
    ]
    return {
        "score": _weighted_gate_score(gates, [0.35, 0.25, 0.20, 0.20]),
        "gates": gates,
        "missingProperties": ["domain-specific-property-model"],
        "nextCalculations": ["select a domain preset and add domain-specific property calculations"],
        "warnings": _evidence_warnings(risk_profile, ["domain-specific-property-model"]),
    }


def _evidence_gate(id_: str, label: str, value: Any, score: float, source: str, threshold: str) -> dict[str, Any]:
    bounded = max(0.0, min(float(score), 1.0))
    if source == "missing-proxy":
        status = "missing"
    elif bounded >= 0.75:
        status = "pass"
    elif bounded >= 0.45:
        status = "watch"
    else:
        status = "fail"
    return {
        "id": id_,
        "label": label,
        "value": _json_scalar(value),
        "score": round(bounded, 6),
        "status": status,
        "source": source,
        "threshold": threshold,
    }


def _weighted_gate_score(gates: list[dict[str, Any]], weights: list[float]) -> float:
    if not gates:
        return 0.0
    normalized = weights[: len(gates)]
    if len(normalized) < len(gates):
        normalized.extend([1.0] * (len(gates) - len(normalized)))
    total = sum(normalized)
    if total <= 0:
        return 0.0
    return sum(float(gate.get("score") or 0.0) * weight for gate, weight in zip(gates, normalized)) / total


def _evidence_tier(profile: dict[str, Any]) -> str:
    score = float(profile.get("score") or 0.0)
    missing_count = len(profile.get("missingProperties") or [])
    fail_count = sum(1 for gate in profile.get("gates") or [] if gate.get("status") == "fail")
    property_gates = [gate for gate in profile.get("gates") or [] if gate.get("source") == "property"]
    if score >= 0.78 and fail_count == 0 and missing_count <= 2 and len(property_gates) >= 2:
        return "research-shortlist"
    if score >= 0.68 and fail_count <= 1:
        return "proxy-shortlist"
    if score >= 0.48:
        return "watchlist"
    if missing_count >= 4 and score < 0.55:
        return "insufficient-data"
    return "low-confidence"


def _evidence_source_level(gates: list[dict[str, Any]]) -> str:
    if not gates:
        return "none"
    property_count = sum(1 for gate in gates if gate.get("source") == "property")
    proxy_count = sum(1 for gate in gates if str(gate.get("source") or "").endswith("proxy") or gate.get("source") == "composition-proxy")
    if property_count >= max(2, len(gates) // 2):
        return "property-backed"
    if property_count > 0:
        return "mixed-property-proxy"
    if proxy_count:
        return "proxy-only"
    return "summary-only"


def _evidence_interpretation(profile: dict[str, Any], candidate: dict[str, Any], family: str) -> str:
    formula = candidate.get("formula") or candidate.get("materialId") or "candidate"
    tier = profile.get("tier", "unknown")
    score = float(profile.get("score") or 0.0)
    missing = profile.get("missingProperties") or []
    if missing:
        return f"{formula} is a {tier} candidate in the {family} family with evidence score {score:.3f}; missing {len(missing)} research-grade property check(s)."
    return f"{formula} is a {tier} candidate in the {family} family with evidence score {score:.3f}; no required evidence fields were missing."


def _evidence_warnings(risk_profile: dict[str, Any], missing: list[str]) -> list[str]:
    warnings = []
    if missing:
        warnings.append(f"Research evidence is incomplete; missing: {', '.join(missing[:5])}.")
    if risk_profile.get("riskFlags"):
        warnings.append("Chemistry risk flags are present and should be resolved before experimental prioritization.")
    return warnings


def _missing_properties(values: dict[str, Any]) -> list[str]:
    return [key for key, value in values.items() if value is None]


def _candidate_number(candidate: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = candidate.get(key)
        if isinstance(value, bool) or value is None:
            continue
        try:
            return float(value)
        except Exception:
            continue
    return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _json_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    try:
        return float(value)
    except Exception:
        return str(value)


def _maximum_score(value: Any, maximum: float, tolerance: float) -> float:
    if value is None:
        return 0.2
    try:
        numeric = float(value)
    except Exception:
        return 0.2
    if numeric <= maximum:
        return 1.0
    if tolerance <= 0:
        return 0.0
    return max(0.0, 1.0 - min((numeric - maximum) / tolerance, 1.0))


def _offset_score(electron_offset: float | None, hole_offset: float | None) -> float:
    values = [value for value in [electron_offset, hole_offset] if value is not None]
    if not values:
        return 0.30
    return min(_minimum_score(value, 1.0) for value in values)


def _carrier_mass_score(electron_mass: float | None, hole_mass: float | None) -> float:
    values = [value for value in [electron_mass, hole_mass] if value is not None]
    if not values:
        return 0.35
    scores = [_maximum_score(value, 0.50, 1.50) for value in values]
    imbalance = abs((electron_mass or values[0]) - (hole_mass or values[-1])) if len(values) == 2 else 0.25
    return max(0.0, min(sum(scores) / len(scores) - min(imbalance / 4.0, 0.20), 1.0))


def _transport_property_score(seebeck: float | None, power_factor: float | None, thermal_conductivity: float | None) -> float:
    scores = []
    if seebeck is not None:
        scores.append(_minimum_score(abs(seebeck), 150.0))
    if power_factor is not None:
        scores.append(_minimum_score(power_factor, 20.0))
    if thermal_conductivity is not None:
        scores.append(_maximum_score(thermal_conductivity, 2.0, 6.0))
    if not scores:
        return 0.35
    return sum(scores) / len(scores)


def _high_k_chemistry_score(elements: set[str], descriptors: dict[str, Any], family: str) -> float:
    strong_high_k_elements = {"Hf", "Zr", "Ti", "Ta", "Nb", "La", "Y", "Sr", "Ba"}
    low_k_network_formers = {"Al", "Si", "B", "P"}
    strong_hits = len(elements.intersection(strong_high_k_elements))
    low_k_hits = len(elements.intersection(low_k_network_formers))
    denominator = max(len(elements), 1)
    strong_fraction = strong_hits / denominator
    low_k_fraction = low_k_hits / denominator
    oxide_bonus = 0.15 if float(descriptors.get("oxygenAtomicFraction") or 0.0) > 0.35 else 0.0
    family_bonus = 0.14 if family in {"perovskite-oxide", "complex-oxide"} else 0.08 if family == "binary-oxide" else 0.0
    score = 0.22 + strong_fraction * 0.62 + oxide_bonus + family_bonus - low_k_fraction * 0.18
    if strong_hits == 0:
        score = min(score, 0.55)
    return max(0.0, min(score, 1.0))


def _high_k_interface_score(elements: set[str], family: str) -> float:
    if elements.intersection({"Hf", "Zr", "Al", "Si"}) and "O" in elements:
        return 0.85
    if family == "perovskite-oxide":
        return 0.65
    if elements.intersection({"Ti", "Ta", "La", "Y", "Sr", "Ba"}) and "O" in elements:
        return 0.60
    if "O" in elements:
        return 0.50
    return 0.25


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
        return _empty_composition_descriptors()
    if Composition is not None:
        try:
            composition = Composition(formula)
            total = float(composition.num_atoms)
            elements = [str(element.symbol) for element in composition.elements]
            fractions = {str(element.symbol): float(composition.get_atomic_fraction(element)) for element in composition.elements}
            heavy_fraction = sum(fraction for symbol, fraction in fractions.items() if _is_heavy_element(symbol))
            metal_fraction = sum(fraction for symbol, fraction in fractions.items() if _is_metal_symbol(symbol))
            return {
                "elements": elements,
                "numAtoms": total,
                "liAtomicFraction": round(float(composition.get_atomic_fraction("Li")), 6),
                "hydrogenAtomicFraction": round(float(composition.get_atomic_fraction("H")), 6),
                "oxygenAtomicFraction": round(float(composition.get_atomic_fraction("O")), 6),
                "halogenAtomicFraction": round(sum(fractions.get(symbol, 0.0) for symbol in ["F", "Cl", "Br", "I"]), 6),
                "chalcogenideAtomicFraction": round(sum(fractions.get(symbol, 0.0) for symbol in ["S", "Se", "Te"]), 6),
                "heavyAtomicFraction": round(heavy_fraction, 6),
                "metalAtomicFraction": round(metal_fraction, 6),
                "numElements": len(elements),
            }
        except Exception:
            pass
    elements = [str(item) for item in candidate.get("elements") or []]
    denominator = max(len(elements), 1)
    return {
        "elements": elements,
        "numAtoms": None,
        "liAtomicFraction": 1.0 / denominator if "Li" in elements else 0.0,
        "hydrogenAtomicFraction": 1.0 / denominator if "H" in elements else 0.0,
        "oxygenAtomicFraction": 1.0 / denominator if "O" in elements else 0.0,
        "halogenAtomicFraction": sum(1 for element in elements if element in {"F", "Cl", "Br", "I"}) / denominator,
        "chalcogenideAtomicFraction": sum(1 for element in elements if element in {"S", "Se", "Te"}) / denominator,
        "heavyAtomicFraction": sum(1 for element in elements if _is_heavy_element(element)) / denominator,
        "metalAtomicFraction": sum(1 for element in elements if _is_metal_symbol(element)) / denominator,
        "numElements": len(elements),
    }


def _empty_composition_descriptors() -> dict[str, Any]:
    return {
        "elements": [],
        "numAtoms": None,
        "liAtomicFraction": 0.0,
        "hydrogenAtomicFraction": 0.0,
        "oxygenAtomicFraction": 0.0,
        "halogenAtomicFraction": 0.0,
        "chalcogenideAtomicFraction": 0.0,
        "heavyAtomicFraction": 0.0,
        "metalAtomicFraction": 0.0,
        "numElements": 0,
    }


def _is_heavy_element(symbol: str) -> bool:
    atomic_numbers = {
        "Rb": 37, "Sr": 38, "Y": 39, "Zr": 40, "Nb": 41, "Mo": 42, "Tc": 43, "Ru": 44,
        "Rh": 45, "Pd": 46, "Ag": 47, "Cd": 48, "In": 49, "Sn": 50, "Sb": 51, "Te": 52,
        "I": 53, "Xe": 54, "Cs": 55, "Ba": 56, "La": 57, "Ce": 58, "Pr": 59, "Nd": 60,
        "Sm": 62, "Eu": 63, "Gd": 64, "Tb": 65, "Dy": 66, "Ho": 67, "Er": 68, "Tm": 69,
        "Yb": 70, "Lu": 71, "Hf": 72, "Ta": 73, "W": 74, "Re": 75, "Os": 76, "Ir": 77,
        "Pt": 78, "Au": 79, "Hg": 80, "Tl": 81, "Pb": 82, "Bi": 83, "Th": 90, "U": 92,
    }
    return atomic_numbers.get(symbol, 0) >= 37


def _is_metal_symbol(symbol: str) -> bool:
    nonmetals = {"H", "B", "C", "N", "O", "F", "Si", "P", "S", "Cl", "As", "Se", "Br", "Te", "I"}
    noble_gases = {"He", "Ne", "Ar", "Kr", "Xe", "Rn"}
    return symbol not in nonmetals and symbol not in noble_gases


def _looks_like_molecular_salt(candidate: dict[str, Any], elements: set[str]) -> bool:
    family = _infer_material_family(candidate)
    if family in {"garnet-oxide", "lgps-like-sulfide", "nasicon-oxide", "thiophosphate-sulfide", "zirconium-phosphate"}:
        return False
    if {"Li", "Cl", "O"}.issubset(elements) and not {"P", "S", "B", "Si", "Ge", "La", "Zr", "Ti", "Al", "Y", "In", "Sc"}.intersection(elements):
        return True
    if {"Li", "N", "H"}.issubset(elements):
        return True
    return False


def _family_prior_score(family: str, preset: str = "generic") -> float:
    by_preset = {
        "high-k-dielectric": {
            "binary-oxide": 0.95,
            "perovskite-oxide": 0.88,
            "complex-oxide": 0.82,
            "oxide": 0.75,
            "generic": 0.35,
        },
        "photovoltaic-absorber": {
            "halide-perovskite-like": 0.95,
            "chalcopyrite-chalcogenide": 0.92,
            "ii-vi-chalcogenide": 0.88,
            "chalcogenide-absorber": 0.84,
            "oxide-absorber": 0.62,
            "generic": 0.35,
        },
        "thermoelectric": {
            "telluride-thermoelectric": 0.98,
            "rocksalt-chalcogenide": 0.92,
            "skutterudite-like": 0.88,
            "chalcogenide-thermoelectric": 0.84,
            "oxide-thermoelectric": 0.58,
            "generic": 0.35,
        },
    }
    if preset in by_preset:
        return by_preset[preset].get(family, 0.45)
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


def _domain_descriptor_score(descriptors: dict[str, Any], preset: str) -> float:
    if preset == "high-k-dielectric":
        return max(
            float(descriptors.get("oxygenAtomicFraction") or 0.0),
            float(descriptors.get("metalAtomicFraction") or 0.0) * 0.7,
        )
    if preset == "photovoltaic-absorber":
        return max(
            float(descriptors.get("chalcogenideAtomicFraction") or 0.0),
            float(descriptors.get("halogenAtomicFraction") or 0.0) * 0.8,
            float(descriptors.get("oxygenAtomicFraction") or 0.0) * 0.5,
        )
    if preset == "thermoelectric":
        return float(descriptors.get("heavyAtomicFraction") or 0.0)
    return max(
        float(descriptors.get("oxygenAtomicFraction") or 0.0),
        float(descriptors.get("chalcogenideAtomicFraction") or 0.0),
        float(descriptors.get("halogenAtomicFraction") or 0.0),
        float(descriptors.get("metalAtomicFraction") or 0.0),
    )


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
    elif criteria.get("preset") == "high-k-dielectric":
        warnings.append("High-k preset still requires dielectric tensors, band offsets, interface reactions, and defect/leakage checks before device prioritization.")
    elif criteria.get("preset") == "photovoltaic-absorber":
        warnings.append("Photovoltaic preset still requires optical absorption, band-edge alignment, defect tolerance, and transport validation before device prioritization.")
    elif criteria.get("preset") == "thermoelectric":
        warnings.append("Thermoelectric preset still requires transport coefficients, carrier concentration sweeps, and lattice thermal conductivity validation.")
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
        "domainEvidenceScore",
        "evidenceTier",
        "evidenceSourceLevel",
        "riskPenalty",
        "stabilityComponent",
        "bandGapComponent",
        "densityComponent",
        "domainEvidenceComponent",
        "riskFlags",
        "domainGates",
        "missingProperties",
        "nextCalculations",
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
            evidence = candidate.get("domainEvidence") or {}
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
                "domainEvidenceScore": candidate.get("domainEvidenceScore"),
                "evidenceTier": evidence.get("tier"),
                "evidenceSourceLevel": evidence.get("sourceLevel"),
                "riskPenalty": candidate.get("riskPenalty"),
                "stabilityComponent": weighted.get("stability"),
                "bandGapComponent": weighted.get("bandGap"),
                "densityComponent": weighted.get("density"),
                "domainEvidenceComponent": weighted.get("domainEvidence"),
                "riskFlags": ",".join(((candidate.get("riskProfile") or {}).get("riskFlags") or [])),
                "domainGates": ";".join(
                    f"{gate.get('id')}:{gate.get('status')}:{gate.get('score')}"
                    for gate in (evidence.get("gates") or [])
                ),
                "missingProperties": ",".join(evidence.get("missingProperties") or []),
                "nextCalculations": " | ".join(evidence.get("nextCalculations") or []),
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


def _domain_coverage_report(ranked: list[dict[str, Any]]) -> dict[str, Any]:
    tiers = Counter(str(((candidate.get("domainEvidence") or {}).get("tier")) or "unknown") for candidate in ranked)
    source_levels = Counter(str(((candidate.get("domainEvidence") or {}).get("sourceLevel")) or "unknown") for candidate in ranked)
    missing = Counter()
    for candidate in ranked:
        evidence = candidate.get("domainEvidence") or {}
        for item in evidence.get("missingProperties") or []:
            missing[str(item)] += 1
    return {
        "tierCounts": dict(tiers),
        "sourceLevelCounts": dict(source_levels),
        "mostCommonMissingProperties": missing.most_common(10),
    }


def _infer_material_family(candidate: dict[str, Any], criteria: dict[str, Any] | None = None) -> str:
    formula = str(candidate.get("formula") or "").lower()
    elements = {str(item) for item in candidate.get("elements") or []}
    if not elements:
        elements = set(_composition_descriptors(candidate).get("elements") or [])
    preset = str((criteria or {}).get("preset") or "generic")

    if preset == "high-k-dielectric":
        if {"Ba", "Ti", "O"}.issubset(elements) or {"Sr", "Ti", "O"}.issubset(elements):
            return "perovskite-oxide"
        if len(elements) == 2 and "O" in elements:
            if {"Hf", "Zr", "Ti", "Ta", "Y", "La", "Al", "Si"}.intersection(elements):
                return "binary-oxide"
            return "oxide"
        if "O" in elements:
            return "complex-oxide"
    if preset == "photovoltaic-absorber":
        if {"Pb", "I"}.issubset(elements) or {"Sn", "I"}.issubset(elements):
            return "halide-perovskite-like"
        if {"Cu", "In", "Se"}.issubset(elements) or {"Cu", "Ga", "Se"}.issubset(elements):
            return "chalcopyrite-chalcogenide"
        if {"Cd", "Te"}.issubset(elements):
            return "ii-vi-chalcogenide"
        if {"S", "Se", "Te"}.intersection(elements):
            return "chalcogenide-absorber"
        if "O" in elements:
            return "oxide-absorber"
    if preset == "thermoelectric":
        if {"Bi", "Te"}.issubset(elements) or {"Sb", "Te"}.issubset(elements):
            return "telluride-thermoelectric"
        if {"Pb", "Te"}.issubset(elements) or {"Sn", "Se"}.issubset(elements):
            return "rocksalt-chalcogenide"
        if {"Co", "Sb"}.issubset(elements):
            return "skutterudite-like"
        if {"S", "Se", "Te"}.intersection(elements):
            return "chalcogenide-thermoelectric"
        if "O" in elements:
            return "oxide-thermoelectric"

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
