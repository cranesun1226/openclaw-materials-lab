from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
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
    from pymatgen.core import Composition, Element, Structure  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    Composition = None
    Element = None
    Structure = None

try:
    from pymatgen.io.vasp import Poscar  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    Poscar = None

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    PdfReader = None


ATOMIC_MASS_FALLBACK = {
    "H": 1.00794,
    "Li": 6.941,
    "Be": 9.012182,
    "B": 10.811,
    "C": 12.0107,
    "N": 14.0067,
    "O": 15.9994,
    "F": 18.9984032,
    "Na": 22.98976928,
    "Mg": 24.305,
    "Al": 26.9815386,
    "Si": 28.0855,
    "P": 30.973762,
    "S": 32.065,
    "Cl": 35.453,
    "K": 39.0983,
    "Ca": 40.078,
    "Sc": 44.955912,
    "Ti": 47.867,
    "V": 50.9415,
    "Cr": 51.9961,
    "Mn": 54.938045,
    "Fe": 55.845,
    "Co": 58.933195,
    "Ni": 58.6934,
    "Cu": 63.546,
    "Zn": 65.38,
    "Ga": 69.723,
    "Ge": 72.64,
    "As": 74.9216,
    "Se": 78.96,
    "Br": 79.904,
    "Rb": 85.4678,
    "Sr": 87.62,
    "Y": 88.90585,
    "Zr": 91.224,
    "Nb": 92.90638,
    "Mo": 95.96,
    "Ag": 107.8682,
    "Cd": 112.411,
    "In": 114.818,
    "Sn": 118.71,
    "Sb": 121.76,
    "Te": 127.6,
    "I": 126.90447,
    "Cs": 132.9054519,
    "Ba": 137.327,
    "La": 138.90547,
    "Ce": 140.116,
    "Hf": 178.49,
    "Ta": 180.94788,
    "W": 183.84,
    "Pb": 207.2,
    "Bi": 208.9804,
}


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
        "plan_research_loop": lambda: handle_plan_research_loop(request_id=request_id, payload=payload, api_key=api_key),
        "ingest_evidence": lambda: handle_ingest_evidence(request_id=request_id, payload=payload),
        "evaluate_research_claim": lambda: handle_evaluate_research_claim(request_id=request_id, payload=payload),
        "execute_research_plan": lambda: handle_execute_research_plan(request_id=request_id, payload=payload, api_key=api_key),
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
        "usedDevelopmentFixtureData": used_offline,
    }
    mode = "development fixture data" if used_offline else "Materials Project"
    return success(
        action="search_materials",
        request_id=request_id,
        summary=f"Found {len(data['candidates'])} candidate materials using {mode}.",
        data=data,
        warnings=["Using development fixture data; results are for smoke testing only."] if used_offline else [],
    )


def handle_fetch_structure(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    material_id = ensure_string(payload.get("materialId"), field="materialId")
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    format_name = str(payload.get("format") or "both").lower()
    allow_offline = ensure_bool(payload.get("allowOffline"), field="allowOffline", default=False)
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
    if used_offline:
        warnings.append("Using development fixture data; fetched structure is not live Materials Project evidence.")

    data = {
        "material": _candidate_summary(material),
        "structurePath": json_path,
        "cifPath": cif_path,
        "structure": structure_data,
        "usedOfflineData": used_offline,
        "usedDevelopmentFixtureData": used_offline,
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
    allow_offline = ensure_bool(payload.get("allowOffline"), field="allowOffline", default=False)
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
    if used_offline:
        warnings.append("Using development fixture data; structural analysis is a smoke-test artifact.")

    data = {
        "materialId": material_id,
        "formula": analysis["summaryMetrics"].get("formula"),
        "summaryMetrics": analysis["summaryMetrics"],
        "readableSummary": analysis["readableSummary"],
        "plotPath": plot_path,
        "usedOfflineData": used_offline,
        "usedDevelopmentFixtureData": used_offline,
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


def handle_plan_research_loop(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    candidates = payload.get("candidates") or []
    if not isinstance(candidates, list):
        raise WorkerError("INVALID_PARAMS", "plan_research_loop requires candidates to be an array when provided.")

    raw_criteria = ensure_dict(payload.get("criteria") or {}, field="criteria")
    criteria = _prepare_compare_criteria(raw_criteria)
    budget = _normalize_research_budget(ensure_dict(payload.get("budget") or {}, field="budget"))
    research_goal = ensure_string(payload.get("researchGoal"), field="researchGoal", required=False)
    objective = ensure_string(payload.get("objective"), field="objective", required=False) or research_goal or _default_research_objective(criteria)
    if not candidates and not objective:
        raise WorkerError("INVALID_PARAMS", "plan_research_loop requires either candidates or a researchGoal/objective.")
    mode = str(payload.get("mode") or "property-backed").strip().lower()
    approval_policy = str(payload.get("approvalPolicy") or "approval-required").strip().lower()
    protocol_inputs = _normalize_protocol_inputs(payload, objective=objective, criteria=criteria)
    draft_protocol = _compile_dynamic_research_protocol(
        objective=objective,
        candidates=candidates,
        criteria=criteria,
        protocol_inputs=protocol_inputs,
    )
    criteria = _criteria_for_protocol_topic(raw_criteria, criteria, draft_protocol.get("topic") or {})
    discovery = _autonomous_candidate_discovery(
        candidates=candidates,
        protocol=draft_protocol,
        criteria=criteria,
        budget=budget,
        artifact_dir=artifact_dir,
        api_key=api_key,
        protocol_inputs=protocol_inputs,
    )
    if not candidates and discovery.get("rankedCandidates"):
        candidates = list(discovery.get("rankedCandidates") or [])

    plan = _build_research_loop_plan(
        candidates=candidates,
        criteria=criteria,
        budget=budget,
        objective=objective,
        mode=mode,
        approval_policy=approval_policy,
        protocol_inputs=protocol_inputs,
    )
    _attach_autonomous_discovery(plan, discovery, candidates)
    manifest_path = artifact_dir / f"{plan['planId']}.json"
    report_path = artifact_dir / f"{plan['planId']}.md"
    manifest_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_research_plan_markdown(plan), encoding="utf-8")
    data = {
        "plan": plan,
        "manifestPath": str(manifest_path),
        "reportPath": str(report_path),
        **_discovery_paths_for_result(discovery),
    }
    warnings = list(plan.get("warnings") or [])
    warnings.extend(discovery.get("warnings") or [])
    return success(
        action="plan_research_loop",
        request_id=request_id,
        summary=f"Compiled dynamic research protocol with {len(plan['calculationQueue'])} approval-gated step(s) for {len(plan['selectedCandidates'])} selected candidate(s).",
        data=data,
        artifacts=[str(manifest_path), str(report_path), *list(discovery.get("artifactPaths") or [])],
        warnings=warnings,
    )


def handle_evaluate_research_claim(*, request_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    plan = _load_research_plan(payload)
    candidate_id = (
        ensure_string(payload.get("candidateId"), field="candidateId", required=False)
        or _default_claim_candidate_id(plan)
    )
    if not candidate_id:
        raise WorkerError("INVALID_PARAMS", "evaluate_research_claim requires candidateId or a plan with selectedCandidates.")

    ledger_path = (
        ensure_string(payload.get("evidenceLedgerPath"), field="evidenceLedgerPath", required=False)
        or _default_evidence_ledger_path(plan)
    )
    existing_rows = _read_evidence_ledger(ledger_path) if ledger_path else []
    provided_rows = [
        _normalize_evidence_row(item, candidate_id=candidate_id)
        for item in (payload.get("evidenceRows") or [])
        if isinstance(item, dict)
    ]
    rows = [*existing_rows, *provided_rows]
    if not rows:
        raise WorkerError(
            "NO_EVIDENCE_ROWS",
            "No evidence rows were available for claim evaluation.",
            hint="Pass evidenceLedgerPath or evidenceRows with parsed literature/calculation/experiment evidence.",
        )

    merged_ledger_path = artifact_dir / f"{_safe_file_stem(candidate_id)}-claim-evidence-ledger.jsonl"
    merged_ledger_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    requested = str(payload.get("requestedClaimLevel") or "research-grade-candidate")
    review = _evaluate_research_claim(
        plan=plan,
        candidate_id=candidate_id,
        rows=rows,
        requested_claim_level=requested,
        ledger_path=ledger_path,
        merged_ledger_path=str(merged_ledger_path),
    )
    review_path = artifact_dir / f"{_safe_file_stem(candidate_id)}-claim-review.json"
    report_path = artifact_dir / f"{_safe_file_stem(candidate_id)}-claim-review.md"
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_claim_evaluation_markdown(review), encoding="utf-8")
    data = {
        "candidateId": candidate_id,
        "claimStatus": review["claimStatus"],
        "reviewPath": str(review_path),
        "reportPath": str(report_path),
        "ledgerPath": ledger_path,
        "mergedLedgerPath": str(merged_ledger_path),
        "missingEvidence": review["missingEvidence"],
        "satisfiedEvidence": review["satisfiedEvidence"],
        "blockingEvidence": review["blockingEvidence"],
        "conflictingEvidence": review["conflictingEvidence"],
        "uncertaintySummary": review["uncertaintySummary"],
        "auditCertificate": review["auditCertificate"],
        "evidenceRowsReviewed": review["evidenceRowsReviewed"],
    }
    warnings = list(review.get("warnings") or [])
    return success(
        action="evaluate_research_claim",
        request_id=request_id,
        summary=(
            f"Evaluated claim for {candidate_id}: "
            f"{review['claimStatus']['currentLevel']} "
            f"(research-grade allowed: {str(review['claimStatus']['researchGradeClaimAllowed']).lower()})."
        ),
        data=data,
        artifacts=[str(review_path), str(report_path), str(merged_ledger_path)],
        warnings=warnings,
    )


def handle_ingest_evidence(*, request_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    plan: dict[str, Any] = {}
    if payload.get("plan") or payload.get("planPath"):
        plan = _load_research_plan(payload)
    candidate_id = (
        ensure_string(payload.get("candidateId"), field="candidateId", required=False)
        or _default_claim_candidate_id(plan)
    )
    evidence_ledger_path = (
        ensure_string(payload.get("evidenceLedgerPath"), field="evidenceLedgerPath", required=False)
        or _default_evidence_ledger_path(plan)
    )
    output_ledger_path = ensure_string(payload.get("outputLedgerPath"), field="outputLedgerPath", required=False)
    parser = str(payload.get("parser") or "auto").strip().lower()
    artifact_paths = _string_list(payload.get("artifactPaths"))
    provided_rows = [
        _normalize_evidence_row(item, candidate_id=candidate_id)
        for item in (payload.get("evidenceRows") or [])
        if isinstance(item, dict)
    ]
    rows: list[dict[str, Any]] = []
    parsed_artifacts: list[dict[str, Any]] = []
    warnings: list[str] = []
    rows.extend(provided_rows)
    for artifact_path in artifact_paths:
        path = Path(artifact_path)
        if not path.exists():
            warnings.append(f"Artifact not found and was skipped: {artifact_path}")
            continue
        parsed_rows, record_warnings, parser_used = _parse_evidence_artifact(
            path=path,
            parser=parser,
            plan=plan,
            candidate_id=candidate_id,
            evidence_requirement_id=ensure_string(payload.get("evidenceRequirementId"), field="evidenceRequirementId", required=False),
            default_status=ensure_string(payload.get("defaultStatus"), field="defaultStatus", required=False),
            source_label=ensure_string(payload.get("sourceLabel"), field="sourceLabel", required=False),
        )
        rows.extend(parsed_rows)
        warnings.extend(record_warnings)
        parsed_artifacts.append({
            "path": str(path),
            "parser": parser_used,
            "evidenceRows": len(parsed_rows),
        })
    if not rows:
        raise WorkerError(
            "NO_EVIDENCE_PARSED",
            "No evidence rows were parsed or provided.",
            hint="Pass QE/VASP output files, evidenceRows, or JSON/CSV literature/experiment evidence.",
        )
    rows = [_normalize_evidence_row(row, candidate_id=candidate_id) for row in rows]
    prior_rows = _read_evidence_ledger(evidence_ledger_path) if evidence_ledger_path and Path(evidence_ledger_path).exists() else []
    output_path = Path(output_ledger_path or evidence_ledger_path or artifact_dir / "ingested-evidence-ledger.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_rows = _dedupe_evidence_rows([*prior_rows, *rows])
    output_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in merged_rows), encoding="utf-8")
    report_path = artifact_dir / "evidence-ingestion-report.md"
    report = {
        "candidateId": candidate_id,
        "parser": parser,
        "evidenceLedgerPath": str(output_path),
        "newEvidenceRows": len(rows),
        "totalEvidenceRows": len(merged_rows),
        "parsedArtifacts": parsed_artifacts,
        "warnings": warnings,
        "evidenceRows": rows,
    }
    report_path.write_text(_evidence_ingestion_markdown(report), encoding="utf-8")
    data = {
        "candidateId": candidate_id,
        "parser": parser,
        "evidenceRows": rows,
        "evidenceRowCount": len(rows),
        "evidenceLedgerPath": str(output_path),
        "reportPath": str(report_path),
        "parsedArtifacts": parsed_artifacts,
        "warnings": warnings,
    }
    return success(
        action="ingest_evidence",
        request_id=request_id,
        summary=f"Ingested {len(rows)} evidence row(s) into {output_path}.",
        data=data,
        artifacts=[str(output_path), str(report_path)],
        warnings=warnings,
    )


def handle_execute_research_plan(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    backend = str(payload.get("backend") or "dev-smoke").strip().lower()
    plan = _load_research_plan(payload)
    if not isinstance(plan.get("calculationQueue"), list):
        raise WorkerError("INVALID_PARAMS", "execute_research_plan requires a plan with calculationQueue.")

    max_steps = int(payload.get("maxSteps") or len(plan["calculationQueue"]))
    execution_mode = str(payload.get("executionMode") or "prepare").strip().lower()
    if backend == "dev-smoke":
        allow_blocked_dev_smoke = ensure_bool(payload.get("allowBlockedDevSmoke"), field="allowBlockedDevSmoke", default=False)
        execution = _execute_dev_smoke_plan(
            plan=plan,
            artifact_dir=artifact_dir,
            api_key=api_key,
            max_steps=max_steps,
            allow_blocked_dev_smoke=allow_blocked_dev_smoke,
        )
    elif backend in {"quantum-espresso", "vasp", "atomate2", "aiida"}:
        execution = _execute_external_backend_plan(
            plan=plan,
            artifact_dir=artifact_dir,
            api_key=api_key,
            backend=backend,
            max_steps=max_steps,
            execution_mode=execution_mode,
            allow_execution=ensure_bool(payload.get("allowExecution"), field="allowExecution", default=False),
            backend_config=ensure_dict(payload.get("backendConfig") or {}, field="backendConfig"),
            execution_manifest_path=ensure_string(payload.get("executionManifestPath"), field="executionManifestPath", required=False),
        )
    else:
        raise WorkerError(
            "BACKEND_NOT_AVAILABLE",
            f"Research backend '{backend}' is not available in this build.",
            hint="Use one of: dev-smoke, quantum-espresso, vasp, atomate2, aiida.",
        )

    artifacts = [execution["manifestPath"], execution["reportPath"], *execution.get("resultPaths", []), *execution.get("inputPaths", [])]
    return success(
        action="execute_research_plan",
        request_id=request_id,
        summary=(
            f"{execution['statusSummary']}: {execution.get('completedCalculations', 0)} completed, "
            f"{execution.get('preparedCalculations', 0)} prepared, {execution.get('submittedCalculations', 0)} submitted, "
            f"{execution.get('skippedCalculations', 0)} skipped."
        ),
        data=execution,
        artifacts=artifacts,
        warnings=execution["warnings"],
    )


def handle_ase_relax(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    artifact_dir = ensure_string(payload.get("artifactDir"), field="artifactDir")
    structure_path = ensure_string(payload.get("structurePath"), field="structurePath", required=False)
    material_id = ensure_string(payload.get("materialId"), field="materialId", required=False)
    allow_offline = ensure_bool(payload.get("allowOffline"), field="allowOffline", default=False)
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
        "usedDevelopmentFixtureData": used_offline,
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
    allow_offline = ensure_bool(payload.get("allowOffline"), field="allowOffline", default=False)
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
            "usedDevelopmentFixtureData": used_offline,
        },
        artifacts=[artifact for artifact in [plot_path, *table_paths] if artifact],
        warnings=["Using development fixture data; batch screen is a smoke-test artifact."] if used_offline else [],
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


def _parse_evidence_artifact(
    *,
    path: Path,
    parser: str,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str | None,
    default_status: str | None,
    source_label: str | None,
) -> tuple[list[dict[str, Any]], list[str], str]:
    parser_used = _resolve_evidence_parser(path, parser)
    if parser_used == "quantum-espresso":
        return _parse_quantum_espresso_evidence(path, plan, candidate_id, evidence_requirement_id, default_status, source_label), [], parser_used
    if parser_used == "vasp":
        return _parse_vasp_evidence(path, plan, candidate_id, evidence_requirement_id, default_status, source_label), [], parser_used
    if parser_used in {"lammps", "md"}:
        return _parse_md_evidence(path, plan, candidate_id, evidence_requirement_id, default_status, source_label, parser_used), [], parser_used
    if parser_used in {"literature-text", "literature-pdf", "literature-markdown"}:
        rows, warnings = _parse_literature_text_evidence(path, plan, candidate_id, evidence_requirement_id, default_status, source_label, parser_used)
        return rows, warnings, parser_used
    if parser_used in {"literature-json", "experiment-json", "evidence-jsonl"}:
        return _parse_structured_evidence(path, parser_used, candidate_id, default_status, source_label), [], parser_used
    if parser_used == "csv":
        return _parse_csv_evidence(path, candidate_id, default_status, source_label), [], parser_used
    return [], [f"No evidence parser matched {path}."], parser_used


def _resolve_evidence_parser(path: Path, parser: str) -> str:
    if parser != "auto":
        return parser
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name in {"outcar", "vasprun.xml"} or "vasp" in name:
        return "vasp"
    if name.endswith((".out", ".pwout")) or "qe" in name or "espresso" in name or "pw.scf" in name or "ph." in name:
        return "quantum-espresso"
    if name in {"log.lammps", "lammps.log"} or "lammps" in name:
        return "lammps"
    if "aimd" in name or "md.log" in name or name.endswith(".lammpstrj"):
        return "md"
    if suffix == ".pdf":
        return "literature-pdf"
    if suffix in {".md", ".markdown"} and any(token in name for token in ["literature", "citation", "paper", "abstract", "review"]):
        return "literature-markdown"
    if suffix == ".txt" and any(token in name for token in ["literature", "citation", "paper", "abstract", "review"]):
        return "literature-text"
    if suffix == ".csv":
        return "csv"
    if suffix == ".jsonl":
        return "evidence-jsonl"
    if suffix == ".json":
        return "evidence-jsonl"
    return "unknown"


def _parse_quantum_espresso_evidence(
    path: Path,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str | None,
    default_status: str | None,
    source_label: str | None,
) -> list[dict[str, Any]]:
    text = path.read_text("utf-8", errors="replace")
    rows: list[dict[str, Any]] = []
    total = _last_float_match(text, r"!\s+total energy\s+=\s+([-+]?\d+(?:\.\d+)?)\s+Ry")
    if total is not None:
        rows.append(_parsed_evidence_row(
            plan=plan,
            candidate_id=candidate_id,
            evidence_requirement_id=evidence_requirement_id or _infer_requirement_for_properties(plan, ["totalEnergyRy", "totalEnergyEv"], "phase-stability"),
            artifact_path=str(path),
            source_type="parsed-calculation",
            source=source_label or "quantum-espresso",
            status=default_status or "parsed-property",
            claim="Quantum ESPRESSO output parsed total-energy evidence.",
            property_values={
                "totalEnergyRy": total,
                "totalEnergyEv": total * 13.605693122994,
                "jobDone": "JOB DONE" in text,
            },
        ))
    band_gap = _qe_band_gap_ev(text)
    if band_gap is not None:
        rows.append(_parsed_evidence_row(
            plan=plan,
            candidate_id=candidate_id,
            evidence_requirement_id=evidence_requirement_id or _infer_requirement_for_properties(plan, ["directBandGapEv", "bandGapEv"], "optical-absorption"),
            artifact_path=str(path),
            source_type="parsed-calculation",
            source=source_label or "quantum-espresso",
            status=default_status or "parsed-property",
            claim="Quantum ESPRESSO output parsed band-gap evidence.",
            property_values={"directBandGapEv": band_gap, "bandGapEv": band_gap},
        ))
    adsorption = _last_float_match(text, r"adsorption\s+energy\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*eV")
    if adsorption is not None:
        rows.append(_parsed_evidence_row(
            plan=plan,
            candidate_id=candidate_id,
            evidence_requirement_id=evidence_requirement_id or _infer_requirement_for_properties(plan, ["adsorptionEnergyEv"], "surface-activity"),
            artifact_path=str(path),
            source_type="parsed-calculation",
            source=source_label or "quantum-espresso",
            status=default_status or "parsed-property",
            claim="Quantum ESPRESSO-derived output parsed adsorption-energy evidence.",
            property_values={"adsorptionEnergyEv": adsorption},
        ))
    dielectric = _parse_dielectric_scalar(text)
    if dielectric is not None:
        rows.append(_parsed_evidence_row(
            plan=plan,
            candidate_id=candidate_id,
            evidence_requirement_id=evidence_requirement_id or _infer_requirement_for_properties(plan, ["dielectricTotal"], "dielectric-response"),
            artifact_path=str(path),
            source_type="parsed-calculation",
            source=source_label or "quantum-espresso",
            status=default_status or "parsed-property",
            claim="Quantum ESPRESSO/DFPT output parsed dielectric evidence.",
            property_values={"dielectricTotal": dielectric},
        ))
    rows.extend(_parse_electronic_structure_rows(text, path, plan, candidate_id, evidence_requirement_id, default_status, source_label or "quantum-espresso"))
    rows.extend(_parse_surface_energy_rows(text, path, plan, candidate_id, evidence_requirement_id, default_status, source_label or "quantum-espresso"))
    rows.extend(_parse_phonon_rows(text, path, plan, candidate_id, evidence_requirement_id, default_status, source_label or "quantum-espresso"))
    rows.extend(_parse_aimd_rows(text, path, plan, candidate_id, evidence_requirement_id, default_status, source_label or "quantum-espresso"))
    return rows


def _parse_vasp_evidence(
    path: Path,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str | None,
    default_status: str | None,
    source_label: str | None,
) -> list[dict[str, Any]]:
    text = path.read_text("utf-8", errors="replace")
    rows: list[dict[str, Any]] = []
    total = _last_float_match(text, r"TOTEN\s+=\s+([-+]?\d+(?:\.\d+)?)\s+eV")
    if total is None:
        total = _last_float_match(text, r"<i\s+name=\"e_fr_energy\">\s*([-+]?\d+(?:\.\d+)?)\s*</i>")
    if total is not None:
        rows.append(_parsed_evidence_row(
            plan=plan,
            candidate_id=candidate_id,
            evidence_requirement_id=evidence_requirement_id or _infer_requirement_for_properties(plan, ["totalEnergyEv"], "phase-stability"),
            artifact_path=str(path),
            source_type="parsed-calculation",
            source=source_label or "vasp",
            status=default_status or "parsed-property",
            claim="VASP output parsed total-energy evidence.",
            property_values={"totalEnergyEv": total},
        ))
    band_gap = _last_float_match(text, r"band\s*gap\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*eV")
    if band_gap is not None:
        rows.append(_parsed_evidence_row(
            plan=plan,
            candidate_id=candidate_id,
            evidence_requirement_id=evidence_requirement_id or _infer_requirement_for_properties(plan, ["directBandGapEv", "bandGapEv"], "optical-absorption"),
            artifact_path=str(path),
            source_type="parsed-calculation",
            source=source_label or "vasp",
            status=default_status or "parsed-property",
            claim="VASP output parsed band-gap evidence.",
            property_values={"directBandGapEv": band_gap, "bandGapEv": band_gap},
        ))
    adsorption = _last_float_match(text, r"adsorption\s+energy\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*eV")
    if adsorption is not None:
        rows.append(_parsed_evidence_row(
            plan=plan,
            candidate_id=candidate_id,
            evidence_requirement_id=evidence_requirement_id or _infer_requirement_for_properties(plan, ["adsorptionEnergyEv"], "surface-activity"),
            artifact_path=str(path),
            source_type="parsed-calculation",
            source=source_label or "vasp",
            status=default_status or "parsed-property",
            claim="VASP-derived output parsed adsorption-energy evidence.",
            property_values={"adsorptionEnergyEv": adsorption},
        ))
    rows.extend(_parse_electronic_structure_rows(text, path, plan, candidate_id, evidence_requirement_id, default_status, source_label or "vasp"))
    rows.extend(_parse_surface_energy_rows(text, path, plan, candidate_id, evidence_requirement_id, default_status, source_label or "vasp"))
    rows.extend(_parse_phonon_rows(text, path, plan, candidate_id, evidence_requirement_id, default_status, source_label or "vasp"))
    rows.extend(_parse_aimd_rows(text, path, plan, candidate_id, evidence_requirement_id, default_status, source_label or "vasp"))
    return rows


def _parse_electronic_structure_rows(
    text: str,
    path: Path,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str | None,
    default_status: str | None,
    source: str,
) -> list[dict[str, Any]]:
    values: dict[str, Any] = {}
    fermi = _last_float_match(text, r"(?:Fermi energy is|E-fermi\s*:)\s*([-+]?\d+(?:\.\d+)?)\s*(?:ev|eV)?")
    dos_fermi = _last_float_match(text, r"(?:DOS at Fermi|N\(E_F\)|dos\(e_f\))\s*[:=]\s*([-+]?\d+(?:\.\d+)?)")
    cbm = _last_float_match(text, r"\bCBM\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*eV")
    vbm = _last_float_match(text, r"\bVBM\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*eV")
    if fermi is not None:
        values["fermiEnergyEv"] = fermi
    if dos_fermi is not None:
        values["dosAtFermi"] = dos_fermi
    if cbm is not None:
        values["cbmEv"] = cbm
    if vbm is not None:
        values["vbmEv"] = vbm
    if not values:
        return []
    requirement_id = evidence_requirement_id or _infer_requirement_for_properties(
        plan,
        ["fermiEnergyEv", "dosAtFermi", "cbmEv", "vbmEv", "bandGapEv"],
        "electronic-structure",
    )
    return [_parsed_evidence_row(
        plan=plan,
        candidate_id=candidate_id,
        evidence_requirement_id=requirement_id,
        artifact_path=str(path),
        source_type="parsed-calculation",
        source=source,
        status=default_status or "parsed-property",
        claim="Electronic-structure output parsed band/DOS provenance.",
        property_values=values,
    )]


def _parse_surface_energy_rows(
    text: str,
    path: Path,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str | None,
    default_status: str | None,
    source: str,
) -> list[dict[str, Any]]:
    surface_energy = _last_float_match(text, r"surface\s+energy\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*(?:J/m\^?2|J m-2)")
    surface_energy_ev_a2 = _last_float_match(text, r"surface\s+energy\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*(?:eV/A\^?2|eV Angstrom-2)")
    cleavage = _last_float_match(text, r"cleavage\s+energy\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*(?:J/m\^?2|J m-2)")
    values: dict[str, Any] = {}
    if surface_energy is not None:
        values["surfaceEnergyJm2"] = surface_energy
    if surface_energy_ev_a2 is not None:
        values["surfaceEnergyEvA2"] = surface_energy_ev_a2
    if cleavage is not None:
        values["cleavageEnergyJm2"] = cleavage
    if not values:
        return []
    requirement_id = evidence_requirement_id or _infer_requirement_for_properties(
        plan,
        ["surfaceEnergyJm2", "surfaceEnergyEvA2", "cleavageEnergyJm2", "surfaceStability"],
        "surface-activity",
    )
    return [_parsed_evidence_row(
        plan=plan,
        candidate_id=candidate_id,
        evidence_requirement_id=requirement_id,
        artifact_path=str(path),
        source_type="parsed-calculation",
        source=source,
        status=default_status or "parsed-property",
        claim="Surface-energy output parsed surface stability/activity evidence.",
        property_values=values,
    )]


def _parse_phonon_rows(
    text: str,
    path: Path,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str | None,
    default_status: str | None,
    source: str,
) -> list[dict[str, Any]]:
    frequencies = [float(item) for item in re.findall(
        r"(?:freq\s*\([^)]*\)\s*=|f/i=|THz\s*)\s*([-+]?\d+(?:\.\d+)?)\s*(?:\[?cm-1\]?|cm\^-1|THz)?",
        text,
        flags=re.IGNORECASE,
    )]
    if not frequencies:
        frequencies = [float(item) for item in re.findall(r"phonon\s+frequency\s*[:=]\s*([-+]?\d+(?:\.\d+)?)", text, flags=re.IGNORECASE)]
    if not frequencies:
        return []
    min_frequency = min(frequencies)
    imaginary_count = sum(1 for value in frequencies if value < -5e-3)
    requirement_id = evidence_requirement_id or _infer_requirement_for_properties(
        plan,
        ["phononStability", "imaginaryModeCount", "minPhononFrequencyCm1", "latticeThermalConductivityWmK"],
        "phonon-stability",
    )
    status = default_status or ("parsed-property" if imaginary_count == 0 else "conflicting-evidence")
    return [_parsed_evidence_row(
        plan=plan,
        candidate_id=candidate_id,
        evidence_requirement_id=requirement_id,
        artifact_path=str(path),
        source_type="parsed-calculation",
        source=source,
        status=status,
        claim="Phonon output parsed dynamic-stability evidence.",
        property_values={
            "phononStability": imaginary_count == 0,
            "imaginaryModeCount": imaginary_count,
            "minPhononFrequencyCm1": min_frequency,
            "phononModeCount": len(frequencies),
        },
    )]


def _parse_aimd_rows(
    text: str,
    path: Path,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str | None,
    default_status: str | None,
    source: str,
) -> list[dict[str, Any]]:
    temperatures = [float(item) for item in re.findall(r"(?:temperature|T=)\s*[:=]?\s*([-+]?\d+(?:\.\d+)?)\s*K?", text, flags=re.IGNORECASE)]
    diffusion = _last_float_match(text, r"(?:diffusion\s+coefficient|D_?self|D=)\s*[:=]\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*(?:cm\^?2/s|m\^?2/s)?")
    msd = _last_float_match(text, r"(?:MSD|mean\s+square\s+displacement)\s*[:=]\s*([-+]?\d+(?:\.\d+)?)")
    drift = _last_float_match(text, r"(?:total\s+drift|energy\s+drift)\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*(?:eV|Ry)?")
    values: dict[str, Any] = {}
    if temperatures:
        values["averageTemperatureK"] = sum(temperatures) / len(temperatures)
        values["temperatureSamples"] = len(temperatures)
    if diffusion is not None:
        values["diffusionCoefficient"] = diffusion
    if msd is not None:
        values["meanSquaredDisplacement"] = msd
    if drift is not None:
        values["energyDrift"] = drift
    if not values:
        return []
    requirement_id = evidence_requirement_id or _infer_requirement_for_properties(
        plan,
        ["diffusionCoefficient", "meanSquaredDisplacement", "averageTemperatureK", "operandoStability", "ionicConductivityScm"],
        "operando-stability",
    )
    return [_parsed_evidence_row(
        plan=plan,
        candidate_id=candidate_id,
        evidence_requirement_id=requirement_id,
        artifact_path=str(path),
        source_type="md" if "diffusionCoefficient" in values or "meanSquaredDisplacement" in values else "parsed-calculation",
        source=source,
        status=default_status or "parsed-property",
        claim="AIMD/MD output parsed finite-temperature stability or transport evidence.",
        property_values=values,
    )]


def _parse_md_evidence(
    path: Path,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str | None,
    default_status: str | None,
    source_label: str | None,
    parser_used: str,
) -> list[dict[str, Any]]:
    text = path.read_text("utf-8", errors="replace")
    rows = _parse_aimd_rows(text, path, plan, candidate_id, evidence_requirement_id, default_status, source_label or parser_used)
    if not rows:
        thermo_values = _parse_lammps_thermo_values(text)
        if thermo_values:
            rows.append(_parsed_evidence_row(
                plan=plan,
                candidate_id=candidate_id,
                evidence_requirement_id=evidence_requirement_id or _infer_requirement_for_properties(
                    plan,
                    ["averageTemperatureK", "averagePressure", "totalEnergyDrift", "operandoStability"],
                    "operando-stability",
                ),
                artifact_path=str(path),
                source_type="md",
                source=source_label or parser_used,
                status=default_status or "parsed-property",
                claim="MD log parsed thermo trajectory evidence.",
                property_values=thermo_values,
            ))
    return rows


def _parse_lammps_thermo_values(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        headers = line.split()
        lower = [item.lower() for item in headers]
        if "step" not in lower or not any(item in lower for item in ["temp", "temperature"]):
            continue
        samples: list[dict[str, float]] = []
        for data_line in lines[index + 1:]:
            parts = data_line.split()
            if len(parts) < len(headers):
                break
            try:
                samples.append({header: float(value) for header, value in zip(lower, parts)})
            except Exception:
                break
        if not samples:
            continue
        values: dict[str, Any] = {"thermoSamples": len(samples)}
        for key, output_key in [("temp", "averageTemperatureK"), ("press", "averagePressure"), ("etotal", "averageTotalEnergy")]:
            collected = [sample[key] for sample in samples if key in sample]
            if collected:
                values[output_key] = sum(collected) / len(collected)
                if key == "etotal":
                    values["totalEnergyDrift"] = collected[-1] - collected[0]
        return values
    return {}


def _parse_literature_text_evidence(
    path: Path,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str | None,
    default_status: str | None,
    source_label: str | None,
    parser_used: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    text, warnings = _read_literature_text(path, parser_used)
    if not text.strip():
        return [], warnings or [f"No extractable literature text found in {path}."]
    citations = _extract_citation_provenance(text, path)
    candidates = _candidate_mentions_from_text(text, plan, candidate_id)
    property_values = _extract_literature_property_values(text)
    table_like_lines = _count_table_like_lines(text)
    rows: list[dict[str, Any]] = []
    generated_at = int(time.time())
    for target_candidate in candidates or [candidate_id]:
        requirement_id = evidence_requirement_id or _infer_requirement_for_properties(
            plan,
            list(property_values.keys()) or ["literatureBaseline"],
            "literature-benchmark",
        )
        row = _normalize_evidence_row({
            "ledgerVersion": "evidence-ledger-v1",
            "evidenceId": _safe_file_stem(f"{target_candidate or 'candidate'}-{requirement_id}-{path.stem}").lower(),
            "candidateId": target_candidate,
            "formula": _candidate_formula_for_plan(plan, target_candidate),
            "evidenceRequirementId": requirement_id,
            "claim": "Literature artifact parsed into citation-provenance evidence.",
            "status": default_status or "literature-supported",
            "sourceType": "literature",
            "source": source_label or path.name,
            "confidence": "citation-provenance" if citations.get("doi") or citations.get("url") else "literature-text-extraction",
            "propertyValues": {
                **property_values,
                "citationCount": len(citations.get("references") or []),
                "tableLikeLineCount": table_like_lines,
                "literatureBaseline": True,
            },
            "artifactPath": str(path),
            "sourcePath": str(path),
            "citation": citations.get("primaryCitation"),
            "citationProvenance": citations,
            "generatedAt": generated_at,
        }, candidate_id=target_candidate)
        rows.append(row)
    return rows, warnings


def _read_literature_text(path: Path, parser_used: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if parser_used == "literature-pdf":
        if PdfReader is None:
            warnings.append("pypdf is not installed; PDF text extraction used a lossy fallback.")
            return path.read_bytes().decode("utf-8", errors="replace"), warnings
        try:
            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages[:50]]
            return "\n".join(pages), warnings
        except Exception as exc:
            warnings.append(f"PDF text extraction failed: {exc}")
            return "", warnings
    return path.read_text("utf-8", errors="replace"), warnings


def _extract_citation_provenance(text: str, path: Path) -> dict[str, Any]:
    doi_matches = sorted(set(re.findall(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", text, flags=re.IGNORECASE)))
    arxiv_matches = sorted(set(re.findall(r"\barXiv:\s*([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", text, flags=re.IGNORECASE)))
    urls = sorted(set(re.findall(r"https?://[^\s)>\]]+", text)))
    nonempty = [line.strip() for line in text.splitlines() if line.strip()]
    title = next((line for line in nonempty if 12 <= len(line) <= 220), path.stem)
    references = []
    for value in doi_matches:
        references.append({"type": "doi", "value": value})
    for value in arxiv_matches:
        references.append({"type": "arxiv", "value": value})
    for value in urls[:10]:
        references.append({"type": "url", "value": value})
    primary = doi_matches[0] if doi_matches else f"arXiv:{arxiv_matches[0]}" if arxiv_matches else urls[0] if urls else title
    return {
        "titleOrFirstLine": title,
        "doi": doi_matches[0] if doi_matches else None,
        "arxiv": arxiv_matches[0] if arxiv_matches else None,
        "url": urls[0] if urls else None,
        "primaryCitation": primary,
        "references": references,
    }


def _candidate_mentions_from_text(text: str, plan: dict[str, Any], candidate_id: str | None) -> list[str]:
    if candidate_id:
        return [candidate_id]
    lowered = text.lower()
    matches: list[str] = []
    for candidate in plan.get("selectedCandidates") or []:
        if not isinstance(candidate, dict):
            continue
        material_id = str(candidate.get("materialId") or "")
        formula = str(candidate.get("formula") or "")
        if material_id and material_id.lower() in lowered:
            matches.append(material_id)
        elif formula and formula.lower() in lowered and material_id:
            matches.append(material_id)
    return _unique_ordered(matches)


def _extract_literature_property_values(text: str) -> dict[str, Any]:
    patterns = {
        "bandGapEv": r"band\s+gap\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?)\s*eV",
        "dielectricTotal": r"(?:dielectric\s+constant|relative\s+permittivity|k\s*value)\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?)",
        "ionicConductivityScm": r"ionic\s+conductivity\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*S/?cm",
        "adsorptionEnergyEv": r"adsorption\s+energy\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?)\s*eV",
        "overpotentialV": r"overpotential\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?)\s*V",
        "capacityMahG": r"capacity\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?)\s*mAh/?g",
        "voltageV": r"voltage\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?)\s*V",
        "seebeckUvK": r"Seebeck\s*(?:coefficient)?\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?)\s*(?:uV/K|µV/K)",
        "zt": r"\bZT\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?)",
        "criticalTemperatureK": r"(?:critical\s+temperature|T_c|Tc)\s*(?:of|=|:)?\s*([-+]?\d+(?:\.\d+)?)\s*K",
    }
    values: dict[str, Any] = {}
    for key, pattern in patterns.items():
        value = _last_float_match(text, pattern)
        if value is not None:
            values[key] = value
    if any(word in text.lower() for word in ["contradict", "failed to reproduce", "unstable", "decomposes"]):
        values["negativeEvidenceMentioned"] = True
    return values


def _count_table_like_lines(text: str) -> int:
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.count("|") >= 2 or stripped.count(",") >= 3 or stripped.count("\t") >= 2:
            count += 1
    return count


def _parse_structured_evidence(
    path: Path,
    parser: str,
    candidate_id: str | None,
    default_status: str | None,
    source_label: str | None,
) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        parsed_rows = _read_evidence_ledger(str(path))
    else:
        parsed = json.loads(path.read_text("utf-8"))
        if isinstance(parsed, list):
            parsed_rows = [_normalize_evidence_row(item) for item in parsed if isinstance(item, dict)]
        elif isinstance(parsed, dict) and isinstance(parsed.get("evidenceRows"), list):
            parsed_rows = [_normalize_evidence_row(item) for item in parsed["evidenceRows"] if isinstance(item, dict)]
        elif isinstance(parsed, dict):
            parsed_rows = [_normalize_evidence_row(parsed)]
        else:
            parsed_rows = []
    source_type = "literature" if parser == "literature-json" else "experiment" if parser == "experiment-json" else None
    status = default_status or ("literature-supported" if parser == "literature-json" else "experimentally-supported" if parser == "experiment-json" else None)
    rows = []
    for row in parsed_rows:
        if candidate_id and not row.get("candidateId"):
            row["candidateId"] = candidate_id
        if source_type and row.get("sourceType") in {"unknown", ""}:
            row["sourceType"] = source_type
        if source_label and not row.get("source"):
            row["source"] = source_label
        if status and row.get("status") in {"unknown", ""}:
            row["status"] = status
        row.setdefault("artifactPath", str(path))
        rows.append(_normalize_evidence_row(row, candidate_id=candidate_id))
    return rows


def _parse_csv_evidence(path: Path, candidate_id: str | None, default_status: str | None, source_label: str | None) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for item in csv.DictReader(handle):
            property_values: dict[str, Any] = {}
            if item.get("propertyValues"):
                try:
                    parsed = json.loads(str(item["propertyValues"]))
                    if isinstance(parsed, dict):
                        property_values.update(parsed)
                except Exception:
                    pass
            if item.get("propertyKey"):
                property_values[str(item["propertyKey"])] = _coerce_scalar(item.get("value"))
            row = {
                "candidateId": item.get("candidateId") or candidate_id,
                "formula": item.get("formula"),
                "evidenceRequirementId": item.get("evidenceRequirementId") or item.get("requirementId"),
                "claim": item.get("claim"),
                "status": item.get("status") or default_status or "parsed-property",
                "sourceType": item.get("sourceType") or item.get("evidenceType") or "experiment",
                "source": item.get("source") or source_label,
                "confidence": item.get("confidence") or "imported-table",
                "propertyValues": property_values,
                "artifactPath": item.get("artifactPath") or str(path),
                "sourcePath": item.get("sourcePath"),
                "citation": item.get("citation"),
                "queryIds": [item["queryId"]] if item.get("queryId") else [],
            }
            rows.append(_normalize_evidence_row(
                {key: value for key, value in row.items() if value is not None and value != ""},
                candidate_id=candidate_id,
            ))
    return rows


def _parsed_evidence_row(
    *,
    plan: dict[str, Any],
    candidate_id: str | None,
    evidence_requirement_id: str,
    artifact_path: str,
    source_type: str,
    source: str,
    status: str,
    claim: str,
    property_values: dict[str, Any],
) -> dict[str, Any]:
    return _normalize_evidence_row({
        "ledgerVersion": "evidence-ledger-v1",
        "evidenceId": _safe_file_stem(f"{candidate_id or 'candidate'}-{evidence_requirement_id}-{source}").lower(),
        "candidateId": candidate_id,
        "formula": _candidate_formula_for_plan(plan, candidate_id),
        "evidenceRequirementId": evidence_requirement_id,
        "claim": claim,
        "status": status,
        "sourceType": source_type,
        "source": source,
        "confidence": "parsed-output",
        "propertyValues": property_values,
        "artifactPath": artifact_path,
        "generatedAt": int(time.time()),
    }, candidate_id=candidate_id)


def _candidate_formula_for_plan(plan: dict[str, Any], candidate_id: str | None) -> str | None:
    for candidate in plan.get("selectedCandidates") or []:
        if isinstance(candidate, dict) and str(candidate.get("materialId")) == str(candidate_id):
            return str(candidate.get("formula") or "") or None
    return None


def _infer_requirement_for_properties(plan: dict[str, Any], property_keys: list[str], fallback: str) -> str:
    wanted = set(property_keys)
    for requirement in plan.get("evidenceSchema") or []:
        if not isinstance(requirement, dict):
            continue
        keys = set(str(item) for item in requirement.get("propertyKeys") or [])
        if keys.intersection(wanted):
            return str(requirement.get("id") or fallback)
    return fallback


def _last_float_match(text: str, pattern: str) -> float | None:
    matches = re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if not matches:
        return None
    try:
        return float(matches[-1])
    except Exception:
        return None


def _qe_band_gap_ev(text: str) -> float | None:
    matches = re.findall(
        r"highest\s+occupied,\s+lowest\s+unoccupied\s+level\s*\(ev\)\s*:\s*([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )
    if matches:
        homo, lumo = matches[-1]
        return max(0.0, float(lumo) - float(homo))
    return _last_float_match(text, r"band\s*gap\s*[:=]\s*([-+]?\d+(?:\.\d+)?)\s*eV")


def _parse_dielectric_scalar(text: str) -> float | None:
    value = _last_float_match(text, r"dielectric(?:\s+constant|\s+total)?\s*[:=]\s*([-+]?\d+(?:\.\d+)?)")
    if value is not None:
        return value
    tensor_block = re.search(r"dielectric.*?tensor(.*?)(?:\n\s*\n|$)", text, flags=re.IGNORECASE | re.DOTALL)
    if not tensor_block:
        return None
    numbers = [float(item) for item in re.findall(r"[-+]?\d+(?:\.\d+)?", tensor_block.group(1))]
    if len(numbers) >= 9:
        return sum(numbers[index] for index in [0, 4, 8]) / 3.0
    return None


def _coerce_scalar(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return text


def _dedupe_evidence_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for row in rows:
        key = json.dumps({
            "candidateId": row.get("candidateId"),
            "evidenceRequirementId": row.get("evidenceRequirementId"),
            "status": row.get("status"),
            "sourceType": row.get("sourceType"),
            "source": row.get("source"),
            "artifactPath": row.get("artifactPath"),
            "propertyValues": row.get("propertyValues"),
            "citation": row.get("citation"),
        }, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _evidence_ingestion_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Evidence Ingestion",
        "",
        "## Summary",
        "",
        f"- Candidate: `{report.get('candidateId') or '-'}`",
        f"- Parser: `{report.get('parser')}`",
        f"- New evidence rows: {report.get('newEvidenceRows')}",
        f"- Total ledger rows: {report.get('totalEvidenceRows')}",
        f"- Ledger: {report.get('evidenceLedgerPath')}",
        "",
        "## Parsed Artifacts",
        "",
        "| Path | Parser | Rows |",
        "| --- | --- | ---: |",
    ]
    for item in report.get("parsedArtifacts") or []:
        lines.append(f"| {item.get('path')} | {item.get('parser')} | {item.get('evidenceRows')} |")
    if not report.get("parsedArtifacts"):
        lines.append("| - | - | 0 |")
    lines.extend([
        "",
        "## Evidence Rows",
        "",
        "| Candidate | Requirement | Status | Source Type | Properties |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in report.get("evidenceRows") or []:
        properties = ", ".join(sorted((row.get("propertyValues") or {}).keys())) if isinstance(row.get("propertyValues"), dict) else "-"
        lines.append(
            f"| {row.get('candidateId') or '-'} | {row.get('evidenceRequirementId')} | "
            f"{row.get('status')} | {row.get('sourceType')} | {properties or '-'} |"
        )
    lines.extend([
        "",
        "## Warnings",
        "",
        *([f"- {warning}" for warning in report.get("warnings") or []] or ["- No warnings."]),
        "",
    ])
    return "\n".join(lines)


def _default_claim_candidate_id(plan: dict[str, Any]) -> str | None:
    candidates = plan.get("selectedCandidates") if isinstance(plan.get("selectedCandidates"), list) else []
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("materialId"):
            return str(candidate["materialId"])
    return None


def _default_evidence_ledger_path(plan: dict[str, Any]) -> str | None:
    discovery = plan.get("autonomousDiscovery") if isinstance(plan.get("autonomousDiscovery"), dict) else {}
    if discovery.get("evidenceLedgerPath"):
        return str(discovery["evidenceLedgerPath"])
    candidate_generation = plan.get("candidateGenerationPlan") if isinstance(plan.get("candidateGenerationPlan"), dict) else {}
    auto = candidate_generation.get("autoDiscovery") if isinstance(candidate_generation.get("autoDiscovery"), dict) else {}
    if auto.get("evidenceLedgerPath"):
        return str(auto["evidenceLedgerPath"])
    return None


def _read_evidence_ledger(ledger_path: str) -> list[dict[str, Any]]:
    path = Path(ledger_path)
    if not path.exists():
        raise WorkerError("EVIDENCE_LEDGER_NOT_FOUND", f"Evidence ledger was not found: {ledger_path}")
    rows: list[dict[str, Any]] = []
    if path.suffix.lower() == ".json":
        parsed = json.loads(path.read_text("utf-8"))
        if isinstance(parsed, list):
            rows.extend(_normalize_evidence_row(item) for item in parsed if isinstance(item, dict))
        elif isinstance(parsed, dict):
            rows.append(_normalize_evidence_row(parsed))
        return rows
    for line_number, line in enumerate(path.read_text("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise WorkerError("INVALID_EVIDENCE_LEDGER", f"Invalid JSONL at {ledger_path}:{line_number}: {exc}") from exc
        if isinstance(parsed, dict):
            rows.append(_normalize_evidence_row(parsed))
    return rows


def _normalize_evidence_row(row: dict[str, Any], *, candidate_id: str | None = None) -> dict[str, Any]:
    normalized = dict(row)
    if candidate_id and not normalized.get("candidateId"):
        normalized["candidateId"] = candidate_id
    normalized["evidenceRequirementId"] = str(
        normalized.get("evidenceRequirementId")
        or normalized.get("requirementId")
        or normalized.get("id")
        or ""
    )
    normalized["status"] = str(normalized.get("status") or "unknown").strip().lower()
    normalized["sourceType"] = str(normalized.get("sourceType") or normalized.get("evidenceType") or "unknown").strip().lower()
    normalized["confidence"] = str(normalized.get("confidence") or "unspecified").strip().lower()
    property_values = normalized.get("propertyValues")
    normalized["propertyValues"] = property_values if isinstance(property_values, dict) else {}
    return normalized


def _evaluate_research_claim(
    *,
    plan: dict[str, Any],
    candidate_id: str,
    rows: list[dict[str, Any]],
    requested_claim_level: str,
    ledger_path: str | None,
    merged_ledger_path: str,
) -> dict[str, Any]:
    evidence_schema = [
        item for item in (plan.get("evidenceSchema") or [])
        if isinstance(item, dict)
    ]
    required_ids = list((plan.get("claimPolicy") or {}).get("requiredEvidenceRequirementIds") or [])
    if not required_ids:
        required_ids = [str(item.get("id")) for item in evidence_schema if item.get("requiredForClaim")]
    required = [
        requirement for requirement in evidence_schema
        if str(requirement.get("id")) in set(required_ids)
    ]
    candidate_rows = [
        row for row in rows
        if _row_candidate_matches(row, candidate_id)
    ]
    satisfied: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    warnings: list[str] = []
    for requirement in required:
        support = _supporting_rows_for_requirement(requirement, candidate_rows)
        if support:
            satisfied.append({
                "evidenceRequirementId": requirement.get("id"),
                "label": requirement.get("label"),
                "rows": [_row_ref(row) for row in support],
            })
        else:
            candidate_requirement_rows = [
                row for row in candidate_rows
                if str(row.get("evidenceRequirementId")) == str(requirement.get("id"))
            ]
            missing.append({
                "evidenceRequirementId": requirement.get("id"),
                "label": requirement.get("label"),
                "requiredEvidenceTypes": requirement.get("evidenceTypes") or [],
                "propertyKeys": requirement.get("propertyKeys") or [],
                "reason": _missing_requirement_reason(requirement, candidate_requirement_rows),
                "rowsSeen": [_row_ref(row) for row in candidate_requirement_rows],
            })
    blocking = [_row_ref(row) for row in candidate_rows if _row_blocks_claim(row)]
    conflicts = [_row_ref(row) for row in candidate_rows if _row_conflicts(row)]
    uncertainty_summary = _uncertainty_and_conflict_summary(
        plan=plan,
        candidate_id=candidate_id,
        rows=candidate_rows,
        requirements=required,
    )
    material_conflicts = uncertainty_summary.get("materialConflicts") or []
    artifact_warnings = _artifact_trace_warnings(candidate_rows)
    warnings.extend(artifact_warnings)
    current_level = _claim_level_from_evaluation(
        satisfied=satisfied,
        missing=missing,
        blocking=blocking,
        candidate_rows=candidate_rows,
    )
    if material_conflicts and current_level == "research-grade-candidate":
        current_level = "property-backed-shortlist"
    research_grade_allowed = (
        requested_claim_level == "research-grade-candidate"
        and current_level == "research-grade-candidate"
        and not missing
        and not blocking
        and not conflicts
        and not material_conflicts
        and float(uncertainty_summary.get("overallConfidenceScore") or 0.0) >= 0.72
    )
    blocked_by = [item["evidenceRequirementId"] for item in missing] + [item["evidenceId"] for item in blocking]
    blocked_by.extend(item.get("propertyKey") or item.get("reason") for item in material_conflicts if isinstance(item, dict))
    claim_status = {
        "requestedLevel": requested_claim_level,
        "currentLevel": current_level,
        "researchGradeClaimAllowed": research_grade_allowed,
        "blockedBy": [str(item) for item in blocked_by if item],
        "reason": (
            "All required evidence gates are satisfied by traceable evidence rows."
            if research_grade_allowed
            else "Research-grade claim remains blocked until missing/conflicting evidence gates are closed."
        ),
    }
    audit_certificate = _claim_audit_certificate(
        plan=plan,
        candidate_id=candidate_id,
        requested_claim_level=requested_claim_level,
        rows=candidate_rows,
        claim_status=claim_status,
        satisfied=satisfied,
        missing=missing,
        blocking=blocking,
        conflicts=conflicts,
        uncertainty_summary=uncertainty_summary,
        ledger_path=ledger_path,
        merged_ledger_path=merged_ledger_path,
    )
    return {
        "evaluationVersion": "claim-policy-evaluator-v1",
        "generatedAt": int(time.time()),
        "planId": plan.get("planId"),
        "candidateId": candidate_id,
        "ledgerPath": ledger_path,
        "mergedLedgerPath": merged_ledger_path,
        "requestedClaimLevel": requested_claim_level,
        "claimStatus": claim_status,
        "requiredEvidenceRequirementIds": required_ids,
        "satisfiedEvidence": satisfied,
        "missingEvidence": missing,
        "blockingEvidence": blocking,
        "conflictingEvidence": conflicts,
        "uncertaintySummary": uncertainty_summary,
        "auditCertificate": audit_certificate,
        "evidenceRowsReviewed": len(candidate_rows),
        "warnings": warnings,
    }


def _row_candidate_matches(row: dict[str, Any], candidate_id: str) -> bool:
    row_candidate = row.get("candidateId") or row.get("materialId")
    return not row_candidate or str(row_candidate) == candidate_id


def _uncertainty_and_conflict_summary(
    *,
    plan: dict[str, Any],
    candidate_id: str,
    rows: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
) -> dict[str, Any]:
    scored_rows = [
        {**_row_ref(row), "strengthScore": _row_strength_score(row)}
        for row in rows
    ]
    requirement_scores: list[dict[str, Any]] = []
    for requirement in requirements:
        requirement_rows = [
            row for row in rows
            if str(row.get("evidenceRequirementId")) == str(requirement.get("id"))
        ]
        scores = [_row_strength_score(row) for row in requirement_rows]
        requirement_scores.append({
            "evidenceRequirementId": requirement.get("id"),
            "rowCount": len(requirement_rows),
            "maxStrengthScore": round(max(scores), 6) if scores else 0.0,
            "meanStrengthScore": round(sum(scores) / len(scores), 6) if scores else 0.0,
            "uncertainty": round(1.0 - max(scores), 6) if scores else 1.0,
        })
    row_scores = [_row_strength_score(row) for row in rows]
    overall = sum(row_scores) / len(row_scores) if row_scores else 0.0
    material_conflicts = _numeric_property_conflicts(rows)
    explicit_conflicts = [_row_ref(row) for row in rows if _row_conflicts(row)]
    return {
        "candidateId": candidate_id,
        "planId": plan.get("planId"),
        "overallConfidenceScore": round(overall, 6),
        "overallUncertainty": round(1.0 - overall, 6),
        "requirementScores": requirement_scores,
        "rowScores": scored_rows,
        "materialConflicts": material_conflicts,
        "explicitConflictingRows": explicit_conflicts,
        "policy": {
            "researchGradeMinimumConfidenceScore": 0.72,
            "numericConflictRelativeTolerance": 0.20,
            "conflictingRowsBlockResearchGrade": True,
        },
    }


def _row_strength_score(row: dict[str, Any]) -> float:
    status = str(row.get("status") or "").lower()
    source_type = str(row.get("sourceType") or "").lower()
    confidence = str(row.get("confidence") or "").lower()
    score = 0.20
    if status in _strong_evidence_statuses(str(row.get("evidenceRequirementId") or "")):
        score += 0.28
    elif "proxy" in status or "hypothesis" in status:
        score += 0.08
    elif _row_blocks_claim(row) or _row_conflicts(row):
        score -= 0.20
    source_scores = {
        "parsed-calculation": 0.28,
        "parsed-output": 0.28,
        "dft": 0.27,
        "dfpt": 0.27,
        "md": 0.25,
        "experiment": 0.30,
        "experimental-measurement": 0.30,
        "workflow": 0.22,
        "database": 0.20,
        "materials-project": 0.20,
        "literature": 0.20,
        "citation": 0.20,
        "safety": 0.18,
        "regulatory": 0.18,
    }
    score += source_scores.get(source_type, 0.05)
    if _row_has_trace(row):
        score += 0.14
    if row.get("citationProvenance") or row.get("citation"):
        score += 0.05
    if isinstance(row.get("propertyValues"), dict) and row["propertyValues"]:
        score += 0.08
    if "parsed" in confidence or "provenance" in confidence or "workflow" in confidence:
        score += 0.05
    if _row_blocks_claim(row) or _row_conflicts(row):
        score = min(score, 0.40)
    return max(0.0, min(score, 1.0))


def _numeric_property_conflicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if _row_blocks_claim(row):
            continue
        values = row.get("propertyValues") if isinstance(row.get("propertyValues"), dict) else {}
        for key, value in values.items():
            if isinstance(value, bool) or value is None:
                continue
            try:
                numeric_value = float(value)
            except Exception:
                continue
            values_by_key[str(key)].append({"value": numeric_value, "row": row})
    conflicts: list[dict[str, Any]] = []
    for key, items in values_by_key.items():
        if len(items) < 2:
            continue
        raw_values = [item["value"] for item in items]
        minimum = min(raw_values)
        maximum = max(raw_values)
        scale = max(abs(sum(raw_values) / len(raw_values)), 1e-9)
        relative_spread = abs(maximum - minimum) / scale
        if relative_spread <= 0.20:
            continue
        conflicts.append({
            "propertyKey": key,
            "min": minimum,
            "max": maximum,
            "relativeSpread": round(relative_spread, 6),
            "reason": "numeric evidence spread exceeds tolerance",
            "rows": [_row_ref(item["row"]) for item in items],
        })
    return conflicts


def _claim_audit_certificate(
    *,
    plan: dict[str, Any],
    candidate_id: str,
    requested_claim_level: str,
    rows: list[dict[str, Any]],
    claim_status: dict[str, Any],
    satisfied: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    blocking: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    uncertainty_summary: dict[str, Any],
    ledger_path: str | None,
    merged_ledger_path: str,
) -> dict[str, Any]:
    row_refs = [_row_ref(row) for row in rows]
    return {
        "certificateVersion": "research-claim-audit-v1",
        "generatedAt": int(time.time()),
        "planId": plan.get("planId"),
        "candidateId": candidate_id,
        "requestedClaimLevel": requested_claim_level,
        "decision": "allow" if claim_status.get("researchGradeClaimAllowed") else "block",
        "claimStatus": claim_status,
        "ledgerDigest": _ledger_digest(rows),
        "ledgerPath": ledger_path,
        "mergedLedgerPath": merged_ledger_path,
        "gateSummary": {
            "satisfied": len(satisfied),
            "missing": len(missing),
            "blocking": len(blocking),
            "conflicting": len(conflicts) + len(uncertainty_summary.get("materialConflicts") or []),
        },
        "uncertaintySummary": {
            "overallConfidenceScore": uncertainty_summary.get("overallConfidenceScore"),
            "overallUncertainty": uncertainty_summary.get("overallUncertainty"),
            "materialConflictCount": len(uncertainty_summary.get("materialConflicts") or []),
        },
        "reviewChecklist": [
            {
                "item": "all-required-evidence-gates-closed",
                "passed": not missing,
            },
            {
                "item": "no-blocking-or-conflicting-evidence",
                "passed": not blocking and not conflicts and not uncertainty_summary.get("materialConflicts"),
            },
            {
                "item": "traceable-source-artifacts-or-citations",
                "passed": all(_row_has_trace(row) for row in rows),
            },
            {
                "item": "confidence-above-research-grade-threshold",
                "passed": float(uncertainty_summary.get("overallConfidenceScore") or 0.0) >= 0.72,
            },
        ],
        "evidenceRows": row_refs,
    }


def _ledger_digest(rows: list[dict[str, Any]]) -> str:
    canonical = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _supporting_rows_for_requirement(requirement: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if str(row.get("evidenceRequirementId")) != str(requirement.get("id")):
            continue
        ok, _reason = _row_supports_requirement(row, requirement)
        if ok:
            result.append(row)
    return result


def _row_supports_requirement(row: dict[str, Any], requirement: dict[str, Any]) -> tuple[bool, str]:
    status = str(row.get("status") or "").lower()
    if _row_blocks_claim(row) or _row_conflicts(row):
        return False, "row blocks or conflicts with the claim"
    requirement_id = str(requirement.get("id") or "")
    evidence_types = set(str(item).lower() for item in requirement.get("evidenceTypes") or [])
    if requirement_id == "database-provenance":
        if row.get("sourceType") in {"database", "materials-project"} and "dev-fixture" not in str(row.get("source") or "").lower():
            return True, "live database provenance is attached"
        return False, "database provenance must come from a live database source"
    if status not in _strong_evidence_statuses(requirement_id):
        return False, f"status '{status}' is not strong enough"
    source_type = str(row.get("sourceType") or "").lower()
    if not _source_type_satisfies(source_type, evidence_types):
        return False, f"sourceType '{source_type}' does not satisfy {sorted(evidence_types)}"
    if not _row_has_trace(row):
        return False, "row lacks source/citation/artifact trace"
    property_keys = [str(item) for item in requirement.get("propertyKeys") or []]
    if property_keys and not _row_has_property_values(row, property_keys):
        return False, "row lacks required property values"
    return True, "row satisfies requirement"


def _strong_evidence_statuses(requirement_id: str) -> set[str]:
    base = {
        "pass",
        "passed",
        "validated",
        "supports-research-grade-claim",
        "supports-property-claim",
        "property-backed",
        "parsed-property",
        "experimentally-supported",
        "dft-confirmed",
        "literature-supported",
        "safety-reviewed",
        "workflow-reproduced",
    }
    if requirement_id in {"literature-benchmark", "synthesis-safety", "environmental-health-safety"}:
        base.add("supports-candidate-hypothesis")
    return base


def _source_type_satisfies(source_type: str, evidence_types: set[str]) -> bool:
    if "database" in evidence_types and source_type in {"database", "materials-project"}:
        return True
    if "literature" in evidence_types and source_type in {"literature", "citation"}:
        return True
    if "safety" in evidence_types and source_type in {"safety", "literature", "experiment", "regulatory"}:
        return True
    if "experiment" in evidence_types and source_type in {"experiment", "experimental-measurement"}:
        return True
    if evidence_types.intersection({"dft", "dfpt", "md", "workflow"}) and source_type in {
        "parsed-calculation",
        "parsed-output",
        "dft",
        "dfpt",
        "md",
        "workflow",
        "experiment",
    }:
        return True
    return False


def _row_has_trace(row: dict[str, Any]) -> bool:
    return any(row.get(key) for key in ["source", "artifactPath", "sourcePath", "citation", "queryIds"])


def _row_has_property_values(row: dict[str, Any], property_keys: list[str]) -> bool:
    values = row.get("propertyValues") if isinstance(row.get("propertyValues"), dict) else {}
    if not values:
        return False
    return any(key in values and values.get(key) is not None for key in property_keys)


def _row_blocks_claim(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").lower()
    requirement_id = str(row.get("evidenceRequirementId") or "")
    if requirement_id == "claim-policy":
        return False
    return "block" in status or status in {"fail", "failed", "rejected"}


def _row_conflicts(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").lower()
    return "contradict" in status or "conflict" in status


def _missing_requirement_reason(requirement: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "no evidence row exists for this required evidence gate"
    reasons = []
    for row in rows:
        ok, reason = _row_supports_requirement(row, requirement)
        if not ok:
            reasons.append(reason)
    return "; ".join(sorted(set(reasons))) or "evidence rows exist but did not satisfy the gate"


def _artifact_trace_warnings(rows: list[dict[str, Any]]) -> list[str]:
    warnings = []
    for row in rows:
        for key in ["artifactPath", "sourcePath"]:
            value = row.get(key)
            if not value or not isinstance(value, str):
                continue
            path = Path(value)
            if path.is_absolute() and not path.exists():
                warnings.append(f"Evidence artifact does not exist: {value}")
    return warnings


def _claim_level_from_evaluation(
    *,
    satisfied: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    blocking: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> str:
    if blocking:
        return "candidate-hypothesis"
    if not missing:
        return "research-grade-candidate"
    if any(str(row.get("sourceType") or "").lower() in {"parsed-calculation", "parsed-output", "dft", "dfpt", "md", "experiment"} for row in candidate_rows):
        return "property-backed-shortlist"
    if satisfied:
        return "proxy-shortlist"
    return "candidate-hypothesis"


def _row_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidenceId": row.get("evidenceId") or _safe_file_stem(f"{row.get('candidateId', 'candidate')}-{row.get('evidenceRequirementId', 'evidence')}").lower(),
        "candidateId": row.get("candidateId"),
        "evidenceRequirementId": row.get("evidenceRequirementId"),
        "status": row.get("status"),
        "sourceType": row.get("sourceType"),
        "source": row.get("source"),
        "confidence": row.get("confidence"),
        "artifactPath": row.get("artifactPath"),
        "sourcePath": row.get("sourcePath"),
        "citation": row.get("citation"),
        "propertyKeys": sorted((row.get("propertyValues") or {}).keys()) if isinstance(row.get("propertyValues"), dict) else [],
    }


def _claim_evaluation_markdown(review: dict[str, Any]) -> str:
    status = review.get("claimStatus") or {}
    lines = [
        f"# Research Claim Evaluation: {review.get('candidateId')}",
        "",
        "## Status",
        "",
        f"- Requested level: `{status.get('requestedLevel')}`",
        f"- Current level: `{status.get('currentLevel')}`",
        f"- Research-grade claim allowed: `{str(status.get('researchGradeClaimAllowed')).lower()}`",
        f"- Reason: {status.get('reason')}",
        "",
        "## Satisfied Evidence",
        "",
        "| Requirement | Rows |",
        "| --- | ---: |",
    ]
    for item in review.get("satisfiedEvidence") or []:
        lines.append(f"| {item.get('evidenceRequirementId')} | {len(item.get('rows') or [])} |")
    if not review.get("satisfiedEvidence"):
        lines.append("| - | 0 |")
    lines.extend([
        "",
        "## Missing Evidence",
        "",
        "| Requirement | Reason |",
        "| --- | --- |",
    ])
    for item in review.get("missingEvidence") or []:
        lines.append(f"| {item.get('evidenceRequirementId')} | {item.get('reason')} |")
    if not review.get("missingEvidence"):
        lines.append("| - | - |")
    lines.extend([
        "",
        "## Blocking Evidence",
        "",
        "| Evidence | Requirement | Status |",
        "| --- | --- | --- |",
    ])
    for item in review.get("blockingEvidence") or []:
        lines.append(f"| {item.get('evidenceId')} | {item.get('evidenceRequirementId')} | {item.get('status')} |")
    if not review.get("blockingEvidence"):
        lines.append("| - | - | - |")
    uncertainty = review.get("uncertaintySummary") or {}
    audit = review.get("auditCertificate") or {}
    lines.extend([
        "",
        "## Uncertainty And Conflicts",
        "",
        f"- Overall confidence score: `{uncertainty.get('overallConfidenceScore', 0)}`",
        f"- Overall uncertainty: `{uncertainty.get('overallUncertainty', 1)}`",
        f"- Numeric material conflicts: {len(uncertainty.get('materialConflicts') or [])}",
        "",
        "| Requirement | Rows | Max Strength | Uncertainty |",
        "| --- | ---: | ---: | ---: |",
    ])
    for item in uncertainty.get("requirementScores") or []:
        lines.append(
            f"| {item.get('evidenceRequirementId')} | {item.get('rowCount')} | "
            f"{item.get('maxStrengthScore')} | {item.get('uncertainty')} |"
        )
    if not uncertainty.get("requirementScores"):
        lines.append("| - | 0 | 0 | 1 |")
    lines.extend([
        "",
        "## Audit Certificate",
        "",
        f"- Certificate version: `{audit.get('certificateVersion', '-')}`",
        f"- Decision: `{audit.get('decision', '-')}`",
        f"- Ledger digest: `{audit.get('ledgerDigest', '-')}`",
        "",
        "| Checklist Item | Passed |",
        "| --- | --- |",
    ])
    for item in audit.get("reviewChecklist") or []:
        lines.append(f"| {item.get('item')} | `{str(item.get('passed')).lower()}` |")
    if not audit.get("reviewChecklist"):
        lines.append("| - | - |")
    lines.extend([
        "",
        "## Artifacts",
        "",
        f"- Ledger reviewed: {review.get('ledgerPath') or '-'}",
        f"- Merged claim ledger: {review.get('mergedLedgerPath') or '-'}",
        "",
        "## Warnings",
        "",
        *([f"- {warning}" for warning in review.get("warnings") or []] or ["- No warnings."]),
        "",
    ])
    return "\n".join(lines)


def _normalize_research_budget(budget: dict[str, Any]) -> dict[str, Any]:
    max_candidates = int(budget.get("maxCandidates") or 5)
    max_calculations = int(budget.get("maxCalculations") or 12)
    max_wall_time_hours = float(budget.get("maxWallTimeHours") or 48.0)
    compute_budget_usd = budget.get("computeBudgetUsd")
    return {
        "maxCandidates": max(1, min(max_candidates, 50)),
        "maxCalculations": max(1, min(max_calculations, 500)),
        "maxWallTimeHours": max(0.25, max_wall_time_hours),
        "computeBudgetUsd": float(compute_budget_usd) if isinstance(compute_budget_usd, (int, float)) else None,
        "maxLoopIterations": max(1, min(int(budget.get("maxLoopIterations") or 2), 20)),
        "allowExpensiveCalculations": bool(budget.get("allowExpensiveCalculations", False)),
    }


def _load_research_plan(payload: dict[str, Any]) -> dict[str, Any]:
    plan = payload.get("plan")
    if isinstance(plan, dict):
        return plan
    plan_path = ensure_string(payload.get("planPath"), field="planPath", required=False)
    if plan_path:
        path = Path(plan_path)
        if not path.exists():
            raise WorkerError("PLAN_NOT_FOUND", f"Research plan was not found: {plan_path}")
        return ensure_dict(json.loads(path.read_text("utf-8")), field="plan")
    raise WorkerError("INVALID_PARAMS", "execute_research_plan requires either plan or planPath.")


def _execute_dev_smoke_plan(
    *,
    plan: dict[str, Any],
    artifact_dir: Path,
    api_key: str | None,
    max_steps: int,
    allow_blocked_dev_smoke: bool,
) -> dict[str, Any]:
    run_id = f"{plan.get('planId', 'research-plan')}-dev-smoke-{int(time.time() * 1000)}"
    run_dir = artifact_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    selected_by_id = {
        str(candidate.get("materialId")): candidate
        for candidate in plan.get("selectedCandidates") or []
        if candidate.get("materialId")
    }
    completed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    warnings: list[str] = [
        "dev-smoke backend validates execution plumbing only; it does not generate property evidence or reranking updates."
    ]

    for step in (plan.get("calculationQueue") or [])[: max(0, max_steps)]:
        if not isinstance(step, dict):
            continue
        status = str(step.get("status") or "planned")
        calculation_id = str(step.get("calculationId") or step.get("id") or f"calculation-{len(completed) + len(skipped) + 1}")
        if status.startswith("blocked") and not allow_blocked_dev_smoke:
            skipped.append({
                "calculationId": calculation_id,
                "materialId": step.get("materialId"),
                "status": "skipped-blocked",
                "reason": step.get("blockedReason") or "calculation is blocked by the plan approval gates",
            })
            continue

        material_id = str(step.get("materialId") or "")
        candidate = selected_by_id.get(material_id, {"materialId": material_id, "formula": step.get("formula")})
        result = _run_dev_smoke_step(step, candidate, plan, api_key=api_key)
        result_path = run_dir / f"{_safe_file_stem(calculation_id)}.json"
        result["resultPath"] = str(result_path)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        completed.append(result)

    manifest = {
        "runId": run_id,
        "backend": "dev-smoke",
        "planId": plan.get("planId"),
        "preset": plan.get("preset"),
        "generatedAt": int(time.time()),
        "completedCalculations": len(completed),
        "skippedCalculations": len(skipped),
        "allowBlockedDevSmoke": allow_blocked_dev_smoke,
        "propertyUpdates": [],
        "completed": completed,
        "skipped": skipped,
        "warnings": warnings,
    }
    manifest_path = run_dir / "execution-manifest.json"
    report_path = run_dir / "execution-report.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_dev_smoke_execution_markdown(manifest), encoding="utf-8")
    return {
        "runId": run_id,
        "backend": "dev-smoke",
        "statusSummary": "Executed dev-smoke backend",
        "manifestPath": str(manifest_path),
        "reportPath": str(report_path),
        "resultPaths": [str(Path(result["resultPath"])) for result in completed],
        "inputPaths": [],
        "completedCalculations": len(completed),
        "preparedCalculations": 0,
        "submittedCalculations": 0,
        "skippedCalculations": len(skipped),
        "propertyUpdates": [],
        "warnings": warnings,
    }


def _execute_external_backend_plan(
    *,
    plan: dict[str, Any],
    artifact_dir: Path,
    api_key: str | None,
    backend: str,
    max_steps: int,
    execution_mode: str,
    allow_execution: bool,
    backend_config: dict[str, Any],
    execution_manifest_path: str | None = None,
) -> dict[str, Any]:
    if execution_mode not in {"prepare", "submit", "monitor"}:
        raise WorkerError("INVALID_PARAMS", "executionMode must be 'prepare', 'submit', or 'monitor'.")
    if execution_mode == "monitor":
        return _monitor_external_backend_execution(
            plan=plan,
            artifact_dir=artifact_dir,
            backend=backend,
            backend_config=backend_config,
            execution_manifest_path=execution_manifest_path,
        )
    run_id = f"{plan.get('planId', 'research-plan')}-{backend}-{int(time.time() * 1000)}"
    run_dir = artifact_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    selected_by_id = {
        str(candidate.get("materialId")): candidate
        for candidate in plan.get("selectedCandidates") or []
        if candidate.get("materialId")
    }
    prepared: list[dict[str, Any]] = []
    submitted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    result_paths: list[str] = []
    input_paths: list[str] = []
    warnings: list[str] = []
    allow_blocked_steps = backend_config.get("allowBlockedSteps") is True
    if execution_mode == "submit" and not allow_execution:
        warnings.append("executionMode=submit was requested, but allowExecution=false; prepared inputs without launching external jobs.")
        execution_mode = "prepare"

    for step in (plan.get("calculationQueue") or [])[: max(0, max_steps)]:
        if not isinstance(step, dict):
            continue
        calculation_id = str(step.get("calculationId") or step.get("id") or f"calculation-{len(prepared) + len(skipped) + 1}")
        if step.get("executionBackend") not in {None, "external-backend", "materials-lab"}:
            skipped.append({
                "calculationId": calculation_id,
                "materialId": step.get("materialId"),
                "status": "skipped-non-external-step",
                "reason": f"Step targets {step.get('executionBackend')} rather than the {backend} adapter.",
            })
            continue
        material_id = str(step.get("materialId") or "")
        candidate = selected_by_id.get(material_id, {"materialId": material_id, "formula": step.get("formula")})
        step_dir = run_dir / _safe_file_stem(calculation_id)
        step_dir.mkdir(parents=True, exist_ok=True)
        try:
            prep = _prepare_external_backend_step(
                backend=backend,
                step=step,
                candidate=candidate,
                plan=plan,
                step_dir=step_dir,
                api_key=api_key,
                backend_config=backend_config,
            )
        except WorkerError as exc:
            skipped.append({
                "calculationId": calculation_id,
                "materialId": material_id,
                "status": "skipped-prepare-failed",
                "reason": exc.message,
            })
            warnings.append(f"{calculation_id}: {exc.message}")
            continue
        prepared.append(prep)
        result_paths.append(prep["stepManifestPath"])
        input_paths.extend(prep["inputPaths"])
        if execution_mode == "submit":
            status = str(step.get("status") or "planned")
            if status.startswith("blocked") and not allow_blocked_steps:
                submit = _submission_result(
                    calculation_id,
                    "not-submitted",
                    "Step is blocked by the research plan approval gates; set backendConfig.allowBlockedSteps=true after human approval to submit it.",
                )
            else:
                submit = _submit_external_backend_step(backend=backend, prepared_step=prep, backend_config=backend_config)
            submitted.append(submit)
            if submit.get("submissionManifestPath"):
                result_paths.append(submit["submissionManifestPath"])
            if submit.get("status") != "submitted":
                warnings.append(f"{calculation_id}: {submit.get('message', 'submission did not start')}")

    manifest = {
        "runId": run_id,
        "backend": backend,
        "executionMode": execution_mode,
        "allowBlockedSteps": allow_blocked_steps,
        "planId": plan.get("planId"),
        "preset": plan.get("preset"),
        "generatedAt": int(time.time()),
        "preparedCalculations": len(prepared),
        "submittedCalculations": sum(1 for item in submitted if item.get("status") == "submitted"),
        "completedCalculations": 0,
        "skippedCalculations": len(skipped),
        "prepared": prepared,
        "submitted": submitted,
        "skipped": skipped,
        "propertyUpdates": [],
        "warnings": warnings,
    }
    manifest_path = run_dir / "execution-manifest.json"
    report_path = run_dir / "execution-report.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_external_execution_markdown(manifest), encoding="utf-8")
    status_summary = f"Submitted {backend} backend" if execution_mode == "submit" else f"Prepared {backend} backend"
    return {
        "runId": run_id,
        "backend": backend,
        "statusSummary": status_summary,
        "manifestPath": str(manifest_path),
        "reportPath": str(report_path),
        "resultPaths": [str(Path(path)) for path in result_paths],
        "inputPaths": [str(Path(path)) for path in input_paths],
        "completedCalculations": 0,
        "preparedCalculations": len(prepared),
        "submittedCalculations": sum(1 for item in submitted if item.get("status") == "submitted"),
        "skippedCalculations": len(skipped),
        "propertyUpdates": [],
        "rerankingPayload": {
            "criteriaPatch": {
                **((plan.get("rerankingPolicy") or {}).get("criteriaPatch") or {}),
                "screeningLevel": "property-backed-screen",
            },
            "candidates": [],
            "note": "External backend preparation does not produce parsed propertyUpdates until completed calculations are parsed.",
        },
        "warnings": warnings,
    }


def _monitor_external_backend_execution(
    *,
    plan: dict[str, Any],
    artifact_dir: Path,
    backend: str,
    backend_config: dict[str, Any],
    execution_manifest_path: str | None,
) -> dict[str, Any]:
    manifest_ref = (
        execution_manifest_path
        or backend_config.get("executionManifestPath")
        or backend_config.get("manifestPath")
    )
    if not manifest_ref:
        raise WorkerError(
            "INVALID_PARAMS",
            "executionMode=monitor requires executionManifestPath or backendConfig.executionManifestPath.",
            hint="Pass the execution-manifest.json produced by prepare/submit.",
        )
    manifest_path = Path(str(manifest_ref))
    if not manifest_path.exists():
        raise WorkerError("EXECUTION_MANIFEST_NOT_FOUND", f"Execution manifest was not found: {manifest_path}")

    prior_manifest = ensure_dict(json.loads(manifest_path.read_text("utf-8")), field="executionManifest")
    run_id = f"{prior_manifest.get('runId', plan.get('planId', 'research-plan'))}-monitor-{int(time.time() * 1000)}"
    run_dir = artifact_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    monitored: list[dict[str, Any]] = []
    parsed_rows: list[dict[str, Any]] = []
    parsed_artifacts: list[dict[str, Any]] = []
    parse_outputs = backend_config.get("parseOutputs", True) is not False

    for step in prior_manifest.get("prepared") or []:
        if not isinstance(step, dict):
            continue
        step_manifest_path = Path(str(step.get("stepManifestPath") or ""))
        step_dir = step_manifest_path.parent if step_manifest_path.exists() else Path(str(step.get("executionScript") or ".")).parent
        outputs = _backend_output_candidates(step_dir, backend)
        status = _backend_step_observed_status(outputs, backend)
        record = {
            "calculationId": step.get("calculationId"),
            "materialId": step.get("materialId"),
            "formula": step.get("formula"),
            "backend": backend,
            "status": status,
            "stepDir": str(step_dir),
            "outputPaths": [str(path) for path in outputs],
            "evidenceRowsParsed": 0,
        }
        if parse_outputs:
            for output_path in outputs:
                rows, record_warnings, parser_used = _parse_evidence_artifact(
                    path=output_path,
                    parser=str(backend_config.get("parser") or "auto"),
                    plan=plan,
                    candidate_id=ensure_string(step.get("materialId"), field="materialId", required=False),
                    evidence_requirement_id=ensure_string(step.get("evidenceRequirementId"), field="evidenceRequirementId", required=False),
                    default_status=ensure_string(backend_config.get("defaultStatus"), field="defaultStatus", required=False),
                    source_label=ensure_string(backend_config.get("sourceLabel"), field="sourceLabel", required=False) or backend,
                )
                if rows:
                    parsed_rows.extend(rows)
                    parsed_artifacts.append({
                        "path": str(output_path),
                        "parser": parser_used,
                        "evidenceRows": len(rows),
                    })
                    record["evidenceRowsParsed"] = int(record["evidenceRowsParsed"]) + len(rows)
                warnings.extend(record_warnings)
        monitored.append(record)

    evidence_ledger_path = ensure_string(backend_config.get("evidenceLedgerPath"), field="evidenceLedgerPath", required=False)
    output_ledger_path = Path(str(backend_config.get("outputLedgerPath") or run_dir / "monitor-evidence-ledger.jsonl"))
    prior_rows = _read_evidence_ledger(evidence_ledger_path) if evidence_ledger_path and Path(evidence_ledger_path).exists() else []
    merged_rows = _dedupe_evidence_rows([*prior_rows, *parsed_rows])
    output_ledger_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in merged_rows), encoding="utf-8")

    claim_reviews: list[dict[str, Any]] = []
    if backend_config.get("claimReview") is True and merged_rows:
        for candidate_id in _candidate_ids_for_claim_review(plan, merged_rows):
            review = _evaluate_research_claim(
                plan=plan,
                candidate_id=candidate_id,
                rows=merged_rows,
                requested_claim_level=str(backend_config.get("requestedClaimLevel") or "research-grade-candidate"),
                ledger_path=evidence_ledger_path,
                merged_ledger_path=str(output_ledger_path),
            )
            review_path = run_dir / f"{_safe_file_stem(candidate_id)}-claim-review.json"
            report_path = run_dir / f"{_safe_file_stem(candidate_id)}-claim-review.md"
            review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            report_path.write_text(_claim_evaluation_markdown(review), encoding="utf-8")
            claim_reviews.append({
                "candidateId": candidate_id,
                "claimStatus": review["claimStatus"],
                "reviewPath": str(review_path),
                "reportPath": str(report_path),
            })

    completed = sum(1 for item in monitored if item.get("status") == "completed")
    failed = sum(1 for item in monitored if item.get("status") == "failed")
    manifest = {
        "runId": run_id,
        "backend": backend,
        "executionMode": "monitor",
        "sourceExecutionManifestPath": str(manifest_path),
        "planId": plan.get("planId"),
        "generatedAt": int(time.time()),
        "monitoredCalculations": len(monitored),
        "completedCalculations": completed,
        "failedCalculations": failed,
        "parsedEvidenceRows": len(parsed_rows),
        "evidenceLedgerPath": str(output_ledger_path),
        "monitored": monitored,
        "parsedArtifacts": parsed_artifacts,
        "claimReviews": claim_reviews,
        "warnings": warnings,
    }
    monitor_manifest_path = run_dir / "monitor-manifest.json"
    monitor_report_path = run_dir / "monitor-report.md"
    monitor_manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    monitor_report_path.write_text(_monitor_execution_markdown(manifest), encoding="utf-8")
    result_paths = [
        str(monitor_manifest_path),
        str(monitor_report_path),
        str(output_ledger_path),
        *[item["reviewPath"] for item in claim_reviews],
        *[item["reportPath"] for item in claim_reviews],
    ]
    return {
        "runId": run_id,
        "backend": backend,
        "statusSummary": f"Monitored {backend} backend",
        "manifestPath": str(monitor_manifest_path),
        "reportPath": str(monitor_report_path),
        "resultPaths": result_paths,
        "inputPaths": [],
        "completedCalculations": completed,
        "preparedCalculations": int(prior_manifest.get("preparedCalculations") or len(prior_manifest.get("prepared") or [])),
        "submittedCalculations": int(prior_manifest.get("submittedCalculations") or 0),
        "skippedCalculations": int(prior_manifest.get("skippedCalculations") or 0),
        "propertyUpdates": [],
        "parsedEvidenceRows": len(parsed_rows),
        "evidenceLedgerPath": str(output_ledger_path),
        "claimReviews": claim_reviews,
        "warnings": warnings,
    }


def _backend_output_candidates(step_dir: Path, backend: str) -> list[Path]:
    if not step_dir.exists():
        return []
    names_by_backend = {
        "quantum-espresso": ["pw.scf.out", "ph.dielectric.out", "ph.gamma.out", "pp.potential.out", "bands.out", "dos.out"],
        "vasp": ["OUTCAR", "vasprun.xml", "vasp.out", "OSZICAR", "DOSCAR", "EIGENVAL"],
        "atomate2": ["taskdoc.json", "jobflow_output.json", "vasprun.xml", "OUTCAR"],
        "aiida": ["aiida.out", "retrieved/pw.scf.out", "retrieved/aiida.out"],
    }
    candidates: list[Path] = []
    for name in names_by_backend.get(backend, []):
        path = step_dir / name
        if path.exists() and path.is_file():
            candidates.append(path)
    for path in step_dir.glob("*.out"):
        if path.is_file() and path not in candidates:
            candidates.append(path)
    for path in step_dir.glob("*.xml"):
        if path.is_file() and path not in candidates:
            candidates.append(path)
    return candidates


def _backend_step_observed_status(outputs: list[Path], backend: str) -> str:
    if not outputs:
        return "waiting-for-outputs"
    combined = "\n".join(path.read_text("utf-8", errors="replace")[-5000:] for path in outputs if path.exists())
    lowered = combined.lower()
    if any(marker in lowered for marker in ["error", "traceback", "segmentation fault", "fatal"]):
        return "failed"
    if backend == "quantum-espresso" and "job done" in lowered:
        return "completed"
    if backend == "vasp" and any(marker in combined for marker in ["TOTEN", "Voluntary context switches", "</modeling>"]):
        return "completed"
    return "outputs-detected"


def _candidate_ids_for_claim_review(plan: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    ids = [
        str(candidate.get("materialId"))
        for candidate in plan.get("selectedCandidates") or []
        if isinstance(candidate, dict) and candidate.get("materialId")
    ]
    for row in rows:
        candidate_id = row.get("candidateId") or row.get("materialId")
        if candidate_id and str(candidate_id) not in ids:
            ids.append(str(candidate_id))
    return ids[:10]


def _monitor_execution_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        f"# Backend Monitor: {manifest.get('backend')}",
        "",
        "## Summary",
        "",
        f"- Source execution manifest: {manifest.get('sourceExecutionManifestPath')}",
        f"- Monitored calculations: {manifest.get('monitoredCalculations')}",
        f"- Completed calculations: {manifest.get('completedCalculations')}",
        f"- Failed calculations: {manifest.get('failedCalculations')}",
        f"- Parsed evidence rows: {manifest.get('parsedEvidenceRows')}",
        f"- Evidence ledger: {manifest.get('evidenceLedgerPath')}",
        "",
        "## Calculations",
        "",
        "| Calculation | Material | Status | Outputs | Parsed Rows |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for item in manifest.get("monitored") or []:
        lines.append(
            f"| {item.get('calculationId')} | {item.get('materialId') or '-'} | {item.get('status')} | "
            f"{len(item.get('outputPaths') or [])} | {item.get('evidenceRowsParsed')} |"
        )
    lines.extend([
        "",
        "## Claim Reviews",
        "",
        "| Candidate | Current Level | Research-grade Allowed |",
        "| --- | --- | --- |",
    ])
    for item in manifest.get("claimReviews") or []:
        status = item.get("claimStatus") or {}
        lines.append(
            f"| {item.get('candidateId')} | {status.get('currentLevel')} | "
            f"{str(status.get('researchGradeClaimAllowed')).lower()} |"
        )
    if not manifest.get("claimReviews"):
        lines.append("| - | - | - |")
    lines.extend([
        "",
        "## Warnings",
        "",
        *([f"- {warning}" for warning in manifest.get("warnings") or []] or ["- No warnings."]),
        "",
    ])
    return "\n".join(lines)


def _prepare_external_backend_step(
    *,
    backend: str,
    step: dict[str, Any],
    candidate: dict[str, Any],
    plan: dict[str, Any],
    step_dir: Path,
    api_key: str | None,
    backend_config: dict[str, Any],
) -> dict[str, Any]:
    material = _fetch_material_for_backend(
        str(candidate.get("materialId") or ""),
        str(candidate.get("formula") or step.get("formula") or ""),
        api_key=api_key,
        allow_dev_fixtures=backend_config.get("allowDevFixtures") is True,
    )
    structure_data = material.get("structure") if isinstance(material, dict) else None
    structure_paths = _write_backend_structure_files(structure_data, material, step_dir)
    if str(step.get("id") or "") == "structure-preflight":
        input_paths = [_write_structure_preflight_note(step, material, structure_paths, step_dir)]
    elif backend == "quantum-espresso":
        input_paths = _write_quantum_espresso_inputs(step, material, structure_data, step_dir, backend_config)
    elif backend == "vasp":
        input_paths = _write_vasp_inputs(step, material, structure_data, step_dir, backend_config)
    elif backend == "atomate2":
        input_paths = _write_atomate2_inputs(step, material, structure_paths, step_dir, backend_config)
    elif backend == "aiida":
        input_paths = _write_aiida_inputs(step, material, structure_paths, step_dir, backend_config)
    else:
        raise WorkerError("BACKEND_NOT_AVAILABLE", f"Unsupported backend: {backend}")
    all_inputs = [*structure_paths.values(), *input_paths]
    step_manifest = {
        "calculationId": step.get("calculationId"),
        "backend": backend,
        "status": "prepared",
        "materialId": material.get("materialId"),
        "formula": material.get("formula"),
        "calculationType": step.get("id"),
        "evidenceRequirementId": step.get("evidenceRequirementId"),
        "label": step.get("label"),
        "costClass": step.get("costClass"),
        "writesProperties": step.get("writesProperties") or [],
        "inputPaths": all_inputs,
        "structurePaths": structure_paths,
        "executionScript": next((item for item in input_paths if item.endswith(("run.sh", "submit.sh", "atomate2_flow.py", "aiida_submit.py"))), None),
        "provenance": {
            "backend": backend,
            "stage": "input-preparation",
            "generatedAt": int(time.time()),
            "requiresExternalCode": True,
            "parsedPropertiesAvailable": False,
        },
    }
    manifest_path = step_dir / "step-manifest.json"
    step_manifest["stepManifestPath"] = str(manifest_path)
    manifest_path.write_text(json.dumps(step_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return step_manifest


def _fetch_material_for_backend(material_id: str, formula: str, *, api_key: str | None, allow_dev_fixtures: bool = False) -> dict[str, Any]:
    if material_id:
        try:
            material, _used_offline = fetch_material(material_id, api_key=api_key, allow_offline=allow_dev_fixtures)
            summary = _candidate_summary(material)
            summary["structure"] = material.get("structure")
            return summary
        except Exception:
            pass
    return {"materialId": material_id, "formula": formula, "source": "materials-project", "structure": None}


def _write_backend_structure_files(structure_data: Any, material: dict[str, Any], step_dir: Path) -> dict[str, str]:
    paths: dict[str, str] = {}
    if isinstance(structure_data, dict):
        json_path = step_dir / "structure.json"
        json_path.write_text(json.dumps(structure_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths["structureJson"] = str(json_path)
        cif_path = write_cif(structure_data, str(step_dir / "structure.cif"))
        if cif_path:
            paths["structureCif"] = cif_path
        if Poscar is not None and Structure is not None:
            try:
                poscar_path = step_dir / "POSCAR"
                Poscar(Structure.from_dict(structure_data)).write_file(str(poscar_path))
                paths["poscar"] = str(poscar_path)
            except Exception:
                pass
        if "poscar" not in paths:
            poscar_path = _write_simple_poscar(structure_data, material, step_dir / "POSCAR")
            if poscar_path:
                paths["poscar"] = poscar_path
    else:
        note_path = step_dir / "structure-unavailable.md"
        note_path.write_text(
            "\n".join([
                "# Structure Unavailable",
                "",
                f"- materialId: {material.get('materialId')}",
                f"- formula: {material.get('formula')}",
                "- The backend adapter prepared template inputs, but a real run requires a resolved structure.",
                "",
            ]),
            encoding="utf-8",
        )
        paths["structureNote"] = str(note_path)
    return paths


def _write_simple_poscar(structure_data: Any, material: dict[str, Any], output_path: Path) -> str | None:
    atoms = _structure_atoms_for_input(structure_data, material)
    elements = _unique_ordered([atom["element"] for atom in atoms]) or _composition_elements(material)
    if not atoms or not elements:
        return None
    grouped = {element: [atom for atom in atoms if atom["element"] == element] for element in elements}
    lines = [
        str(material.get("formula") or material.get("materialId") or "OpenClaw generated structure"),
        "1.0",
    ]
    for row in _structure_lattice_for_input(structure_data):
        lines.append("  " + " ".join(f"{value:.10f}" for value in row))
    lines.append("  " + " ".join(elements))
    lines.append("  " + " ".join(str(len(grouped[element])) for element in elements))
    lines.append("Direct")
    for element in elements:
        for atom in grouped[element]:
            lines.append("  " + " ".join(f"{value:.10f}" for value in atom["coords"]))
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(output_path)


def _write_structure_preflight_note(step: dict[str, Any], material: dict[str, Any], structure_paths: dict[str, str], step_dir: Path) -> str:
    note_path = step_dir / "preflight-note.md"
    note_path.write_text(
        "\n".join([
            "# Structure Preflight",
            "",
            f"- materialId: {material.get('materialId')}",
            f"- formula: {material.get('formula')}",
            f"- calculationId: {step.get('calculationId')}",
            f"- structure artifacts: {len(structure_paths)}",
            "",
            "This step fetches and normalizes structure files for downstream backend calculations.",
            "No external electronic-structure code is required for this metadata preflight step.",
            "",
        ]),
        encoding="utf-8",
    )
    return str(note_path)


def _write_quantum_espresso_inputs(
    step: dict[str, Any],
    material: dict[str, Any],
    structure_data: Any,
    step_dir: Path,
    backend_config: dict[str, Any],
) -> list[str]:
    input_paths: list[str] = []
    scf_path = step_dir / "pw.scf.in"
    scf_path.write_text(_quantum_espresso_scf_input(material, structure_data, backend_config), encoding="utf-8")
    input_paths.append(str(scf_path))
    calc_type = str(step.get("id") or "")
    if calc_type == "dfpt-dielectric-tensor":
        ph_path = step_dir / "ph.dielectric.in"
        ph_path.write_text(_quantum_espresso_ph_input(material, backend_config), encoding="utf-8")
        input_paths.append(str(ph_path))
    elif calc_type == "phonon-stability":
        ph_path = step_dir / "ph.gamma.in"
        ph_path.write_text(_quantum_espresso_ph_input(material, backend_config, epsil=False), encoding="utf-8")
        input_paths.append(str(ph_path))
    elif calc_type == "band-alignment":
        pp_path = step_dir / "pp.potential.in"
        pp_path.write_text(_quantum_espresso_pp_input(material, backend_config), encoding="utf-8")
        input_paths.append(str(pp_path))
    pseudo_path = step_dir / "PSEUDOPOTENTIALS.required"
    pseudo_path.write_text(_pseudopotential_manifest(material), encoding="utf-8")
    run_path = step_dir / "run.sh"
    run_path.write_text(_quantum_espresso_run_script(step, backend_config), encoding="utf-8")
    run_path.chmod(0o755)
    input_paths.extend([str(pseudo_path), str(run_path)])
    return input_paths


def _write_vasp_inputs(
    step: dict[str, Any],
    material: dict[str, Any],
    structure_data: Any,
    step_dir: Path,
    backend_config: dict[str, Any],
) -> list[str]:
    input_paths: list[str] = []
    if "poscar" not in _write_backend_structure_files(structure_data, material, step_dir):
        poscar_path = step_dir / "POSCAR.template"
        poscar_path.write_text(f"{material.get('formula') or 'unknown'}\n1.0\n# Replace with real POSCAR before running VASP.\n", encoding="utf-8")
        input_paths.append(str(poscar_path))
    incar_path = step_dir / "INCAR"
    incar_path.write_text(_vasp_incar(step, backend_config), encoding="utf-8")
    kpoints_path = step_dir / "KPOINTS"
    kpoints_path.write_text(_vasp_kpoints(backend_config), encoding="utf-8")
    potcar_spec_path = step_dir / "POTCAR.spec"
    potcar_spec_path.write_text(_vasp_potcar_spec(material), encoding="utf-8")
    run_path = step_dir / "run.sh"
    run_path.write_text(_vasp_run_script(backend_config), encoding="utf-8")
    run_path.chmod(0o755)
    input_paths.extend([str(incar_path), str(kpoints_path), str(potcar_spec_path), str(run_path)])
    return input_paths


def _write_atomate2_inputs(step: dict[str, Any], material: dict[str, Any], structure_paths: dict[str, str], step_dir: Path, backend_config: dict[str, Any]) -> list[str]:
    script_path = step_dir / "atomate2_flow.py"
    script_path.write_text(_atomate2_flow_script(step, material, structure_paths, backend_config), encoding="utf-8")
    script_path.chmod(0o755)
    requirements_path = step_dir / "requirements-note.txt"
    requirements_path.write_text("Requires atomate2, jobflow, pymatgen, and a configured calculation backend.\n", encoding="utf-8")
    return [str(script_path), str(requirements_path)]


def _write_aiida_inputs(step: dict[str, Any], material: dict[str, Any], structure_paths: dict[str, str], step_dir: Path, backend_config: dict[str, Any]) -> list[str]:
    script_path = step_dir / "aiida_submit.py"
    script_path.write_text(_aiida_submit_script(step, material, structure_paths, backend_config), encoding="utf-8")
    script_path.chmod(0o755)
    profile_path = step_dir / "aiida-profile-note.txt"
    profile_path.write_text("Requires a configured AiiDA profile, code, computer, pseudopotential family, and plugin stack.\n", encoding="utf-8")
    return [str(script_path), str(profile_path)]


def _submit_external_backend_step(*, backend: str, prepared_step: dict[str, Any], backend_config: dict[str, Any]) -> dict[str, Any]:
    script = prepared_step.get("executionScript")
    calculation_id = str(prepared_step.get("calculationId") or "calculation")
    if not script:
        return _submission_result(calculation_id, "not-submitted", "No execution script was generated.")
    command = _backend_submit_command(backend, script, backend_config)
    executable = shutil.which(command[0])
    if executable is None:
        result = _submission_result(calculation_id, "not-submitted", f"Executable not found: {command[0]}")
    else:
        timeout = int(backend_config.get("maxRuntimeSeconds") or 300)
        try:
            completed = subprocess.run(
                [executable, *command[1:]],
                cwd=str(Path(str(script)).parent),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            result = _submission_result(
                calculation_id,
                "submitted" if completed.returncode == 0 else "failed",
                f"Return code {completed.returncode}",
                stdout=completed.stdout[-4000:],
                stderr=completed.stderr[-4000:],
            )
        except subprocess.TimeoutExpired as exc:
            result = _submission_result(calculation_id, "failed", f"Timed out after {timeout}s", stdout=exc.stdout, stderr=exc.stderr)
    submission_path = Path(str(script)).parent / "submission-manifest.json"
    result["submissionManifestPath"] = str(submission_path)
    submission_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _backend_submit_command(backend: str, script: str, backend_config: dict[str, Any]) -> list[str]:
    if backend in {"quantum-espresso", "vasp"}:
        return [str(backend_config.get("shellCommand") or "bash"), str(Path(script).name)]
    if backend == "atomate2":
        return [str(backend_config.get("pythonCommand") or "python"), str(Path(script).name)]
    if backend == "aiida":
        return [str(backend_config.get("pythonCommand") or "python"), str(Path(script).name)]
    return ["bash", str(Path(script).name)]


def _submission_result(calculation_id: str, status: str, message: str, *, stdout: Any = "", stderr: Any = "") -> dict[str, Any]:
    return {
        "calculationId": calculation_id,
        "status": status,
        "message": message,
        "stdout": stdout.decode("utf-8", errors="replace") if isinstance(stdout, bytes) else stdout,
        "stderr": stderr.decode("utf-8", errors="replace") if isinstance(stderr, bytes) else stderr,
        "generatedAt": int(time.time()),
    }


def _quantum_espresso_scf_input(material: dict[str, Any], structure_data: Any, backend_config: dict[str, Any]) -> str:
    prefix = _safe_file_stem(str(material.get("materialId") or material.get("formula") or "qe"))
    lines = [
        "&CONTROL",
        "  calculation = 'scf',",
        f"  prefix = '{prefix}',",
        "  outdir = './tmp',",
        f"  pseudo_dir = '{backend_config.get('pseudoDir') or './pseudo'}',",
        "/",
        "&SYSTEM",
        "  ibrav = 0,",
        f"  ecutwfc = {float(backend_config.get('ecutwfc') or 60.0):.1f},",
        f"  ecutrho = {float(backend_config.get('ecutrho') or 480.0):.1f},",
    ]
    atoms = _structure_atoms_for_input(structure_data, material)
    elements = _unique_ordered([atom["element"] for atom in atoms]) or _composition_elements(material)
    lines.extend([f"  nat = {max(len(atoms), 1)},", f"  ntyp = {max(len(elements), 1)},", "/"])
    lines.extend(["&ELECTRONS", "  conv_thr = 1.0d-8,", "/"])
    lines.append("ATOMIC_SPECIES")
    for element in elements:
        lines.append(f"  {element} {_atomic_mass(element):.6f} {element}.UPF")
    lines.append("CELL_PARAMETERS angstrom")
    for row in _structure_lattice_for_input(structure_data):
        lines.append("  " + " ".join(f"{value:.10f}" for value in row))
    lines.append("ATOMIC_POSITIONS crystal")
    if atoms:
        for atom in atoms:
            lines.append(f"  {atom['element']} " + " ".join(f"{value:.10f}" for value in atom["coords"]))
    else:
        lines.append(f"  {elements[0] if elements else 'X'} 0.0000000000 0.0000000000 0.0000000000")
    lines.extend(["K_POINTS automatic", str(backend_config.get("kpoints") or "4 4 4 0 0 0"), ""])
    return "\n".join(lines)


def _quantum_espresso_ph_input(material: dict[str, Any], backend_config: dict[str, Any], *, epsil: bool = True) -> str:
    prefix = _safe_file_stem(str(material.get("materialId") or material.get("formula") or "qe"))
    return "\n".join([
        "&INPUTPH",
        "  tr2_ph = 1.0d-14,",
        f"  prefix = '{prefix}',",
        "  outdir = './tmp',",
        f"  epsil = {'.true.' if epsil else '.false.'},",
        f"  fildyn = '{prefix}.dynG',",
        "/",
        "0.0 0.0 0.0",
        "",
    ])


def _quantum_espresso_pp_input(material: dict[str, Any], backend_config: dict[str, Any]) -> str:
    prefix = _safe_file_stem(str(material.get("materialId") or material.get("formula") or "qe"))
    return "\n".join([
        "&INPUTPP",
        f"  prefix = '{prefix}',",
        "  outdir = './tmp',",
        "  plot_num = 11,",
        "/",
        "&PLOT",
        "  iflag = 3,",
        f"  fileout = '{prefix}.potential.cube',",
        "/",
        "",
    ])


def _quantum_espresso_run_script(step: dict[str, Any], backend_config: dict[str, Any]) -> str:
    pw = str(backend_config.get("pwCommand") or "pw.x")
    ph = str(backend_config.get("phCommand") or "ph.x")
    pp = str(backend_config.get("ppCommand") or "pp.x")
    calc_type = str(step.get("id") or "")
    commands = ["set -euo pipefail", f"{pw} -in pw.scf.in > pw.scf.out"]
    if calc_type == "dfpt-dielectric-tensor":
        commands.append(f"{ph} -in ph.dielectric.in > ph.dielectric.out")
    elif calc_type == "phonon-stability":
        commands.append(f"{ph} -in ph.gamma.in > ph.gamma.out")
    elif calc_type == "band-alignment":
        commands.append(f"{pp} -in pp.potential.in > pp.potential.out")
    return "#!/usr/bin/env bash\n" + "\n".join(commands) + "\n"


def _vasp_incar(step: dict[str, Any], backend_config: dict[str, Any]) -> str:
    calc_type = str(step.get("id") or "")
    lines = [
        "SYSTEM = OpenClaw Materials Lab backend adapter",
        "ENCUT = " + str(backend_config.get("encut") or 520),
        "EDIFF = 1E-6",
        "PREC = Accurate",
        "ISMEAR = 0",
        "SIGMA = 0.05",
    ]
    if calc_type == "dfpt-dielectric-tensor":
        lines.extend(["LEPSILON = .TRUE.", "IBRION = 8", "NSW = 1"])
    elif calc_type == "phonon-stability":
        lines.extend(["IBRION = 5", "NFREE = 2", "NSW = 1"])
    elif calc_type == "band-alignment":
        lines.extend(["LVTOT = .TRUE.", "LVHAR = .TRUE.", "NSW = 0"])
    else:
        lines.extend(["NSW = 0"])
    return "\n".join(lines) + "\n"


def _vasp_kpoints(backend_config: dict[str, Any]) -> str:
    mesh = str(backend_config.get("kpoints") or "4 4 4")
    return "\n".join(["Automatic mesh", "0", "Gamma", mesh, "0 0 0", ""])


def _vasp_potcar_spec(material: dict[str, Any]) -> str:
    elements = _composition_elements(material)
    return "\n".join([f"{element}  # provide POTCAR for {element}" for element in elements] + [""])


def _vasp_run_script(backend_config: dict[str, Any]) -> str:
    command = str(backend_config.get("vaspCommand") or "vasp_std")
    return "#!/usr/bin/env bash\nset -euo pipefail\n" + f"{command} > vasp.out\n"


def _atomate2_flow_script(step: dict[str, Any], material: dict[str, Any], structure_paths: dict[str, str], backend_config: dict[str, Any]) -> str:
    structure_ref = structure_paths.get("structureCif") or structure_paths.get("poscar") or "REPLACE_WITH_STRUCTURE"
    return f'''#!/usr/bin/env python
"""Generated by OpenClaw Materials Lab.

This script is a backend adapter scaffold. Review resources and code settings before running.
"""
from pathlib import Path

from pymatgen.core import Structure

STRUCTURE_PATH = Path({structure_ref!r})
MATERIAL_ID = {material.get("materialId")!r}
CALCULATION_TYPE = {step.get("id")!r}


def main():
    structure = Structure.from_file(STRUCTURE_PATH)
    print(f"Prepared atomate2/jobflow scaffold for {{MATERIAL_ID}}: {{CALCULATION_TYPE}}")
    print(structure.composition)
    print("TODO: connect atomate2 makers, jobflow manager, and store output parser.")


if __name__ == "__main__":
    main()
'''


def _aiida_submit_script(step: dict[str, Any], material: dict[str, Any], structure_paths: dict[str, str], backend_config: dict[str, Any]) -> str:
    structure_ref = structure_paths.get("structureCif") or structure_paths.get("poscar") or "REPLACE_WITH_STRUCTURE"
    return f'''#!/usr/bin/env python
"""Generated by OpenClaw Materials Lab.

This script is an AiiDA submission scaffold. Review profile/code/pseudopotential settings before running.
"""
from pathlib import Path

STRUCTURE_PATH = Path({structure_ref!r})
MATERIAL_ID = {material.get("materialId")!r}
CALCULATION_TYPE = {step.get("id")!r}
AIIDA_PROFILE = {backend_config.get("profile")!r}
AIIDA_CODE = {backend_config.get("code")!r}


def main():
    print(f"Prepared AiiDA scaffold for {{MATERIAL_ID}}: {{CALCULATION_TYPE}}")
    print(f"profile={{AIIDA_PROFILE}} code={{AIIDA_CODE}} structure={{STRUCTURE_PATH}}")
    print("TODO: load aiida profile, create StructureData, configure builder, submit.")


if __name__ == "__main__":
    main()
'''


def _pseudopotential_manifest(material: dict[str, Any]) -> str:
    elements = _composition_elements(material)
    return "\n".join([f"{element}.UPF" for element in elements] + [""])


def _structure_atoms_for_input(structure_data: Any, material: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(structure_data, dict):
        try:
            if Structure is not None:
                structure = Structure.from_dict(structure_data)
                return [
                    {"element": str(site.specie.symbol), "coords": [float(value) for value in site.frac_coords]}
                    for site in structure
                ]
        except Exception:
            pass
        sites = structure_data.get("sites") or []
        atoms = []
        for site in sites:
            if not isinstance(site, dict):
                continue
            species = site.get("species") or site.get("label") or site.get("element")
            if isinstance(species, list) and species:
                symbol = str((species[0] or {}).get("element") or (species[0] or {}).get("label") or "X")
            else:
                symbol = str(species or "X")
            coords = site.get("abc") or site.get("coords") or [0.0, 0.0, 0.0]
            atoms.append({"element": symbol, "coords": [float(value) for value in coords[:3]]})
        return atoms
    elements = _composition_elements(material)
    return [{"element": elements[0], "coords": [0.0, 0.0, 0.0]}] if elements else []


def _structure_lattice_for_input(structure_data: Any) -> list[list[float]]:
    if isinstance(structure_data, dict):
        try:
            if Structure is not None:
                return [[float(value) for value in row] for row in Structure.from_dict(structure_data).lattice.matrix]
        except Exception:
            pass
        lattice = structure_data.get("lattice")
        if isinstance(lattice, dict) and isinstance(lattice.get("matrix"), list):
            return [[float(value) for value in row[:3]] for row in lattice["matrix"][:3]]
        if isinstance(lattice, list):
            return [[float(value) for value in row[:3]] for row in lattice[:3]]
    return [[8.0, 0.0, 0.0], [0.0, 8.0, 0.0], [0.0, 0.0, 8.0]]


def _composition_elements(material: dict[str, Any]) -> list[str]:
    elements = [str(item) for item in material.get("elements") or [] if item]
    if elements:
        return _unique_ordered(elements)
    descriptors = _composition_descriptors(material)
    elements = [str(item) for item in descriptors.get("elements") or [] if item]
    return _unique_ordered(elements) or ["X"]


def _unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _atomic_mass(symbol: str) -> float:
    if Element is not None:
        try:
            return float(Element(symbol).atomic_mass)
        except Exception:
            pass
    return ATOMIC_MASS_FALLBACK.get(symbol, 1.0)


def _external_execution_markdown(manifest: dict[str, Any]) -> str:
    backend_label = {
        "quantum-espresso": "Quantum ESPRESSO",
        "vasp": "VASP",
        "atomate2": "atomate2/jobflow",
        "aiida": "AiiDA",
    }.get(str(manifest.get("backend")), str(manifest.get("backend")))
    lines = [
        f"# Research Backend Preparation: {backend_label}",
        "",
        "## Summary",
        "",
        f"- Backend: `{manifest.get('backend')}`",
        f"- Execution mode: `{manifest.get('executionMode')}`",
        f"- Allow blocked steps: `{manifest.get('allowBlockedSteps')}`",
        f"- Prepared calculations: {manifest.get('preparedCalculations')}",
        f"- Submitted calculations: {manifest.get('submittedCalculations')}",
        f"- Skipped calculations: {manifest.get('skippedCalculations')}",
        "- Parsed property updates: `0`",
        "",
        "## Prepared Steps",
        "",
        "| Calculation | Material | Type | Inputs |",
        "| --- | --- | --- | ---: |",
    ]
    for step in manifest.get("prepared") or []:
        lines.append(
            f"| {step.get('calculationId')} | {step.get('materialId')} | {step.get('calculationType')} | {len(step.get('inputPaths') or [])} |"
        )
    lines.extend([
        "",
        "## Notes",
        "",
        "- This adapter prepares reproducible backend inputs and optional submission scripts.",
        "- It does not mark candidates as property-backed until completed outputs are parsed into propertyUpdates.",
        "- Review pseudopotentials, k-points, cutoffs, scheduler resources, and code licenses before submission.",
        "",
        "## Warnings",
        "",
        *([f"- {warning}" for warning in manifest.get("warnings") or []] or ["- No warnings."]),
        "",
    ])
    return "\n".join(lines)


def _run_dev_smoke_step(step: dict[str, Any], candidate: dict[str, Any], plan: dict[str, Any], *, api_key: str | None) -> dict[str, Any]:
    material_id = str(step.get("materialId") or candidate.get("materialId") or "")
    formula = str(step.get("formula") or candidate.get("formula") or "")
    calculation_type = str(step.get("id") or "")
    return {
        "calculationId": step.get("calculationId"),
        "materialId": material_id,
        "formula": formula,
        "backend": "dev-smoke",
        "status": "completed-dev-smoke",
        "calculationType": calculation_type,
        "label": step.get("label"),
        "method": step.get("method"),
        "costClass": step.get("costClass"),
        "estimatedWallTimeHours": step.get("estimatedWallTimeHours"),
        "diagnostics": {
            "hasMaterialId": bool(material_id),
            "hasFormula": bool(formula),
            "preset": plan.get("preset"),
            "writesPropertiesSuppressed": list(step.get("writesProperties") or []),
        },
        "provenance": {
            "backend": "dev-smoke",
            "confidence": "none",
            "generatedAt": int(time.time()),
            "basis": "execution plumbing smoke test only",
            "notAReplacementFor": "Materials Project data, DFT, DFPT, MD, workflow execution, parsed outputs, literature, or experiment",
        },
    }


def _dev_smoke_execution_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        f"# Research Plan Execution: {manifest['runId']}",
        "",
        "## Backend",
        "",
        "- Backend: `dev-smoke`",
        "- Confidence: `none`",
        "- This backend validates execution plumbing only and does not create research property evidence.",
        "",
        "## Summary",
        "",
        f"- Completed calculations: {manifest['completedCalculations']}",
        f"- Skipped calculations: {manifest['skippedCalculations']}",
        f"- Allow blocked dev-smoke execution: `{manifest['allowBlockedDevSmoke']}`",
        "",
        "## Completed Diagnostics",
        "",
        "| Calculation | Material | Formula | Suppressed Properties |",
        "| --- | --- | --- | --- |",
    ]
    for item in manifest["completed"]:
        diagnostics = item.get("diagnostics") or {}
        suppressed = ", ".join(diagnostics.get("writesPropertiesSuppressed") or []) or "-"
        lines.append(f"| {item.get('calculationId')} | {item.get('materialId')} | {item.get('formula')} | {suppressed} |")
    lines.extend([
        "",
        "## Warnings",
        "",
        *[f"- {warning}" for warning in manifest.get("warnings") or []],
        "",
    ])
    return "\n".join(lines)


def _safe_file_stem(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-") or "artifact"


def _numeric(value: Any, default: float) -> float:
    try:
        if value is None or isinstance(value, bool):
            return default
        return float(value)
    except Exception:
        return default


def _default_research_objective(criteria: dict[str, Any]) -> str:
    preset = str(criteria.get("preset") or "generic")
    return {
        "solid-electrolyte": "Promote proxy solid-electrolyte candidates into a property-backed shortlist.",
        "high-k-dielectric": "Promote proxy high-k dielectric candidates into a property-backed gate-dielectric shortlist.",
        "photovoltaic-absorber": "Promote proxy photovoltaic absorber candidates into a property-backed device-material shortlist.",
        "thermoelectric": "Promote proxy thermoelectric candidates into a property-backed transport shortlist.",
    }.get(preset, "Promote proxy candidates into a property-backed materials shortlist.")


def _normalize_protocol_inputs(payload: dict[str, Any], *, objective: str, criteria: dict[str, Any]) -> dict[str, Any]:
    candidate_generation = payload.get("candidateGeneration")
    if not isinstance(candidate_generation, dict):
        candidate_generation = {}
    explicit_requirements = payload.get("evidenceRequirements")
    if not isinstance(explicit_requirements, list):
        explicit_requirements = []
    return {
        "researchGoal": ensure_string(payload.get("researchGoal"), field="researchGoal", required=False) or objective,
        "targetApplication": ensure_string(payload.get("targetApplication"), field="targetApplication", required=False),
        "hypothesis": ensure_string(payload.get("hypothesis"), field="hypothesis", required=False),
        "constraints": _string_list(payload.get("constraints")),
        "literatureQueries": _string_list(payload.get("literatureQueries")),
        "databaseQueries": _string_list(payload.get("databaseQueries")),
        "validationMethods": _string_list(payload.get("validationMethods")),
        "candidateGeneration": candidate_generation,
        "evidenceRequirements": [item for item in explicit_requirements if isinstance(item, dict)],
        "autonomyMode": str(payload.get("autonomyMode") or "bounded").strip().lower(),
        "legacyPreset": criteria.get("preset"),
    }


def _build_research_loop_plan(
    *,
    candidates: list[dict[str, Any]],
    criteria: dict[str, Any],
    budget: dict[str, Any],
    objective: str,
    mode: str,
    approval_policy: str,
    protocol_inputs: dict[str, Any],
) -> dict[str, Any]:
    protocol = _compile_dynamic_research_protocol(
        objective=objective,
        candidates=candidates,
        criteria=criteria,
        protocol_inputs=protocol_inputs,
    )
    selected = _select_research_candidates(candidates, budget)
    plan_id = f"{protocol['protocolId']}-{int(time.time() * 1000)}"
    queue = _dynamic_calculation_queue(selected, protocol, budget)
    approval_gates = _approval_gates(queue, budget, approval_policy, protocol)
    warnings = _research_plan_warnings(selected, queue, budget, approval_policy, protocol)
    return {
        "planId": plan_id,
        "protocolVersion": "dynamic-research-protocol-v1",
        "protocolKind": "research-protocol-compiler",
        "mode": mode if mode in {"property-backed", "closed-loop"} else "property-backed",
        "preset": "dynamic",
        "legacyPreset": protocol_inputs.get("legacyPreset"),
        "topic": protocol["topic"],
        "objective": objective,
        "researchGoal": protocol["researchGoal"],
        "targetApplication": protocol.get("targetApplication"),
        "hypothesis": protocol.get("hypothesis"),
        "constraints": protocol.get("constraints", []),
        "executionStatus": "planned-not-started",
        "autonomyBoundary": {
            "requestedAutonomyMode": protocol["autonomyMode"],
            "approvalPolicy": approval_policy if approval_policy in {"plan-only", "approval-required"} else "approval-required",
            "canExecuteWithoutApproval": False,
            "allowedActionsBeforeApproval": ["write-plan-artifacts", "validate-input-artifacts"],
            "blockedActionsBeforeApproval": [
                "run-dft",
                "submit-hpc-job",
                "call-paid-compute-service",
                "overwrite-candidate-ranking",
                "make-research-grade-claim-without-evidence-ledger",
            ],
        },
        "budget": budget,
        "candidateGenerationPlan": protocol["candidateGenerationPlan"],
        "literatureReviewPlan": protocol["literatureReviewPlan"],
        "literatureEvidencePipeline": protocol["literatureEvidencePipeline"],
        "databaseSearchPlan": protocol["databaseSearchPlan"],
        "evidenceSchema": protocol["evidenceSchema"],
        "methodRegistry": protocol["methodRegistry"],
        "capabilityPlan": protocol["capabilityPlan"],
        "claimPolicy": protocol["claimPolicy"],
        "validationMatrix": protocol["validationMatrix"],
        "selectedCandidates": selected,
        "calculationQueue": queue,
        "approvalGates": approval_gates,
        "rerankingPolicy": _dynamic_reranking_policy(protocol),
        "loopPolicy": {
            "maxIterations": budget["maxLoopIterations"],
            "afterEachIteration": [
                "parse calculation artifacts into candidate property fields",
                "rerun materials_compare_candidates with evidenceWeight enabled",
                "compare domainCoverage against previous iteration",
                "stop, continue, or request human review based on stopCriteria",
            ],
        },
        "stopCriteria": _dynamic_stop_criteria(protocol),
        "propertySchema": _dynamic_property_schema(protocol),
        "warnings": warnings,
    }


def _criteria_for_protocol_topic(raw_criteria: dict[str, Any], criteria: dict[str, Any], topic: dict[str, Any]) -> dict[str, Any]:
    if raw_criteria.get("preset"):
        return criteria
    topic_to_preset = {
        "solid-electrolyte": "solid-electrolyte",
        "dielectric": "high-k-dielectric",
        "photovoltaic-absorber": "photovoltaic-absorber",
        "thermoelectric": "thermoelectric",
    }
    inferred = topic_to_preset.get(str(topic.get("id") or ""))
    if not inferred:
        return criteria
    return _prepare_compare_criteria({**raw_criteria, "preset": inferred})


def _autonomous_candidate_discovery(
    *,
    candidates: list[dict[str, Any]],
    protocol: dict[str, Any],
    criteria: dict[str, Any],
    budget: dict[str, Any],
    artifact_dir: Path,
    api_key: str | None,
    protocol_inputs: dict[str, Any],
) -> dict[str, Any]:
    candidate_generation = ensure_dict(protocol_inputs.get("candidateGeneration") or {}, field="candidateGeneration")
    enabled = _auto_discovery_enabled(candidates, candidate_generation)
    if not enabled:
        return {
            "enabled": False,
            "status": "skipped-existing-candidates" if candidates else "disabled",
            "reason": "Candidate discovery was disabled or explicit candidates were provided.",
            "artifactPaths": [],
            "warnings": [],
        }

    discovery_dir = artifact_dir / "autonomous-discovery"
    discovery_dir.mkdir(parents=True, exist_ok=True)
    allow_development_fixtures = bool(
        candidate_generation.get("allowDevelopmentFixtures")
        or candidate_generation.get("allowOffline")
        or candidate_generation.get("allowOfflineCandidateDiscovery")
    )
    search_payloads = _compile_discovery_search_payloads(
        protocol=protocol,
        criteria=criteria,
        budget=budget,
        protocol_inputs=protocol_inputs,
    )
    query_records: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    rejected: list[dict[str, Any]] = []
    warnings: list[str] = []

    if not api_key and not allow_development_fixtures:
        warnings.append("Autonomous database discovery was attempted without a Materials Project API key; no development fixture fallback was used.")

    for index, payload in enumerate(search_payloads, start=1):
        query_id = f"dbq-{index:03d}"
        query_payload = dict(payload)
        query_payload["allowOffline"] = allow_development_fixtures
        record: dict[str, Any] = {
            "queryId": query_id,
            "status": "planned",
            "tool": "materials_search_mp",
            "payload": query_payload,
            "source": "Materials Project" if api_key else "Materials Project unavailable",
            "usedDevelopmentFixtureData": False,
            "candidateIds": [],
            "rejected": [],
        }
        if not api_key and not allow_development_fixtures:
            record["status"] = "skipped-no-api-key"
            record["message"] = "Configure mpApiKey or set candidateGeneration.allowDevelopmentFixtures=true for smoke tests."
            query_records.append(record)
            continue
        try:
            raw_candidates, used_offline = search_materials(query_payload, api_key=api_key)
            summaries = [_candidate_summary(item) for item in raw_candidates]
            accepted, rejected_for_query = _filter_discovered_candidates(
                summaries,
                protocol=protocol,
                criteria=criteria,
                protocol_inputs=protocol_inputs,
            )
            for candidate in accepted:
                material_id = str(candidate.get("materialId") or "")
                if not material_id:
                    continue
                existing = by_id.setdefault(material_id, dict(candidate))
                query_ids = set(existing.get("discoveryQueryIds") or [])
                query_ids.add(query_id)
                existing["discoveryQueryIds"] = sorted(query_ids)
                existing["discoverySource"] = "dev-fixture" if used_offline else "materials-project-live"
            rejected.extend(rejected_for_query)
            record.update({
                "status": "ok",
                "source": "development fixture data" if used_offline else "Materials Project",
                "usedDevelopmentFixtureData": used_offline,
                "candidateCount": len(summaries),
                "acceptedCount": len(accepted),
                "candidateIds": [candidate.get("materialId") for candidate in accepted],
                "rejected": rejected_for_query,
            })
        except WorkerError as exc:
            record.update({
                "status": "failed",
                "error": exc.code,
                "message": exc.message,
                "hint": exc.hint,
            })
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            record.update({
                "status": "failed",
                "error": exc.__class__.__name__,
                "message": str(exc),
            })
        query_records.append(record)

    discovered = list(by_id.values())
    rankable, excluded_by_ranking = _filter_candidates_for_ranking(discovered, criteria)
    if excluded_by_ranking:
        rejected.extend(excluded_by_ranking)
    ranked = _rank_candidates(rankable, criteria) if rankable else []
    ranked = ranked[: int(budget["maxCandidates"])]
    for candidate in ranked:
        candidate["claimLevel"] = "candidate-hypothesis"
        candidate["researchGradeClaimAllowed"] = False

    evidence_rows = _discovery_evidence_ledger_rows(
        candidates=ranked,
        query_records=query_records,
        protocol=protocol,
        criteria=criteria,
    )
    artifact_paths = _write_discovery_artifacts(
        discovery_dir=discovery_dir,
        query_records=query_records,
        ranked=ranked,
        evidence_rows=evidence_rows,
        rejected=rejected,
        protocol=protocol,
    )
    status = "completed" if ranked else "completed-no-candidates"
    if not ranked:
        warnings.append("Autonomous candidate discovery produced no rankable candidates; protocol remains candidate-generation-first.")
    return {
        "enabled": True,
        "status": status,
        "sourceMode": _discovery_source_mode(query_records, api_key=api_key),
        "queryCount": len(query_records),
        "successfulQueryCount": sum(1 for record in query_records if record.get("status") == "ok"),
        "candidateCount": len(discovered),
        "rankedCandidateCount": len(ranked),
        "rankedCandidates": ranked,
        "rejectedCandidates": rejected,
        "queryRecords": query_records,
        "artifactPaths": artifact_paths,
        "warnings": warnings,
        "candidatePoolPath": str(discovery_dir / "candidate-pool.jsonl"),
        "evidenceLedgerPath": str(discovery_dir / "evidence-ledger.jsonl"),
        "queryLogPath": str(discovery_dir / "query-log.json"),
        "summaryPath": str(discovery_dir / "summary.json"),
    }


def _discovery_source_mode(query_records: list[dict[str, Any]], *, api_key: str | None) -> str:
    if any(record.get("usedDevelopmentFixtureData") for record in query_records):
        return "development-fixture-smoke"
    if any(record.get("status") == "ok" for record in query_records):
        return "materials-project-live"
    return "materials-project-unavailable" if not api_key else "materials-project-no-successful-query"


def _auto_discovery_enabled(candidates: list[dict[str, Any]], candidate_generation: dict[str, Any]) -> bool:
    if candidates:
        return bool(candidate_generation.get("discoverAdditionalCandidates", False))
    if "autoDiscover" in candidate_generation:
        return bool(candidate_generation.get("autoDiscover"))
    return True


def _compile_discovery_search_payloads(
    *,
    protocol: dict[str, Any],
    criteria: dict[str, Any],
    budget: dict[str, Any],
    protocol_inputs: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_generation = ensure_dict(protocol_inputs.get("candidateGeneration") or {}, field="candidateGeneration")
    max_queries = max(1, min(int(candidate_generation.get("maxQueries") or 8), 30))
    per_query_limit = max(1, min(int(candidate_generation.get("perQueryLimit") or max(6, budget["maxCandidates"] * 4)), 100))
    payloads: list[dict[str, Any]] = []
    for item in candidate_generation.get("searchPayloads") or []:
        if isinstance(item, dict):
            payloads.append(_sanitize_search_payload(item, per_query_limit))
    for formula in _string_list(candidate_generation.get("formulas")):
        payloads.append(_search_payload({"formula": formula}, criteria, per_query_limit))
    for seed in _string_list(candidate_generation.get("seedMaterials")):
        if _looks_like_formula(seed):
            payloads.append(_search_payload({"formula": seed}, criteria, per_query_limit))
    payloads.extend(_topic_seed_search_payloads(protocol, criteria, per_query_limit))
    elements_include = _string_list(candidate_generation.get("elementsInclude"))
    if elements_include:
        payloads.append(_search_payload({"elementsAll": elements_include[:8]}, criteria, per_query_limit))
    if not payloads:
        payloads.append(_search_payload({}, criteria, per_query_limit))
    return _dedupe_search_payloads(payloads)[:max_queries]


def _topic_seed_search_payloads(protocol: dict[str, Any], criteria: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    topic_id = str((protocol.get("topic") or {}).get("id") or "")
    if topic_id == "photovoltaic-absorber":
        seeds = [
            {"formula": "Si"},
            {"elementsAll": ["Cu", "In", "Se"]},
            {"elementsAll": ["Cu", "Ga", "Se"]},
            {"elementsAll": ["Cu", "Zn", "Sn", "S"]},
            {"elementsAll": ["Ag", "Bi", "S"]},
        ]
    elif topic_id == "dielectric":
        seeds = [
            {"formula": "HfO2"},
            {"formula": "ZrO2"},
            {"formula": "Al2O3"},
            {"formula": "TiO2"},
            {"formula": "SrTiO3"},
            {"elementsAll": ["O"]},
        ]
    elif topic_id == "solid-electrolyte":
        seeds = [
            {"elementsAll": ["Li", "La", "Zr", "O"]},
            {"elementsAll": ["Li", "P", "S"]},
            {"elementsAll": ["Li", "Ge", "P", "S"]},
            {"elementsAll": ["Li", "Al", "Ti", "P", "O"]},
            {"elementsAll": ["Li", "Y", "Cl"]},
        ]
    elif topic_id == "thermoelectric":
        seeds = [
            {"elementsAll": ["Bi", "Te"]},
            {"elementsAll": ["Sb", "Te"]},
            {"elementsAll": ["Mg", "Si"]},
            {"elementsAll": ["Sn", "Se"]},
        ]
    elif topic_id == "superconductor":
        seeds = [
            {"elementsAll": ["Mg", "B"]},
            {"elementsAll": ["Nb", "N"]},
            {"elementsAll": ["Y", "Ba", "Cu", "O"]},
            {"elementsAll": ["Fe", "Se"]},
        ]
    elif topic_id == "alloy":
        seeds = [
            {"elementsAll": ["Fe", "Ni"]},
            {"elementsAll": ["Al", "Ti"]},
            {"elementsAll": ["Co", "Cr", "Fe", "Ni"]},
            {"elementsAll": ["Ni", "Ti"]},
        ]
    elif topic_id == "catalyst":
        seeds = [
            {"elementsAll": ["Fe", "O"]},
            {"elementsAll": ["Co", "O"]},
            {"elementsAll": ["Ni", "O"]},
            {"elementsAll": ["Mo", "S"]},
        ]
    else:
        seeds = [{}]
    return [_search_payload(seed, criteria, limit) for seed in seeds]


def _search_payload(seed: dict[str, Any], criteria: dict[str, Any], limit: int) -> dict[str, Any]:
    payload = dict(seed)
    payload.setdefault("maxEnergyAboveHullEv", 0.08)
    min_gap = criteria.get("minimumBandGapEv")
    if isinstance(min_gap, (int, float)) and float(min_gap) > 0:
        payload.setdefault("minBandGapEv", float(min_gap))
    target_gap = criteria.get("bandGapTargetEv")
    if isinstance(target_gap, (int, float)) and float(target_gap) > 0:
        payload.setdefault("maxBandGapEv", max(float(target_gap) * 1.7, float(min_gap or 0) + 0.5))
    payload["limit"] = limit
    return payload


def _sanitize_search_payload(payload: dict[str, Any], limit: int) -> dict[str, Any]:
    allowed = {
        "textQuery",
        "formula",
        "elementsAll",
        "elementsAny",
        "maxEnergyAboveHullEv",
        "minBandGapEv",
        "maxBandGapEv",
        "limit",
    }
    sanitized = {key: payload[key] for key in allowed if key in payload}
    sanitized["limit"] = int(sanitized.get("limit") or limit)
    return sanitized


def _dedupe_search_payloads(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for payload in payloads:
        key = json.dumps(payload, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        result.append(payload)
    return result


def _filter_discovered_candidates(
    candidates: list[dict[str, Any]],
    *,
    protocol: dict[str, Any],
    criteria: dict[str, Any],
    protocol_inputs: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_generation = ensure_dict(protocol_inputs.get("candidateGeneration") or {}, field="candidateGeneration")
    excluded_elements = set(_string_list(candidate_generation.get("elementsExclude")))
    excluded_elements.update(_constraint_excluded_elements(protocol))
    if criteria.get("excludeToxicElements"):
        excluded_elements.update(str(item) for item in criteria.get("excludedElements") or [])
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for candidate in candidates:
        elements = set(str(item) for item in candidate.get("elements") or [])
        reasons = []
        blocked = sorted(elements.intersection(excluded_elements))
        if blocked:
            reasons.append(f"excluded elements present: {', '.join(blocked)}")
        if reasons:
            rejected.append({
                "materialId": candidate.get("materialId"),
                "formula": candidate.get("formula"),
                "reasons": reasons,
            })
        else:
            accepted.append(candidate)
    return accepted, rejected


def _constraint_excluded_elements(protocol: dict[str, Any]) -> set[str]:
    text = " ".join([
        str(protocol.get("researchGoal") or ""),
        " ".join(protocol.get("constraints") or []),
    ]).lower()
    excluded: set[str] = set()
    if "lead-free" in text or "pb-free" in text:
        excluded.add("Pb")
    if "cadmium-free" in text or "cd-free" in text:
        excluded.add("Cd")
    if "mercury-free" in text or "hg-free" in text:
        excluded.add("Hg")
    if "toxic" in text or "toxicity" in text:
        excluded.update({"Hg", "Tl", "Th", "U"})
    return excluded


def _discovery_evidence_ledger_rows(
    *,
    candidates: list[dict[str, Any]],
    query_records: list[dict[str, Any]],
    protocol: dict[str, Any],
    criteria: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    generated_at = int(time.time())
    query_ids = {str(record.get("queryId")): record for record in query_records}
    for candidate in candidates:
        material_id = str(candidate.get("materialId") or "candidate")
        linked_queries = [query_ids[item] for item in candidate.get("discoveryQueryIds") or [] if item in query_ids]
        rows.append(_ledger_row(
            material_id=material_id,
            formula=str(candidate.get("formula") or ""),
            evidence_requirement_id="database-provenance",
            claim="Candidate came from an auditable database discovery query.",
            status="supports-candidate-hypothesis",
            source_type="database",
            source=candidate.get("source"),
            confidence="database-summary",
            generated_at=generated_at,
            property_values={
                "energyAboveHullEv": candidate.get("energyAboveHullEv"),
                "bandGapEv": candidate.get("bandGapEv"),
                "densityGcm3": candidate.get("densityGcm3"),
                "spacegroup": candidate.get("spacegroup"),
            },
            query_ids=[record.get("queryId") for record in linked_queries],
        ))
        if candidate.get("energyAboveHullEv") is not None:
            rows.append(_ledger_row(
                material_id=material_id,
                formula=str(candidate.get("formula") or ""),
                evidence_requirement_id="phase-stability",
                claim="Database phase-stability proxy is available; DFT decomposition evidence is still required for research-grade promotion.",
                status="proxy-only",
                source_type="database",
                source=candidate.get("source"),
                confidence="database-summary",
                generated_at=generated_at,
                property_values={"energyAboveHullEv": candidate.get("energyAboveHullEv")},
                query_ids=[record.get("queryId") for record in linked_queries],
            ))
        rows.append(_ledger_row(
            material_id=material_id,
            formula=str(candidate.get("formula") or ""),
            evidence_requirement_id="claim-policy",
            claim="Discovery output is limited to candidate-hypothesis/proxy-shortlist until evidenceSchema requirements are closed.",
            status="blocks-research-grade-claim",
            source_type="workflow",
            source="dynamic-research-protocol-v1",
            confidence="workflow-policy",
            generated_at=generated_at,
            property_values={
                "claimLevel": "candidate-hypothesis",
                "researchGradeClaimAllowed": False,
                "rankingPreset": criteria.get("preset"),
                "requiredEvidenceRequirementIds": (protocol.get("claimPolicy") or {}).get("requiredEvidenceRequirementIds"),
            },
            query_ids=[record.get("queryId") for record in linked_queries],
        ))
    return rows


def _ledger_row(
    *,
    material_id: str,
    formula: str,
    evidence_requirement_id: str,
    claim: str,
    status: str,
    source_type: str,
    source: Any,
    confidence: str,
    generated_at: int,
    property_values: dict[str, Any],
    query_ids: list[Any],
) -> dict[str, Any]:
    return {
        "ledgerVersion": "evidence-ledger-v1",
        "evidenceId": _safe_file_stem(f"{material_id}-{evidence_requirement_id}").lower(),
        "candidateId": material_id,
        "formula": formula,
        "evidenceRequirementId": evidence_requirement_id,
        "claim": claim,
        "status": status,
        "sourceType": source_type,
        "source": source,
        "confidence": confidence,
        "propertyValues": {key: value for key, value in property_values.items() if value is not None},
        "queryIds": [item for item in query_ids if item],
        "generatedAt": generated_at,
    }


def _write_discovery_artifacts(
    *,
    discovery_dir: Path,
    query_records: list[dict[str, Any]],
    ranked: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    protocol: dict[str, Any],
) -> list[str]:
    query_log_path = discovery_dir / "query-log.json"
    candidate_pool_path = discovery_dir / "candidate-pool.jsonl"
    evidence_ledger_path = discovery_dir / "evidence-ledger.jsonl"
    summary_path = discovery_dir / "summary.json"
    query_log_path.write_text(json.dumps(query_records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate_pool_path.write_text(
        "".join(json.dumps(_public_candidate_record(candidate), sort_keys=True) + "\n" for candidate in ranked),
        encoding="utf-8",
    )
    evidence_ledger_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in evidence_rows),
        encoding="utf-8",
    )
    summary = {
        "discoveryVersion": "autonomous-discovery-v1",
        "topic": protocol.get("topic"),
        "queryCount": len(query_records),
        "successfulQueryCount": sum(1 for record in query_records if record.get("status") == "ok"),
        "candidateCount": len(ranked),
        "candidateIds": [candidate.get("materialId") for candidate in ranked],
        "rejectedCount": len(rejected),
        "claimLevel": "candidate-hypothesis" if ranked else "no-candidate",
        "researchGradeClaimAllowed": False,
        "artifacts": {
            "queryLogPath": str(query_log_path),
            "candidatePoolPath": str(candidate_pool_path),
            "evidenceLedgerPath": str(evidence_ledger_path),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return [str(query_log_path), str(candidate_pool_path), str(evidence_ledger_path), str(summary_path)]


def _public_candidate_record(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in candidate.items()
        if not key.startswith("_")
    }


def _attach_autonomous_discovery(plan: dict[str, Any], discovery: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    summary = {
        "enabled": discovery.get("enabled", False),
        "status": discovery.get("status"),
        "sourceMode": discovery.get("sourceMode"),
        "queryCount": discovery.get("queryCount", 0),
        "successfulQueryCount": discovery.get("successfulQueryCount", 0),
        "candidateCount": discovery.get("candidateCount", len(candidates)),
        "rankedCandidateCount": discovery.get("rankedCandidateCount", len(candidates)),
        **_discovery_paths_for_result(discovery),
    }
    plan["autonomousDiscovery"] = summary
    plan["claimStatus"] = {
        "currentLevel": "candidate-hypothesis" if plan.get("selectedCandidates") else "no-candidate",
        "researchGradeClaimAllowed": False,
        "blockedBy": [
            "evidence-ledger-review",
            "parsed-property-evidence",
            "claim-policy-review",
        ],
        "reason": "The autonomous design engine can propose and rank candidates, but research-grade claims require closed evidenceSchema entries.",
    }
    candidate_generation = plan.get("candidateGenerationPlan") if isinstance(plan.get("candidateGenerationPlan"), dict) else {}
    candidate_generation["autoDiscovery"] = summary
    candidate_generation["initialCandidateCount"] = len(candidates)
    plan["candidateGenerationPlan"] = candidate_generation


def _discovery_paths_for_result(discovery: dict[str, Any]) -> dict[str, str]:
    return {
        key: str(discovery[key])
        for key in ["queryLogPath", "candidatePoolPath", "evidenceLedgerPath", "summaryPath"]
        if discovery.get(key)
    }


def _looks_like_formula(value: str) -> bool:
    return any(char.isdigit() for char in value) or any(char.isupper() for char in value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _compile_dynamic_research_protocol(
    *,
    objective: str,
    candidates: list[dict[str, Any]],
    criteria: dict[str, Any],
    protocol_inputs: dict[str, Any],
) -> dict[str, Any]:
    research_goal = str(protocol_inputs.get("researchGoal") or objective).strip()
    target_application = protocol_inputs.get("targetApplication")
    hypothesis = protocol_inputs.get("hypothesis")
    constraints = list(protocol_inputs.get("constraints") or [])
    text = " ".join([
        research_goal,
        str(target_application or ""),
        str(hypothesis or ""),
        " ".join(constraints),
        str((protocol_inputs.get("candidateGeneration") or {}).get("strategy") or ""),
    ]).lower()
    topic = _infer_protocol_topic(text, research_goal)
    evidence_schema = _compile_evidence_schema(
        text=text,
        topic=topic,
        explicit_requirements=list(protocol_inputs.get("evidenceRequirements") or []),
        validation_methods=list(protocol_inputs.get("validationMethods") or []),
    )
    candidate_generation = _candidate_generation_plan(
        research_goal=research_goal,
        target_application=target_application,
        constraints=constraints,
        candidates=candidates,
        protocol_inputs=protocol_inputs,
        evidence_schema=evidence_schema,
    )
    return {
        "protocolId": _safe_file_stem(f"{topic['id']}-research-protocol").lower(),
        "researchGoal": research_goal,
        "targetApplication": target_application,
        "hypothesis": hypothesis,
        "constraints": constraints,
        "autonomyMode": protocol_inputs.get("autonomyMode") if protocol_inputs.get("autonomyMode") in {"bounded", "high-autonomy-plan", "human-gated"} else "bounded",
        "topic": topic,
        "candidateGenerationPlan": candidate_generation,
        "literatureReviewPlan": _literature_review_plan(research_goal, topic, protocol_inputs, evidence_schema),
        "literatureEvidencePipeline": _literature_evidence_pipeline(research_goal, topic, protocol_inputs, evidence_schema),
        "databaseSearchPlan": _database_search_plan(research_goal, topic, protocol_inputs, evidence_schema),
        "evidenceSchema": evidence_schema,
        "methodRegistry": _domain_method_registry(topic, evidence_schema),
        "capabilityPlan": _capability_plan(evidence_schema),
        "claimPolicy": _claim_policy(evidence_schema),
        "validationMatrix": _validation_matrix(evidence_schema),
    }


def _infer_protocol_topic(text: str, research_goal: str) -> dict[str, Any]:
    topic_rules = [
        ("solid-electrolyte", "Solid electrolyte / ion conductor", ["solid electrolyte", "ionic conductor", "li-ion", "lithium ion", "sodium ion", "na-ion", "electrolyte"]),
        ("battery-electrode", "Battery electrode", ["cathode", "anode", "battery electrode", "intercalation", "conversion electrode"]),
        ("dielectric", "Dielectric / gate insulator", ["dielectric", "high-k", "gate oxide", "insulator", "breakdown"]),
        ("photovoltaic-absorber", "Photovoltaic absorber", ["photovoltaic", "solar", "absorber", "optoelectronic", "band edge"]),
        ("thermoelectric", "Thermoelectric material", ["thermoelectric", "seebeck", "power factor", "zt", "thermal conductivity"]),
        ("superconductor", "Superconductor", ["superconductor", "superconducting", "critical temperature", "tc ", "t_c", "meissner"]),
        ("alloy", "Alloy / structural chemistry", ["alloy", "high entropy", "hea", "solid solution", "phase diagram", "intermetallic"]),
        ("catalyst", "Catalyst / surface material", ["catalyst", "catalytic", "orr", "oer", "her", "co2 reduction", "adsorption"]),
        ("mechanical-material", "Mechanical / structural material", ["mechanical", "elastic", "modulus", "toughness", "hardness", "strength"]),
        ("thermal-material", "Thermal management material", ["thermal barrier", "heat spreader", "thermal conductivity", "thermal expansion"]),
        ("magnetic-material", "Magnetic / spintronic material", ["magnetic", "spin", "ferromagnetic", "antiferromagnetic", "magnetocaloric"]),
        ("corrosion-coating", "Corrosion or coating material", ["corrosion", "coating", "passivation", "oxidation resistance", "adhesion"]),
    ]
    matches = [
        {"id": id_, "label": label, "matchedKeywords": [keyword for keyword in keywords if keyword in text]}
        for id_, label, keywords in topic_rules
        if any(keyword in text for keyword in keywords)
    ]
    if matches:
        primary = matches[0]
        return {
            "id": primary["id"],
            "label": primary["label"],
            "inference": "keyword-derived",
            "matchedKeywords": primary["matchedKeywords"],
            "alternateTopics": matches[1:],
        }
    return {
        "id": _safe_file_stem(research_goal[:60] or "general-materials").lower() or "general-materials",
        "label": "General materials research",
        "inference": "goal-derived",
        "matchedKeywords": [],
        "alternateTopics": [],
    }


def _compile_evidence_schema(
    *,
    text: str,
    topic: dict[str, Any],
    explicit_requirements: list[dict[str, Any]],
    validation_methods: list[str],
) -> list[dict[str, Any]]:
    requirements = [
        _evidence_requirement("literature-benchmark", "Literature benchmark", ["literatureBaseline"], ["literature"], "Prior art, known positive/negative controls, and reported property ranges.", "At least two independent relevant references or an explicit no-literature-found note.", True),
        _evidence_requirement("database-provenance", "Database provenance", ["databaseSummary"], ["database"], "Traceable database source, query payloads, data timestamp, and structure provenance.", "Every candidate must have source, query, structure, and version metadata.", True),
        _evidence_requirement("phase-stability", "Phase stability", ["energyAboveHullEv", "decompositionProducts"], ["database", "dft"], "Thermodynamic stability or metastability relative to competing phases.", "Low eHull or a justified metastability window with decomposition products.", True),
        _evidence_requirement("structure-validity", "Structure and chemistry validity", ["structureQuality", "oxidationStates", "chargeBalance"], ["database", "workflow"], "Structure parseability, oxidation-state plausibility, charge balance, and duplicate/prototype grouping.", "Candidate must have a validated structure and no unresolved chemistry sanity failure.", True),
        _evidence_requirement("synthesis-safety", "Synthesis, toxicity, and handling risk", ["synthesisRoute", "toxicityFlags", "supplyRisk"], ["literature", "safety", "experiment"], "Known synthesis feasibility, hazardous elements, air/moisture risk, and supply constraints.", "Risk must be explicitly accepted or mitigated before research-grade claims.", True),
    ]
    for item in explicit_requirements:
        requirements.append(_normalize_evidence_requirement(item, len(requirements) + 1, default_methods=validation_methods))

    if not explicit_requirements:
        requirements.extend(_inferred_topic_requirements(text, topic, validation_methods))

    requirements.append(_evidence_requirement("reproducibility", "Reproducibility package", ["workflowManifest", "inputDecks", "parsedOutputs"], ["workflow"], "Machine-readable inputs, outputs, parser versions, and reranking trace.", "All promoted claims must link to artifact paths and parser provenance.", True))
    return _dedupe_requirements(requirements)


def _inferred_topic_requirements(text: str, topic: dict[str, Any], validation_methods: list[str]) -> list[dict[str, Any]]:
    topic_id = str(topic.get("id") or "general-materials")
    by_topic = {
        "solid-electrolyte": [
            ("ion-transport", "Ion transport", ["ionicConductivityScm", "migrationBarrierEv"], ["md", "dft", "experiment"], "Ionic conductivity, activation energy, and connected mobile-ion pathways.", "Conductivity/barrier evidence at relevant temperature or a clearly weaker proxy label."),
            ("electrochemical-window", "Electrochemical stability window", ["electrochemicalWindowV", "interfaceReactionEnergyEv"], ["dft", "database"], "Reductive/oxidative stability and electrode interface reaction risk.", "Grand-potential or comparable interface stability evidence is required."),
        ],
        "battery-electrode": [
            ("voltage-capacity", "Voltage and capacity", ["voltageV", "capacityMahG", "energyDensityWhKg"], ["database", "dft"], "Average voltage, capacity, and energy density under realistic cycling chemistry.", "Capacity/voltage must be computed or literature-backed for the relevant ion."),
            ("cycling-stability", "Cycling stability", ["volumeChangePct", "migrationBarrierEv", "phaseTransformationRisk"], ["dft", "md", "experiment"], "Diffusion, structural change, and phase transformation during cycling.", "Volume change and migration evidence must be bounded before promotion."),
        ],
        "dielectric": [
            ("dielectric-response", "Dielectric response", ["dielectricTotal", "dielectricElectronic"], ["dfpt", "experiment"], "Static/electronic dielectric tensor and anisotropy.", "DFPT or experimental dielectric evidence, not density/chemistry proxy alone."),
            ("leakage-interface", "Leakage and interface risk", ["bandOffsetElectronEv", "bandOffsetHoleEv", "interfaceReactionEnergyEv", "defectFormationEnergyEv"], ["dft", "dfpt"], "Band offsets, interface reactions, and defect/leakage risks.", "Leakage guards and interface stability must be explicitly checked."),
        ],
        "photovoltaic-absorber": [
            ("optical-absorption", "Optical absorption", ["absorptionCoefficientCm1", "directBandGapEv"], ["dft", "experiment"], "Direct/indirect gap and absorption strength.", "Absorption must be property-backed for target spectrum."),
            ("defect-transport", "Defect and transport risk", ["defectToleranceScore", "effectiveMassElectron", "effectiveMassHole"], ["dft"], "Carrier masses, defect tolerance, and recombination risk.", "Transport and defect evidence must be present before device claims."),
        ],
        "thermoelectric": [
            ("transport-coefficients", "Transport coefficients", ["seebeckUvK", "powerFactorUwCmK2", "carrierConcentrationCm3"], ["dft", "workflow", "experiment"], "Seebeck, conductivity/power factor, and carrier concentration dependence.", "Transport sweep required across relevant carrier concentration and temperature."),
            ("lattice-thermal", "Lattice thermal conductivity", ["latticeThermalConductivityWmK"], ["dfpt", "md", "experiment"], "Lattice thermal conductivity or phonon scattering evidence.", "Thermal conductivity evidence must be parsed or literature-backed."),
        ],
        "superconductor": [
            ("superconducting-transition", "Superconducting transition", ["criticalTemperatureK", "criticalFieldT", "meissnerEvidence"], ["literature", "dfpt", "experiment"], "Critical temperature, field, and independent superconducting signatures.", "Tc must be traceable and supported by either experiment or an accepted electron-phonon/DFPT workflow."),
            ("electron-phonon-phonon-stability", "Electron-phonon and phonon stability", ["electronPhononCoupling", "logAveragePhononFrequencyK", "phononStability"], ["dfpt", "workflow"], "Electron-phonon coupling, phonon spectrum, and dynamic stability.", "Imaginary modes and weak coupling must be explicitly recorded before promotion."),
        ],
        "alloy": [
            ("phase-diagram-stability", "Phase diagram and competing phases", ["phaseStability", "mixingEnthalpyEvAtom", "phaseFraction"], ["database", "dft", "experiment"], "Phase stability, miscibility, and competing intermetallic phases.", "Target composition must be tied to a phase diagram or computed convex hull."),
            ("mechanical-processing-window", "Mechanical and processing window", ["yieldStrengthMpa", "ductilityPct", "hardnessGpa", "processingTemperatureK"], ["literature", "experiment", "dft"], "Mechanical response and feasible processing conditions.", "Processing route and at least one mechanical evidence source are required."),
        ],
        "catalyst": [
            ("surface-activity", "Surface activity and selectivity", ["adsorptionEnergyEv", "overpotentialV", "selectivityScore"], ["dft", "experiment"], "Adsorption descriptors, overpotential, and selectivity for target reaction.", "Surface model and reaction conditions must be specified."),
            ("operando-stability", "Operando stability", ["surfaceStability", "dissolutionRisk"], ["dft", "experiment"], "Stability under reaction environment and electrolyte/temperature.", "Stability must be evaluated under target conditions."),
        ],
        "mechanical-material": [
            ("elastic-mechanical", "Mechanical response", ["elasticTensor", "bulkModulusGpa", "shearModulusGpa", "hardnessGpa"], ["dft", "experiment"], "Elastic tensor, modulus, hardness, and failure proxies.", "Mechanical claims require tensor or experimental evidence."),
        ],
        "thermal-material": [
            ("thermal-response", "Thermal response", ["thermalConductivityWmK", "thermalExpansion", "thermalStability"], ["dfpt", "md", "experiment"], "Thermal conductivity, expansion, and high-temperature stability.", "Temperature-dependent thermal evidence required."),
        ],
        "magnetic-material": [
            ("magnetic-ordering", "Magnetic ordering", ["magneticMoment", "orderingTemperatureK", "anisotropyEnergyEv"], ["dft", "experiment"], "Magnetic order, moment, anisotropy, and transition temperature.", "Magnetic state and temperature evidence required."),
        ],
        "corrosion-coating": [
            ("environmental-durability", "Environmental durability", ["corrosionPotentialV", "oxidationResistance", "adhesionEnergy"], ["dft", "experiment", "literature"], "Corrosion/passivation resistance, adhesion, and environment-specific durability.", "Target environment and failure mode must be explicit."),
        ],
    }
    requirements = [
        _evidence_requirement(*entry)
        for entry in by_topic.get(topic_id, [])
    ]
    if not requirements:
        requirements.append(
            _evidence_requirement(
                "target-functional-property",
                "Target functional property",
                ["domainSpecificProperty"],
                validation_methods or ["database", "literature", "dft"],
                "The property that makes a candidate useful for the stated research goal.",
                "Define a measurable property, accepted range, and evidence source before ranking.",
                True,
            )
        )
    if any(word in text for word in ["toxic", "lead-free", "bio", "implant", "water", "air", "moisture", "hazard", "radioactive"]):
        requirements.append(_evidence_requirement("environmental-health-safety", "Environmental health and safety", ["ehsRisk", "regulatoryFlags"], ["safety", "literature"], "Toxicity, environmental release, handling, and regulatory constraints.", "EHS risk must be reviewed before promotion or experimental recommendation.", True))
    return requirements


def _evidence_requirement(
    id_: str,
    label: str,
    property_keys: list[str],
    evidence_types: list[str],
    description: str,
    acceptance_criteria: str,
    required_for_claim: bool = True,
) -> dict[str, Any]:
    return {
        "id": id_,
        "label": label,
        "propertyKeys": property_keys,
        "evidenceTypes": evidence_types,
        "description": description,
        "acceptanceCriteria": acceptance_criteria,
        "requiredForClaim": required_for_claim,
        "confidenceRules": [
            "database/literature-only evidence cannot support research-grade discovery claims",
            "parsed calculation or experimental artifacts must be linked before property-backed promotion",
            "conflicting evidence must be recorded in the evidence ledger rather than silently discarded",
        ],
    }


def _normalize_evidence_requirement(item: dict[str, Any], index: int, *, default_methods: list[str]) -> dict[str, Any]:
    label = str(item.get("label") or item.get("id") or f"Evidence requirement {index}").strip()
    id_ = _safe_file_stem(str(item.get("id") or label)).lower() or f"evidence-{index}"
    property_keys = _string_list(item.get("propertyKeys")) or [id_.replace("-", "_")]
    evidence_types = _string_list(item.get("evidenceTypes")) or default_methods or ["database", "literature", "dft"]
    return _evidence_requirement(
        id_,
        label,
        property_keys,
        evidence_types,
        str(item.get("description") or f"User-defined evidence requirement for {label}."),
        str(item.get("acceptanceCriteria") or "User-defined acceptance criteria must be satisfied or explicitly marked unresolved."),
        bool(item.get("requiredForClaim", True)),
    )


def _dedupe_requirements(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for requirement in requirements:
        id_ = str(requirement.get("id") or "")
        if id_ in seen:
            continue
        seen.add(id_)
        result.append(requirement)
    return result


def _candidate_generation_plan(
    *,
    research_goal: str,
    target_application: Any,
    constraints: list[str],
    candidates: list[dict[str, Any]],
    protocol_inputs: dict[str, Any],
    evidence_schema: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_generation = protocol_inputs.get("candidateGeneration") or {}
    seed_materials = _string_list(candidate_generation.get("seedMaterials"))
    formulas = _string_list(candidate_generation.get("formulas"))
    elements_include = _string_list(candidate_generation.get("elementsInclude"))
    elements_exclude = _string_list(candidate_generation.get("elementsExclude"))
    inferred_queries = [
        f"{research_goal} candidate materials",
        f"{research_goal} computed screening",
        f"{research_goal} materials discovery",
    ]
    if target_application:
        inferred_queries.append(f"{target_application} materials candidates")
    return {
        "strategy": str(candidate_generation.get("strategy") or "Start broad, gather literature/database candidates, then narrow by evidence schema and diversity controls."),
        "seedMaterials": seed_materials,
        "formulas": formulas,
        "elementsInclude": elements_include,
        "elementsExclude": elements_exclude,
        "constraints": constraints,
        "initialCandidateCount": len(candidates),
        "databaseQueries": _string_list(candidate_generation.get("databaseQueries")) or list(protocol_inputs.get("databaseQueries") or []) or inferred_queries,
        "literatureQueries": _string_list(candidate_generation.get("literatureQueries")) or list(protocol_inputs.get("literatureQueries") or []) or [f"{query} review" for query in inferred_queries[:2]],
        "diversityControls": ["deduplicate by reduced formula", "deduplicate by prototype/space group when structures are available", "cap repeated families before final reranking"],
        "requiredEvidenceBeforeShortlist": [requirement["id"] for requirement in evidence_schema if requirement.get("requiredForClaim")],
    }


def _literature_review_plan(research_goal: str, topic: dict[str, Any], protocol_inputs: dict[str, Any], evidence_schema: list[dict[str, Any]]) -> dict[str, Any]:
    queries = list(protocol_inputs.get("literatureQueries") or [])
    if not queries:
        queries = [
            f"{research_goal} review",
            f"{research_goal} benchmark materials",
            f"{topic.get('label')} experimental validation",
        ]
    return {
        "queries": queries,
        "extract": ["reported property values", "known positive controls", "known failure modes", "synthesis conditions", "contradictory evidence"],
        "mapsToEvidence": [requirement["id"] for requirement in evidence_schema if "literature" in requirement.get("evidenceTypes", [])],
        "requiredOutput": "literature-evidence-ledger with citation, claim, property, candidate, and confidence fields",
    }


def _literature_evidence_pipeline(
    research_goal: str,
    topic: dict[str, Any],
    protocol_inputs: dict[str, Any],
    evidence_schema: list[dict[str, Any]],
) -> dict[str, Any]:
    queries = list(protocol_inputs.get("literatureQueries") or [])
    if not queries:
        queries = [
            f"{research_goal} benchmark",
            f"{topic.get('label')} synthesis stability failure modes",
            f"{topic.get('label')} contradictory evidence",
        ]
    return {
        "pipelineVersion": "literature-evidence-pipeline-v1",
        "queries": queries,
        "stages": [
            {
                "stage": "search",
                "output": "citation-search-records.jsonl",
                "requiredFields": ["query", "title", "authors", "year", "doiOrUrl", "abstract", "source"],
            },
            {
                "stage": "pdf-and-text-extraction",
                "tool": "materials_ingest_evidence",
                "parsers": ["literature-json", "literature-text", "literature-markdown", "literature-pdf", "csv"],
                "output": "literature-evidence-ledger.jsonl",
            },
            {
                "stage": "table-extraction",
                "acceptedFormats": ["csv", "json", "jsonl", "markdown-table", "pdf-text-table"],
                "requiredColumns": ["candidateId-or-formula", "property", "value", "unit", "citation"],
            },
            {
                "stage": "citation-provenance",
                "checks": ["doi-or-url-present", "artifactPath-present", "candidate-mention-resolved", "negative-evidence-captured"],
            },
            {
                "stage": "conflict-routing",
                "tool": "materials_evaluate_research_claim",
                "output": "claim-review audit certificate with uncertainty/conflict summary",
            },
        ],
        "mapsToEvidence": [requirement["id"] for requirement in evidence_schema if "literature" in requirement.get("evidenceTypes", [])],
        "claimGuard": "Literature-only evidence can support context and benchmarks, but not a research-grade discovery claim without calculation/experiment/workflow evidence where required.",
    }


def _database_search_plan(research_goal: str, topic: dict[str, Any], protocol_inputs: dict[str, Any], evidence_schema: list[dict[str, Any]]) -> dict[str, Any]:
    queries = list(protocol_inputs.get("databaseQueries") or [])
    if not queries:
        queries = [
            f"Materials Project search for {research_goal}",
            f"structure and stability query for {topic.get('label')}",
        ]
    return {
        "queries": queries,
        "primaryTool": "materials_search_mp",
        "additionalSourcesToIntegrate": ["Materials Project task/property endpoints", "OQMD/AFLOW/NOMAD when available", "user-provided experimental tables"],
        "mapsToEvidence": [requirement["id"] for requirement in evidence_schema if "database" in requirement.get("evidenceTypes", [])],
        "requiredOutput": "candidate table with query payload, source database, version/timestamp, raw fields, and missing-field markers",
    }


def _domain_method_registry(topic: dict[str, Any], evidence_schema: list[dict[str, Any]]) -> dict[str, Any]:
    topic_id = str(topic.get("id") or "general-materials")
    common = {
        "phase-stability": ["database convex-hull provenance", "DFT relaxation and decomposition analysis"],
        "structure-validity": ["structure parser preflight", "oxidation-state/charge-balance sanity checks"],
        "literature-benchmark": ["citation search", "PDF/text/table extraction", "contradictory evidence capture"],
        "reproducibility": ["input/output bundle", "parser version manifest", "claim audit certificate"],
    }
    by_topic: dict[str, dict[str, list[str]]] = {
        "catalyst": {
            "surface-activity": ["slab generation", "adsorption energy workflow", "overpotential descriptor", "experimental activity table ingestion"],
            "operando-stability": ["Pourbaix/environment filter", "surface dissolution risk", "AIMD or experimental durability evidence"],
        },
        "battery-electrode": {
            "voltage-capacity": ["voltage profile workflow", "capacity calculation", "database/literature cycling benchmark"],
            "cycling-stability": ["volume-change workflow", "migration barrier", "AIMD finite-temperature check"],
        },
        "solid-electrolyte": {
            "ion-transport": ["NEB migration barrier", "AIMD diffusion parser", "conductivity Arrhenius fit"],
            "electrochemical-window": ["grand-potential phase stability", "interface reaction energy"],
        },
        "dielectric": {
            "dielectric-response": ["DFPT dielectric tensor", "phonon stability", "experimental permittivity table ingestion"],
            "leakage-interface": ["band alignment", "defect/leakage proxy", "interface reaction energy"],
        },
        "thermoelectric": {
            "transport-coefficients": ["Boltzmann transport sweep", "carrier concentration grid", "experiment table ingestion"],
            "lattice-thermal": ["phonon dispersion", "thermal conductivity workflow", "AIMD/Green-Kubo evidence"],
        },
        "superconductor": {
            "superconducting-transition": ["Tc literature/experiment extraction", "critical-field evidence", "Meissner/signature provenance"],
            "electron-phonon-phonon-stability": ["DFPT phonon dispersion", "electron-phonon coupling", "Eliashberg/McMillan estimate"],
        },
        "alloy": {
            "phase-diagram-stability": ["phase diagram ingestion", "mixing enthalpy", "convex hull by composition"],
            "mechanical-processing-window": ["elastic tensor", "hardness/strength table ingestion", "processing route provenance"],
        },
    }
    registry = {**common, **by_topic.get(topic_id, {})}
    required_ids = [str(item.get("id")) for item in evidence_schema if isinstance(item, dict)]
    return {
        "registryVersion": "domain-method-registry-v1",
        "topicId": topic_id,
        "requiredEvidenceRequirementIds": required_ids,
        "methodsByRequirement": {
            requirement_id: registry.get(requirement_id, ["define domain method", "attach parser-backed evidence", "review uncertainty/conflicts"])
            for requirement_id in required_ids
        },
        "parserCoverage": {
            "quantum-espresso": ["total energy", "band gap", "DOS/Fermi metadata", "dielectric", "surface energy", "adsorption", "phonon", "AIMD"],
            "vasp": ["TOTEN", "band gap", "DOS/Fermi metadata", "surface energy", "adsorption", "phonon", "AIMD"],
            "md": ["LAMMPS thermo logs", "AIMD temperature/MSD/diffusion/drift"],
            "literature": ["JSON/JSONL/CSV evidence", "text/markdown citation extraction", "optional PDF text extraction"],
        },
    }


def _capability_plan(evidence_schema: list[dict[str, Any]]) -> dict[str, Any]:
    required_types = sorted({evidence_type for requirement in evidence_schema for evidence_type in requirement.get("evidenceTypes", [])})
    return {
        "requiredEvidenceTypes": required_types,
        "availableNow": {
            "database": ["materials_search_mp", "materials_fetch_structure", "materials_analyze_structure"],
            "literatureEvidence": ["materials_ingest_evidence with literature-json, literature-text, literature-markdown, literature-pdf, csv"],
            "parserIngestion": ["QE/VASP total energy, band, DOS/Fermi, surface, adsorption, phonon, AIMD", "LAMMPS/MD thermo evidence"],
            "workflowPreparation": ["materials_execute_research_plan with quantum-espresso, vasp, atomate2, aiida in prepare mode"],
            "workflowMonitoring": ["materials_execute_research_plan with executionMode=monitor for output discovery, parsing, and optional claim review"],
            "reporting": ["materials_save_note", "materials_export_report"],
        },
        "requiresExternalIntegration": {
            "literature": "connector or search tool with citation capture",
            "dft/dfpt/md/workflow": "external code execution plus parser ingestion for completed outputs",
            "experiment": "human lab system or imported experimental dataset",
            "safety": "EHS/regulatory data source and human review for hazardous actions",
        },
        "currentLimitations": [
            "prepared external jobs do not become property evidence until parsed outputs are ingested",
            "research-grade claims require an evidence ledger, not only generated plans",
            "costly or hazardous execution remains approval-gated",
        ],
    }


def _claim_policy(evidence_schema: list[dict[str, Any]]) -> dict[str, Any]:
    required = [requirement["id"] for requirement in evidence_schema if requirement.get("requiredForClaim")]
    return {
        "allowedClaimLevels": ["technical-smoke", "candidate-hypothesis", "proxy-shortlist", "property-backed-shortlist", "research-grade-candidate"],
        "researchGradeRequires": [
            "all required evidence requirements pass or have documented waivers",
            "live database provenance and literature ledger are attached",
            "property values come from parsed calculation/experimental/literature artifacts with confidence labels",
            "negative and contradictory evidence are included",
            "uncertainty/conflict engine reports confidence above threshold with no material numeric conflict",
            "reproducibility package contains inputs, outputs, parser versions, and reranking trace",
        ],
        "requiredEvidenceRequirementIds": required,
        "forbiddenWithoutEvidence": ["discovered", "validated", "best material", "experimentally proven", "DFT-confirmed"],
    }


def _validation_matrix(evidence_schema: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matrix = []
    for requirement in evidence_schema:
        matrix.append({
            "evidenceRequirementId": requirement["id"],
            "propertyKeys": requirement.get("propertyKeys") or [],
            "evidenceTypes": requirement.get("evidenceTypes") or [],
            "acceptanceCriteria": requirement.get("acceptanceCriteria"),
            "status": "planned",
            "blockingForResearchGradeClaim": bool(requirement.get("requiredForClaim")),
        })
    return matrix


def _dynamic_calculation_queue(selected: list[dict[str, Any]], protocol: dict[str, Any], budget: dict[str, Any]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    remaining = int(budget["maxCalculations"])
    for step in _global_protocol_steps(protocol):
        if remaining <= 0:
            break
        queue.append(_finalize_protocol_step(step, budget))
        remaining -= 1
    for candidate in selected:
        if remaining <= 0:
            break
        candidate_steps: list[dict[str, Any]] = []
        preflight = _finalize_protocol_step({
            "id": "structure-preflight",
            "label": "Structure fetch and normalization preflight",
            "priority": "required-preflight",
            "method": "fetch_structure + structural sanity checks",
            "costClass": "metadata",
            "estimatedWallTimeHours": 0.05,
            "writesProperties": ["structurePath", "cifPath", "structureQuality"],
            "evidenceTypes": ["database", "workflow"],
            "evidenceRequirementId": "structure-validity",
            "executionBackend": "materials-lab",
            "rationale": "Property calculations need a traceable, normalized input structure.",
            "materialId": candidate.get("materialId"),
            "formula": candidate.get("formula"),
        }, budget)
        preflight["calculationId"] = f"{candidate.get('materialId', 'candidate')}-structure-preflight"
        queue.append(preflight)
        candidate_steps.append(preflight)
        remaining -= 1
        for requirement in protocol.get("evidenceSchema") or []:
            if remaining <= 0:
                break
            property_keys = list(requirement.get("propertyKeys") or [])
            if property_keys and _candidate_has_properties(candidate, property_keys):
                continue
            step = _requirement_step(requirement, candidate)
            step = _finalize_protocol_step(step, budget)
            queue.append(step)
            candidate_steps.append(step)
            remaining -= 1
        candidate["plannedCalculations"] = [step["calculationId"] for step in candidate_steps]
    return queue


def _global_protocol_steps(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": "research-protocol-review",
            "calculationId": "global-research-protocol-review",
            "label": "Research protocol and evidence schema review",
            "priority": "required-preflight",
            "method": "review compiled goal, candidate-generation strategy, evidence schema, claim policy, and stop criteria",
            "costClass": "metadata",
            "estimatedWallTimeHours": 0.25,
            "writesProperties": ["protocolReview"],
            "evidenceTypes": ["workflow"],
            "executionBackend": "agent-review",
            "rationale": "General-purpose research automation needs an explicit evidence contract before execution.",
        },
        {
            "id": "literature-evidence-ledger",
            "calculationId": "global-literature-evidence-ledger",
            "label": "Literature evidence ledger",
            "priority": "evidence-discovery",
            "method": "search, cite, extract PDF/text/table claims, and normalize citation provenance",
            "costClass": "metadata",
            "estimatedWallTimeHours": 1.0,
            "writesProperties": ["literatureBaseline", "knownControls", "failureModes", "citationProvenance"],
            "evidenceTypes": ["literature"],
            "executionBackend": "literature-connector",
            "rationale": "Research-grade claims require literature context and contradictory evidence capture.",
        },
        {
            "id": "database-candidate-search",
            "calculationId": "global-database-candidate-search",
            "label": "Database candidate generation",
            "priority": "evidence-discovery",
            "method": "run database queries and build source-tagged candidate pool",
            "costClass": "metadata",
            "estimatedWallTimeHours": 0.5,
            "writesProperties": ["candidatePool", "databaseSummary"],
            "evidenceTypes": ["database"],
            "executionBackend": "materials_search_mp",
            "rationale": "The agent should discover candidates from database evidence before narrowing.",
        },
    ]


def _candidate_has_properties(candidate: dict[str, Any], property_keys: list[str]) -> bool:
    return all(candidate.get(key) is not None for key in property_keys)


def _requirement_step(requirement: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    evidence_types = list(requirement.get("evidenceTypes") or ["workflow"])
    cost_class = _cost_class_for_evidence(evidence_types)
    material_id = candidate.get("materialId") or "candidate"
    return {
        "id": str(requirement.get("id") or "evidence-step"),
        "calculationId": f"{material_id}-{requirement.get('id', 'evidence-step')}",
        "label": requirement.get("label"),
        "priority": "property-evidence",
        "method": _method_for_requirement(requirement),
        "costClass": cost_class,
        "estimatedWallTimeHours": _hours_for_evidence(evidence_types),
        "writesProperties": list(requirement.get("propertyKeys") or []),
        "evidenceTypes": evidence_types,
        "evidenceRequirementId": requirement.get("id"),
        "executionBackend": _execution_backend_for_evidence(evidence_types),
        "rationale": requirement.get("description"),
        "acceptanceCriteria": requirement.get("acceptanceCriteria"),
        "materialId": candidate.get("materialId"),
        "formula": candidate.get("formula"),
    }


def _method_for_requirement(requirement: dict[str, Any]) -> str:
    evidence_types = set(requirement.get("evidenceTypes") or [])
    if "experiment" in evidence_types:
        return "experimental protocol or imported measurement with calibration metadata"
    if "md" in evidence_types:
        return "molecular dynamics / finite-temperature workflow with parsed outputs"
    if "dfpt" in evidence_types:
        return "DFPT or perturbative electronic-structure workflow with parsed tensors"
    if "dft" in evidence_types:
        return "DFT workflow with convergence checks and parsed properties"
    if "literature" in evidence_types and len(evidence_types) == 1:
        return "citation-backed literature extraction"
    if "database" in evidence_types and len(evidence_types) == 1:
        return "database query and provenance capture"
    return "multi-source evidence collection and parser-backed validation"


def _cost_class_for_evidence(evidence_types: list[str]) -> str:
    evidence = set(evidence_types)
    if evidence.intersection({"experiment", "md", "dfpt"}):
        return "expensive"
    if evidence.intersection({"dft", "workflow"}):
        return "medium"
    return "metadata"


def _hours_for_evidence(evidence_types: list[str]) -> float:
    evidence = set(evidence_types)
    if "experiment" in evidence:
        return 72.0
    if "md" in evidence:
        return 24.0
    if "dfpt" in evidence:
        return 12.0
    if "dft" in evidence:
        return 8.0
    if "workflow" in evidence:
        return 2.0
    if "literature" in evidence:
        return 1.0
    return 0.5


def _execution_backend_for_evidence(evidence_types: list[str]) -> str:
    evidence = set(evidence_types)
    if evidence.intersection({"dft", "dfpt", "md", "workflow"}):
        return "external-backend"
    if "experiment" in evidence:
        return "experimental-system"
    if "literature" in evidence:
        return "literature-connector"
    if "database" in evidence:
        return "database-tool"
    return "agent-review"


def _finalize_protocol_step(step: dict[str, Any], budget: dict[str, Any]) -> dict[str, Any]:
    step = dict(step)
    step.setdefault("calculationId", f"global-{step.get('id', 'step')}")
    step["approvalRequired"] = True
    step["consumesBudget"] = step.get("costClass") != "metadata"
    evidence_types = set(step.get("evidenceTypes") or [])
    expensive_blocked = step.get("costClass") == "expensive" and not budget.get("allowExpensiveCalculations")
    risk_blocked = bool(evidence_types.intersection({"experiment", "safety"}))
    if expensive_blocked:
        step["status"] = "blocked-pending-expensive-approval"
        step["blockedReason"] = "budget.allowExpensiveCalculations is false; explicit approval is required before execution."
    elif risk_blocked:
        step["status"] = "blocked-pending-safety-review"
        step["blockedReason"] = "safety/experiment evidence requires external review and explicit approval before execution."
    else:
        step["status"] = "planned"
    return step


def _dynamic_reranking_policy(protocol: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool": "materials_compare_candidates",
        "criteriaPatch": {
            "screeningLevel": "property-backed-screen",
            "evidenceWeight": 0.25,
        },
        "evidenceSchemaIds": [requirement["id"] for requirement in protocol.get("evidenceSchema") or []],
        "promoteWhen": [
            "required evidenceSchema entries have parsed evidence or documented waivers",
            "literature, database, and property evidence ledgers agree or conflicts are explicitly recorded",
            "no blocking safety, stability, or reproducibility gate remains unresolved",
        ],
    }


def _dynamic_stop_criteria(protocol: dict[str, Any]) -> list[str]:
    required = [requirement["id"] for requirement in protocol.get("evidenceSchema") or [] if requirement.get("requiredForClaim")]
    return [
        "candidateGenerationPlan produces no new candidates after query expansion",
        "budget.maxCalculations or budget.maxWallTimeHours is exhausted",
        "all selected candidates fail at least one required evidence gate",
        "at least one candidate satisfies required evidenceSchema ids: " + ", ".join(required),
        "claimPolicy.researchGradeRequires is satisfied for a promoted candidate",
        "human reviewer or configured governance policy stops the dynamic loop",
    ]


def _dynamic_property_schema(protocol: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for requirement in protocol.get("evidenceSchema") or []:
        for key in requirement.get("propertyKeys") or []:
            if key not in keys:
                keys.append(key)
    return keys


def _select_research_candidates(candidates: list[dict[str, Any]], budget: dict[str, Any]) -> list[dict[str, Any]]:
    selected = []
    for candidate in candidates[: int(budget["maxCandidates"])]:
        evidence = candidate.get("domainEvidence") if isinstance(candidate.get("domainEvidence"), dict) else {}
        selected.append({
            "rank": candidate.get("rank"),
            "materialId": candidate.get("materialId"),
            "formula": candidate.get("formula"),
            "source": candidate.get("source"),
            "family": candidate.get("family"),
            "score": candidate.get("score"),
            "energyAboveHullEv": candidate.get("energyAboveHullEv"),
            "bandGapEv": candidate.get("bandGapEv"),
            "densityGcm3": candidate.get("densityGcm3"),
            "spacegroup": candidate.get("spacegroup"),
            "elements": candidate.get("elements") or [],
            "volume": candidate.get("volume"),
            "sites": candidate.get("sites"),
            "domainEvidenceScore": candidate.get("domainEvidenceScore") or evidence.get("score"),
            "evidenceTier": evidence.get("tier", "unknown"),
            "sourceLevel": evidence.get("sourceLevel", "unknown"),
            "missingProperties": list(evidence.get("missingProperties") or []),
            "nextCalculations": list(evidence.get("nextCalculations") or []),
            "materialsProjectUrl": candidate.get("materialsProjectUrl"),
        })
    return selected


def _approval_gates(queue: list[dict[str, Any]], budget: dict[str, Any], approval_policy: str, protocol: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    total_hours = round(sum(float(step.get("estimatedWallTimeHours") or 0.0) for step in queue), 3)
    expensive = [step["calculationId"] for step in queue if step.get("costClass") == "expensive"]
    safety_or_experiment = [
        step["calculationId"]
        for step in queue
        if set(step.get("evidenceTypes") or []).intersection({"safety", "experiment"})
    ]
    gates = [
        {
            "gateId": "gate-0-human-plan-review",
            "status": "pending",
            "required": approval_policy != "plan-only",
            "blocks": [step["calculationId"] for step in queue],
            "prompt": "Review research goal, evidence schema, candidate-generation strategy, budget, and stop criteria before execution.",
        },
        {
            "gateId": "gate-1-budget-confirmation",
            "status": "pending",
            "required": True,
            "blocks": [step["calculationId"] for step in queue if step.get("consumesBudget")],
            "budgetCheck": {
                "plannedCalculations": len(queue),
                "estimatedWallTimeHours": total_hours,
                "maxWallTimeHours": budget["maxWallTimeHours"],
                "computeBudgetUsd": budget.get("computeBudgetUsd"),
            },
        },
        {
            "gateId": "gate-2-expensive-method-approval",
            "status": "pending",
            "required": bool(expensive),
            "blocks": expensive,
            "prompt": "Approve expensive DFT/DFPT/MD/workflow/experimental calculations explicitly.",
        },
        {
            "gateId": "gate-3-safety-and-experiment-review",
            "status": "pending",
            "required": bool(safety_or_experiment),
            "blocks": safety_or_experiment,
            "prompt": "Review safety, EHS, wet-lab, or experimental actions before execution or recommendation.",
        },
        {
            "gateId": "gate-4-evidence-ledger-acceptance",
            "status": "pending",
            "required": True,
            "blocks": ["update-shortlist", "export-final-report"],
            "prompt": "Accept parsed evidence ledgers before they replace proxy rankings or support research-grade claims.",
        },
    ]
    if protocol:
        gates.append({
            "gateId": "gate-5-claim-policy-review",
            "status": "pending",
            "required": True,
            "blocks": ["research-grade-claim"],
            "prompt": "Verify claimPolicy.researchGradeRequires and required evidenceSchema entries before any discovery claim.",
            "requiredEvidenceRequirementIds": (protocol.get("claimPolicy") or {}).get("requiredEvidenceRequirementIds", []),
        })
    return gates


def _research_plan_warnings(
    selected: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    budget: dict[str, Any],
    approval_policy: str,
    protocol: dict[str, Any] | None = None,
) -> list[str]:
    warnings = []
    if approval_policy != "approval-required":
        warnings.append("Approval policy is not approval-required; the generated plan still marks compute execution as blocked until explicit approval.")
    if not queue:
        warnings.append("No calculations were queued; candidates may already have property evidence or maxCalculations is too small.")
    estimated_hours = sum(float(step.get("estimatedWallTimeHours") or 0.0) for step in queue)
    if estimated_hours > float(budget["maxWallTimeHours"]):
        warnings.append("Planned calculation wall-time estimate exceeds maxWallTimeHours; trim queue before execution.")
    if any(step.get("status") == "blocked-pending-expensive-approval" for step in queue):
        warnings.append("Expensive calculations are present but blocked until allowExpensiveCalculations and explicit approval are set.")
    if any(step.get("status") == "blocked-pending-safety-review" for step in queue):
        warnings.append("Safety or experimental evidence steps are present and require external review before execution.")
    missing_total = sum(len(candidate.get("missingProperties") or []) for candidate in selected)
    if missing_total:
        warnings.append(f"Selected candidates still have {missing_total} missing research-grade property field(s).")
    if not selected:
        warnings.append("No candidates were supplied; this protocol starts with candidate generation and evidence-schema compilation.")
    if protocol:
        warnings.append("Dynamic protocol compiler output is a research plan, not independent scientific validation.")
    return warnings


def _research_plan_markdown(plan: dict[str, Any]) -> str:
    topic = plan.get("topic") or {}
    lines = [
        f"# Dynamic Research Protocol: {topic.get('label') or plan.get('preset')}",
        "",
        "## Objective",
        "",
        str(plan["objective"]),
        "",
        "## Protocol Compiler",
        "",
        f"- Protocol version: `{plan.get('protocolVersion', 'unknown')}`",
        f"- Topic inference: `{topic.get('inference', 'unknown')}`",
        f"- Matched keywords: {', '.join(topic.get('matchedKeywords') or []) or '-'}",
        "",
        "## Autonomy Boundary",
        "",
        f"- Execution status: `{plan['executionStatus']}`",
        f"- Requested autonomy mode: `{plan['autonomyBoundary'].get('requestedAutonomyMode')}`",
        f"- Approval policy: `{plan['autonomyBoundary']['approvalPolicy']}`",
        f"- Can execute without approval: `{plan['autonomyBoundary']['canExecuteWithoutApproval']}`",
        "",
        "## Candidate Generation",
        "",
        f"- Strategy: {(plan.get('candidateGenerationPlan') or {}).get('strategy', '-')}",
        f"- Initial candidate count: {(plan.get('candidateGenerationPlan') or {}).get('initialCandidateCount', 0)}",
        f"- Database queries: {' | '.join((plan.get('databaseSearchPlan') or {}).get('queries') or []) or '-'}",
        f"- Literature queries: {' | '.join((plan.get('literatureReviewPlan') or {}).get('queries') or []) or '-'}",
        "",
        "## Literature Evidence Pipeline",
        "",
        f"- Pipeline version: `{(plan.get('literatureEvidencePipeline') or {}).get('pipelineVersion', '-')}`",
        f"- Parsers: {', '.join((((plan.get('methodRegistry') or {}).get('parserCoverage') or {}).get('literature') or [])) or '-'}",
        f"- Maps to evidence: {', '.join((plan.get('literatureEvidencePipeline') or {}).get('mapsToEvidence') or []) or '-'}",
        "",
        "## Method Registry",
        "",
        f"- Registry version: `{(plan.get('methodRegistry') or {}).get('registryVersion', '-')}`",
        f"- Topic: `{(plan.get('methodRegistry') or {}).get('topicId', '-')}`",
        "",
        "| Requirement | Methods |",
        "| --- | --- |",
    ]
    for requirement_id, methods in ((plan.get("methodRegistry") or {}).get("methodsByRequirement") or {}).items():
        lines.append(f"| {requirement_id} | {', '.join(methods or [])} |")
    if not ((plan.get("methodRegistry") or {}).get("methodsByRequirement") or {}):
        lines.append("| - | - |")
    lines.extend([
        "",
        "## Autonomous Discovery",
        "",
        f"- Enabled: `{(plan.get('autonomousDiscovery') or {}).get('enabled', False)}`",
        f"- Status: `{(plan.get('autonomousDiscovery') or {}).get('status', '-')}`",
        f"- Source mode: `{(plan.get('autonomousDiscovery') or {}).get('sourceMode', '-')}`",
        f"- Queries: {(plan.get('autonomousDiscovery') or {}).get('successfulQueryCount', 0)} / {(plan.get('autonomousDiscovery') or {}).get('queryCount', 0)}",
        f"- Ranked candidates: {(plan.get('autonomousDiscovery') or {}).get('rankedCandidateCount', 0)}",
        f"- Candidate pool: {(plan.get('autonomousDiscovery') or {}).get('candidatePoolPath', '-')}",
        f"- Evidence ledger: {(plan.get('autonomousDiscovery') or {}).get('evidenceLedgerPath', '-')}",
        "",
        "## Evidence Schema",
        "",
        "| ID | Label | Evidence Types | Property Keys | Required |",
        "| --- | --- | --- | --- | --- |",
    ])
    for requirement in plan.get("evidenceSchema") or []:
        lines.append(
            f"| {requirement.get('id')} | {requirement.get('label')} | "
            f"{', '.join(requirement.get('evidenceTypes') or [])} | "
            f"{', '.join(requirement.get('propertyKeys') or [])} | {requirement.get('requiredForClaim')} |"
        )
    lines.extend([
        "",
        "## Selected Candidates",
        "",
        "| Rank | Material | Formula | Evidence Tier | Source Level | Missing Properties | Planned Calculations |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ])
    for candidate in plan.get("selectedCandidates") or []:
        missing = ", ".join(candidate.get("missingProperties") or []) or "-"
        planned = ", ".join(candidate.get("plannedCalculations") or []) or "-"
        lines.append(
            f"| {candidate.get('rank', '')} | {candidate.get('materialId', '')} | {candidate.get('formula', '')} | "
            f"{candidate.get('evidenceTier', '')} | {candidate.get('sourceLevel', '')} | {missing} | {planned} |"
        )
    if not plan.get("selectedCandidates"):
        lines.append("| - | - | - | - | - | Candidate generation pending | - |")
    lines.extend([
        "",
        "## Protocol Queue",
        "",
        "| ID | Material | Label | Backend | Method | Cost | Est. Hours | Writes |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- |",
    ])
    for step in plan["calculationQueue"]:
        lines.append(
            f"| {step['calculationId']} | {step.get('materialId', '') or '-'} | {step['label']} | "
            f"{step.get('executionBackend', '-')} | {step['method']} | "
            f"{step['costClass']} | {step['estimatedWallTimeHours']} | {', '.join(step.get('writesProperties') or [])} |"
        )
    lines.extend([
        "",
        "## Approval Gates",
        "",
        "| Gate | Required | Status | Blocks |",
        "| --- | --- | --- | --- |",
    ])
    for gate in plan["approvalGates"]:
        lines.append(
            f"| {gate['gateId']} | {gate['required']} | {gate['status']} | {', '.join(gate.get('blocks') or [])} |"
        )
    lines.extend([
        "",
        "## Claim Policy",
        "",
        *[f"- {item}" for item in (plan.get("claimPolicy") or {}).get("researchGradeRequires", [])],
        "",
        "## Stop Criteria",
        "",
        *[f"- {item}" for item in plan["stopCriteria"]],
        "",
        "## Warnings",
        "",
        *([f"- {item}" for item in plan.get("warnings") or []] or ["- No warnings."]),
        "",
    ])
    return "\n".join(lines)


def _candidate_summary(item: dict[str, Any]) -> dict[str, Any]:
    material_id = item.get("material_id") or item.get("materialId")
    formula = item.get("formula")
    source = item.get("source", "materials-project")
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
            _property_source(candidate, "ionicConductivityScm") if ionic_conductivity is not None else "missing-proxy",
            ">=1e-4 S/cm screen; >=1e-3 S/cm target",
        ),
        _evidence_gate(
            "migrationBarrier",
            "Li migration barrier",
            migration_barrier,
            _maximum_score(migration_barrier, 0.50, 0.50) if migration_barrier is not None else 0.35,
            _property_source(candidate, "migrationBarrierEv") if migration_barrier is not None else "missing-proxy",
            "<=0.50 eV preferred",
        ),
        _evidence_gate(
            "electrochemicalWindow",
            "Electrochemical window",
            electrochemical_window,
            _minimum_score(electrochemical_window, 4.0) if electrochemical_window is not None else 0.30,
            _property_source(candidate, "electrochemicalWindowV") if electrochemical_window is not None else "missing-proxy",
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
    dielectric_source = _property_source(candidate, "dielectricTotal") if dielectric_total is not None else "composition-proxy"
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
        _evidence_gate("bandOffset", "Band offset leakage guard", _first_present(electron_offset, hole_offset), offset_score, _property_source(candidate, "bandOffsetElectronEv", "bandOffsetHoleEv") if electron_offset is not None or hole_offset is not None else "missing-proxy", "electron/hole offset >=1 eV"),
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
        _evidence_gate("opticalGap", "Optical gap alignment", gap_value, _target_score(gap_value, 1.45), _property_source(candidate, "directBandGapEv") if direct_gap is not None else "mp-summary", "near 1.45 eV"),
        _evidence_gate(
            "absorption",
            "Absorption strength",
            absorption,
            _minimum_score(absorption, 1e4) if absorption is not None else absorber_score,
            _property_source(candidate, "absorptionCoefficientCm1") if absorption is not None else "composition-proxy",
            ">=1e4 cm^-1 preferred",
        ),
        _evidence_gate("absorberChemistry", "Absorber chemistry", None, absorber_score, "composition-proxy", "chalcogenide/halide/oxide absorber proxy"),
        _evidence_gate("carrierTransport", "Carrier transport proxy", _first_present(electron_mass, hole_mass), transport_score, _property_source(candidate, "effectiveMassElectron", "effectiveMassHole") if electron_mass is not None or hole_mass is not None else "missing-proxy", "low balanced effective masses"),
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
        _evidence_gate("transport", "Transport coefficients", _first_present(power_factor, seebeck, thermal_conductivity), transport_score, _property_source(candidate, "seebeckUvK", "powerFactorUwCmK2", "latticeThermalConductivityWmK") if any(value is not None for value in [seebeck, power_factor, thermal_conductivity]) else "missing-proxy", "Seebeck/power factor/kappa"),
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
    estimated_count = sum(1 for gate in gates if gate.get("source") == "estimated-property")
    proxy_count = sum(1 for gate in gates if str(gate.get("source") or "").endswith("proxy") or gate.get("source") == "composition-proxy")
    if property_count >= max(2, len(gates) // 2):
        return "property-backed"
    if property_count > 0:
        return "mixed-property-proxy"
    if estimated_count >= max(2, len(gates) // 2):
        return "estimate-backed"
    if estimated_count > 0:
        return "mixed-estimate-proxy"
    if proxy_count:
        return "proxy-only"
    return "summary-only"


def _property_source(candidate: dict[str, Any], *keys: str) -> str:
    provenance = candidate.get("propertyProvenance")
    if not isinstance(provenance, dict):
        return "property"
    for key in keys:
        entry = provenance.get(key)
        if isinstance(entry, dict) and entry.get("backend") == "dev-smoke":
            return "dev-smoke-diagnostic"
    return "property"


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
