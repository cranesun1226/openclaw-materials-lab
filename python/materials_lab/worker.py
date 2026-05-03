from __future__ import annotations

import csv
import json
import os
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
        "plan_research_loop": lambda: handle_plan_research_loop(request_id=request_id, payload=payload),
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


def handle_plan_research_loop(*, request_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise WorkerError("INVALID_PARAMS", "plan_research_loop requires at least one candidate object.")

    criteria = _prepare_compare_criteria(ensure_dict(payload.get("criteria") or {}, field="criteria"))
    budget = _normalize_research_budget(ensure_dict(payload.get("budget") or {}, field="budget"))
    objective = ensure_string(payload.get("objective"), field="objective", required=False) or _default_research_objective(criteria)
    mode = str(payload.get("mode") or "property-backed").strip().lower()
    approval_policy = str(payload.get("approvalPolicy") or "approval-required").strip().lower()

    plan = _build_research_loop_plan(
        candidates=candidates,
        criteria=criteria,
        budget=budget,
        objective=objective,
        mode=mode,
        approval_policy=approval_policy,
    )
    manifest_path = artifact_dir / f"{plan['planId']}.json"
    report_path = artifact_dir / f"{plan['planId']}.md"
    manifest_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_research_plan_markdown(plan), encoding="utf-8")
    data = {
        "plan": plan,
        "manifestPath": str(manifest_path),
        "reportPath": str(report_path),
    }
    warnings = list(plan.get("warnings") or [])
    return success(
        action="plan_research_loop",
        request_id=request_id,
        summary=f"Planned {len(plan['calculationQueue'])} approval-gated research calculation(s) for {len(plan['selectedCandidates'])} candidate(s).",
        data=data,
        artifacts=[str(manifest_path), str(report_path)],
        warnings=warnings,
    )


def handle_execute_research_plan(*, request_id: str, payload: dict[str, Any], api_key: str | None) -> dict[str, Any]:
    artifact_dir = Path(ensure_string(payload.get("artifactDir"), field="artifactDir"))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    backend = str(payload.get("backend") or "local-surrogate").strip().lower()
    plan = _load_research_plan(payload)
    if not isinstance(plan.get("calculationQueue"), list):
        raise WorkerError("INVALID_PARAMS", "execute_research_plan requires a plan with calculationQueue.")

    max_steps = int(payload.get("maxSteps") or len(plan["calculationQueue"]))
    if backend == "local-surrogate":
        allow_blocked_surrogate = ensure_bool(payload.get("allowBlockedSurrogate"), field="allowBlockedSurrogate", default=False)
        execution = _execute_local_surrogate_plan(
            plan=plan,
            artifact_dir=artifact_dir,
            api_key=api_key,
            max_steps=max_steps,
            allow_blocked_surrogate=allow_blocked_surrogate,
        )
    elif backend in {"quantum-espresso", "vasp", "atomate2", "aiida"}:
        execution = _execute_external_backend_plan(
            plan=plan,
            artifact_dir=artifact_dir,
            api_key=api_key,
            backend=backend,
            max_steps=max_steps,
            execution_mode=str(payload.get("executionMode") or "prepare").strip().lower(),
            allow_execution=ensure_bool(payload.get("allowExecution"), field="allowExecution", default=False),
            backend_config=ensure_dict(payload.get("backendConfig") or {}, field="backendConfig"),
        )
    else:
        raise WorkerError(
            "BACKEND_NOT_AVAILABLE",
            f"Research backend '{backend}' is not available in this build.",
            hint="Use one of: local-surrogate, quantum-espresso, vasp, atomate2, aiida.",
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


def _execute_local_surrogate_plan(
    *,
    plan: dict[str, Any],
    artifact_dir: Path,
    api_key: str | None,
    max_steps: int,
    allow_blocked_surrogate: bool,
) -> dict[str, Any]:
    run_id = f"{plan.get('planId', 'research-plan')}-local-surrogate-{int(time.time() * 1000)}"
    run_dir = artifact_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    selected_by_id = {
        str(candidate.get("materialId")): candidate
        for candidate in plan.get("selectedCandidates") or []
        if candidate.get("materialId")
    }
    completed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    property_updates: dict[str, dict[str, Any]] = {}
    warnings: list[str] = [
        "local-surrogate backend produces low-confidence property estimates; do not treat them as DFT/experimental values."
    ]

    for step in (plan.get("calculationQueue") or [])[: max(0, max_steps)]:
        if not isinstance(step, dict):
            continue
        status = str(step.get("status") or "planned")
        calculation_id = str(step.get("calculationId") or step.get("id") or f"calculation-{len(completed) + len(skipped) + 1}")
        if status.startswith("blocked") and not allow_blocked_surrogate:
            skipped.append({
                "calculationId": calculation_id,
                "materialId": step.get("materialId"),
                "status": "skipped-blocked",
                "reason": step.get("blockedReason") or "calculation is blocked by the plan approval gates",
            })
            continue

        material_id = str(step.get("materialId") or "")
        candidate = selected_by_id.get(material_id, {"materialId": material_id, "formula": step.get("formula")})
        result = _run_local_surrogate_step(step, candidate, plan, api_key=api_key)
        result_path = run_dir / f"{_safe_file_stem(calculation_id)}.json"
        result["resultPath"] = str(result_path)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        completed.append(result)
        update = property_updates.setdefault(material_id, _candidate_update_base(candidate, plan))
        _merge_property_result(update, result)

    updated_candidates = [_finalize_candidate_update(update) for update in property_updates.values()]
    manifest = {
        "runId": run_id,
        "backend": "local-surrogate",
        "planId": plan.get("planId"),
        "preset": plan.get("preset"),
        "generatedAt": int(time.time()),
        "completedCalculations": len(completed),
        "skippedCalculations": len(skipped),
        "allowBlockedSurrogate": allow_blocked_surrogate,
        "propertyUpdates": updated_candidates,
        "completed": completed,
        "skipped": skipped,
        "rerankingPayload": {
            "criteriaPatch": {
                **((plan.get("rerankingPolicy") or {}).get("criteriaPatch") or {}),
                "screeningLevel": "property-backed-screen",
            },
            "candidates": updated_candidates,
        },
        "warnings": warnings,
    }
    manifest_path = run_dir / "execution-manifest.json"
    report_path = run_dir / "execution-report.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(_surrogate_execution_markdown(manifest), encoding="utf-8")
    return {
        "runId": run_id,
        "backend": "local-surrogate",
        "statusSummary": "Executed local-surrogate backend",
        "manifestPath": str(manifest_path),
        "reportPath": str(report_path),
        "resultPaths": [str(Path(result["resultPath"])) for result in completed],
        "inputPaths": [],
        "completedCalculations": len(completed),
        "preparedCalculations": 0,
        "submittedCalculations": 0,
        "skippedCalculations": len(skipped),
        "propertyUpdates": updated_candidates,
        "rerankingPayload": manifest["rerankingPayload"],
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
) -> dict[str, Any]:
    if execution_mode not in {"prepare", "submit"}:
        raise WorkerError("INVALID_PARAMS", "executionMode must be 'prepare' or 'submit'.")
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
    material = _fetch_material_for_backend(str(candidate.get("materialId") or ""), str(candidate.get("formula") or step.get("formula") or ""), api_key=api_key)
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


def _fetch_material_for_backend(material_id: str, formula: str, *, api_key: str | None) -> dict[str, Any]:
    if material_id:
        try:
            material, _used_offline = fetch_material(material_id, api_key=api_key, allow_offline=True)
            summary = _candidate_summary(material)
            summary["structure"] = material.get("structure")
            return summary
        except Exception:
            pass
    return {"materialId": material_id, "formula": formula, "source": "mock", "structure": None}


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


def _run_local_surrogate_step(step: dict[str, Any], candidate: dict[str, Any], plan: dict[str, Any], *, api_key: str | None) -> dict[str, Any]:
    material_id = str(step.get("materialId") or candidate.get("materialId") or "")
    formula = str(step.get("formula") or candidate.get("formula") or "")
    material = _fetch_material_summary_for_surrogate(material_id, formula, api_key=api_key)
    merged_candidate = {**material, **candidate, "materialId": material.get("materialId") or material_id, "formula": material.get("formula") or formula}
    descriptors = _composition_descriptors(merged_candidate)
    calculation_type = str(step.get("id") or "")
    properties = _surrogate_properties_for_step(calculation_type, merged_candidate, descriptors, str(plan.get("preset") or "generic"))
    return {
        "calculationId": step.get("calculationId"),
        "materialId": merged_candidate.get("materialId"),
        "formula": merged_candidate.get("formula"),
        "backend": "local-surrogate",
        "status": "completed-surrogate",
        "calculationType": calculation_type,
        "label": step.get("label"),
        "method": step.get("method"),
        "costClass": step.get("costClass"),
        "estimatedWallTimeHours": step.get("estimatedWallTimeHours"),
        "properties": properties,
        "provenance": {
            "backend": "local-surrogate",
            "confidence": "low",
            "generatedAt": int(time.time()),
            "basis": "composition, MP summary fields, and deterministic domain heuristics",
            "notAReplacementFor": "DFT, DFPT, NEB, AIMD, Boltzmann transport, or experiment",
        },
    }


def _fetch_material_summary_for_surrogate(material_id: str, formula: str, *, api_key: str | None) -> dict[str, Any]:
    if material_id:
        try:
            material, _used_offline = fetch_material(material_id, api_key=api_key, allow_offline=True)
            return _candidate_summary(material)
        except Exception:
            pass
    return {
        "materialId": material_id,
        "formula": formula,
        "source": "mock",
    }


def _surrogate_properties_for_step(
    calculation_type: str,
    candidate: dict[str, Any],
    descriptors: dict[str, Any],
    preset: str,
) -> dict[str, Any]:
    if calculation_type == "structure-preflight":
        return {
            "structureQuality": round(_structure_quality_surrogate(candidate, descriptors), 6),
        }
    if preset == "high-k-dielectric":
        return _high_k_surrogate_properties(calculation_type, candidate, descriptors)
    if preset == "solid-electrolyte":
        return _solid_electrolyte_surrogate_properties(calculation_type, candidate, descriptors)
    if preset == "photovoltaic-absorber":
        return _photovoltaic_surrogate_properties(calculation_type, candidate, descriptors)
    if preset == "thermoelectric":
        return _thermoelectric_surrogate_properties(calculation_type, candidate, descriptors)
    return {"domainSpecificProperty": round(_domain_descriptor_score(descriptors, preset), 6)}


def _high_k_surrogate_properties(calculation_type: str, candidate: dict[str, Any], descriptors: dict[str, Any]) -> dict[str, Any]:
    elements = set(str(item) for item in descriptors.get("elements") or [])
    density = _numeric(candidate.get("densityGcm3"), 5.0)
    gap = _numeric(candidate.get("bandGapEv"), 3.0)
    high_k_strength = _high_k_chemistry_score(elements, descriptors, _infer_material_family(candidate, {"preset": "high-k-dielectric"}))
    if calculation_type == "dfpt-dielectric-tensor":
        total = 3.5 + high_k_strength * 28.0 + max(0.0, density - 4.0) * 0.8
        if elements.intersection({"Ba", "Sr"}) and "Ti" in elements:
            total += 55.0
        if elements.intersection({"Al", "Si"}) and not elements.intersection({"Hf", "Zr", "Ti", "Ta", "Nb", "La", "Y"}):
            total = min(total, 9.5 if "Al" in elements else 4.5)
        return {
            "dielectricTotal": round(total, 4),
            "dielectricElectronic": round(max(1.8, min(total * 0.22, 7.5)), 4),
        }
    if calculation_type == "band-alignment":
        offset = max(0.25, min(gap * 0.32, 2.4))
        return {
            "bandOffsetElectronEv": round(offset, 4),
            "bandOffsetHoleEv": round(max(0.25, min(gap - offset, 3.5)), 4),
        }
    if calculation_type == "interface-reaction":
        base = 0.04 if elements.intersection({"Al", "Si", "Hf", "Zr"}) else 0.16
        return {"interfaceReactionEnergyEv": round(base + max(0.0, density - 7.0) * 0.015, 4)}
    if calculation_type == "phonon-stability":
        return {"phononStability": round(max(0.0, min(1.0, 1.0 - _numeric(candidate.get("energyAboveHullEv"), 0.05) / 0.18)), 4)}
    return {}


def _solid_electrolyte_surrogate_properties(calculation_type: str, candidate: dict[str, Any], descriptors: dict[str, Any]) -> dict[str, Any]:
    li_fraction = float(descriptors.get("liAtomicFraction") or 0.0)
    framework = max(float(descriptors.get("chalcogenideAtomicFraction") or 0.0), float(descriptors.get("halogenAtomicFraction") or 0.0), float(descriptors.get("oxygenAtomicFraction") or 0.0) * 0.75)
    if calculation_type == "li-migration-barrier":
        return {"migrationBarrierEv": round(max(0.18, 0.75 - li_fraction * 0.9 - framework * 0.18), 4)}
    if calculation_type == "aimd-ionic-conductivity":
        conductivity = 1e-6 + li_fraction * framework * 4e-3
        return {"ionicConductivityScm": round(conductivity, 8)}
    if calculation_type == "electrochemical-window":
        return {"electrochemicalWindowV": round(2.5 + _numeric(candidate.get("bandGapEv"), 3.0) * 0.45, 4)}
    if calculation_type == "interface-stability":
        return {"interfaceReactionEnergyEv": round(max(0.02, _numeric(candidate.get("energyAboveHullEv"), 0.05) + 0.05), 4)}
    return {}


def _photovoltaic_surrogate_properties(calculation_type: str, candidate: dict[str, Any], descriptors: dict[str, Any]) -> dict[str, Any]:
    gap = _numeric(candidate.get("bandGapEv"), 1.5)
    absorber = max(float(descriptors.get("chalcogenideAtomicFraction") or 0.0), float(descriptors.get("halogenAtomicFraction") or 0.0) * 0.85, float(descriptors.get("oxygenAtomicFraction") or 0.0) * 0.45)
    if calculation_type == "optical-absorption":
        return {
            "directBandGapEv": round(max(0.1, gap + (0.10 if absorber < 0.4 else -0.05)), 4),
            "absorptionCoefficientCm1": round(2500 + absorber * 45000, 2),
        }
    if calculation_type == "band-edge-alignment":
        return {"cbmEv": round(-4.0 + (gap - 1.4) * 0.25, 4), "vbmEv": round(-4.0 - gap, 4)}
    if calculation_type == "defect-tolerance":
        return {"defectToleranceScore": round(max(0.0, min(1.0, absorber * 0.75 + _target_score(gap, 1.45) * 0.25)), 4)}
    if calculation_type == "carrier-masses":
        return {
            "effectiveMassElectron": round(max(0.12, 1.2 - absorber * 0.65), 4),
            "effectiveMassHole": round(max(0.15, 1.4 - absorber * 0.55), 4),
        }
    return {}


def _thermoelectric_surrogate_properties(calculation_type: str, candidate: dict[str, Any], descriptors: dict[str, Any]) -> dict[str, Any]:
    heavy = float(descriptors.get("heavyAtomicFraction") or 0.0)
    gap_score = _target_score(candidate.get("bandGapEv"), 0.35)
    complexity = min(1.0, float(descriptors.get("numElements") or 1.0) / 4.0)
    if calculation_type == "boltzmann-transport":
        return {
            "seebeckUvK": round(80 + gap_score * 180 + heavy * 90, 4),
            "powerFactorUwCmK2": round(4 + gap_score * 24 + complexity * 12, 4),
        }
    if calculation_type == "lattice-thermal-conductivity":
        return {"latticeThermalConductivityWmK": round(max(0.35, 6.0 - heavy * 4.0 - complexity * 1.5), 4)}
    if calculation_type == "carrier-concentration-sweep":
        return {"carrierConcentrationCm3": round(5e18 + gap_score * 8e19, 2)}
    if calculation_type == "phonon-stability":
        return {"phononStability": round(max(0.0, min(1.0, 1.0 - _numeric(candidate.get("energyAboveHullEv"), 0.05) / 0.25)), 4)}
    return {}


def _structure_quality_surrogate(candidate: dict[str, Any], descriptors: dict[str, Any]) -> float:
    score = 0.55
    if candidate.get("spacegroup"):
        score += 0.15
    if candidate.get("materialsProjectUrl") or candidate.get("source") == "materials-project":
        score += 0.15
    if descriptors.get("numElements"):
        score += 0.10
    return max(0.0, min(score, 1.0))


def _candidate_update_base(candidate: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "materialId": candidate.get("materialId"),
        "formula": candidate.get("formula"),
        "source": candidate.get("source") or "materials-project",
        "rank": candidate.get("rank"),
        "score": candidate.get("score"),
        "family": candidate.get("family"),
        "energyAboveHullEv": candidate.get("energyAboveHullEv"),
        "bandGapEv": candidate.get("bandGapEv"),
        "densityGcm3": candidate.get("densityGcm3"),
        "spacegroup": candidate.get("spacegroup"),
        "elements": candidate.get("elements") or [],
        "volume": candidate.get("volume"),
        "sites": candidate.get("sites"),
        "materialsProjectUrl": candidate.get("materialsProjectUrl"),
        "propertyProvenance": {},
        "calculationStatus": {},
        "screeningLevel": "property-backed-screen",
        "notes": [f"Updated by {plan.get('planId')} using local-surrogate backend."],
    }


def _merge_property_result(update: dict[str, Any], result: dict[str, Any]) -> None:
    properties = result.get("properties") or {}
    provenance = result.get("provenance") or {}
    calculation_id = str(result.get("calculationId") or result.get("calculationType") or "unknown")
    for key, value in properties.items():
        update[key] = value
        update["propertyProvenance"][key] = {
            **provenance,
            "calculationId": calculation_id,
            "calculationType": result.get("calculationType"),
            "resultPath": result.get("resultPath"),
        }
    update["calculationStatus"][calculation_id] = {
        "status": result.get("status"),
        "backend": result.get("backend"),
        "resultPath": result.get("resultPath"),
        "writesProperties": list(properties.keys()),
    }


def _finalize_candidate_update(update: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in update.items() if value is not None}


def _surrogate_execution_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        f"# Research Plan Execution: {manifest['runId']}",
        "",
        "## Backend",
        "",
        "- Backend: `local-surrogate`",
        "- Confidence: `low`",
        "- These values are calculation-adapter smoke outputs, not DFT or experimental results.",
        "",
        "## Summary",
        "",
        f"- Completed calculations: {manifest['completedCalculations']}",
        f"- Skipped calculations: {manifest['skippedCalculations']}",
        f"- Allow blocked surrogate execution: `{manifest['allowBlockedSurrogate']}`",
        "",
        "## Candidate Property Updates",
        "",
        "| Material | Formula | Updated Properties |",
        "| --- | --- | --- |",
    ]
    for candidate in manifest["propertyUpdates"]:
        property_keys = [
            key
            for key in candidate.keys()
            if key not in {
                "materialId",
                "formula",
                "source",
                "rank",
                "score",
                "family",
                "energyAboveHullEv",
                "bandGapEv",
                "densityGcm3",
                "materialsProjectUrl",
                "propertyProvenance",
                "calculationStatus",
                "screeningLevel",
                "notes",
            }
        ]
        lines.append(f"| {candidate.get('materialId')} | {candidate.get('formula')} | {', '.join(property_keys) or '-'} |")
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


def _build_research_loop_plan(
    *,
    candidates: list[dict[str, Any]],
    criteria: dict[str, Any],
    budget: dict[str, Any],
    objective: str,
    mode: str,
    approval_policy: str,
) -> dict[str, Any]:
    preset = str(criteria.get("preset") or _infer_plan_preset(candidates) or "generic")
    selected = _select_research_candidates(candidates, budget)
    plan_id = f"{preset}-research-loop-{int(time.time() * 1000)}"
    queue = _calculation_queue(selected, preset, budget)
    approval_gates = _approval_gates(queue, budget, approval_policy)
    warnings = _research_plan_warnings(selected, queue, budget, approval_policy)
    return {
        "planId": plan_id,
        "mode": mode if mode in {"property-backed", "closed-loop"} else "property-backed",
        "preset": preset,
        "objective": objective,
        "executionStatus": "planned-not-started",
        "autonomyBoundary": {
            "approvalPolicy": approval_policy if approval_policy in {"plan-only", "approval-required"} else "approval-required",
            "canExecuteWithoutApproval": False,
            "allowedActionsBeforeApproval": ["write-plan-artifacts", "validate-input-artifacts"],
            "blockedActionsBeforeApproval": [
                "run-dft",
                "submit-hpc-job",
                "call-paid-compute-service",
                "overwrite-candidate-ranking",
            ],
        },
        "budget": budget,
        "selectedCandidates": selected,
        "calculationQueue": queue,
        "approvalGates": approval_gates,
        "rerankingPolicy": _reranking_policy(preset),
        "loopPolicy": {
            "maxIterations": budget["maxLoopIterations"],
            "afterEachIteration": [
                "parse calculation artifacts into candidate property fields",
                "rerun materials_compare_candidates with evidenceWeight enabled",
                "compare domainCoverage against previous iteration",
                "stop, continue, or request human review based on stopCriteria",
            ],
        },
        "stopCriteria": _stop_criteria(preset),
        "propertySchema": _domain_property_schema(preset),
        "warnings": warnings,
    }


def _infer_plan_preset(candidates: list[dict[str, Any]]) -> str:
    for candidate in candidates:
        evidence = candidate.get("domainEvidence")
        if isinstance(evidence, dict) and evidence.get("preset"):
            return str(evidence["preset"])
    for candidate in candidates:
        level = candidate.get("screeningLevel")
        if isinstance(level, str) and "solid" in level:
            return "solid-electrolyte"
    return "generic"


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


def _calculation_queue(selected: list[dict[str, Any]], preset: str, budget: dict[str, Any]) -> list[dict[str, Any]]:
    recipes = _calculation_recipes(preset)
    queue: list[dict[str, Any]] = []
    remaining = int(budget["maxCalculations"])
    for candidate in selected:
        if remaining <= 0:
            break
        missing = set(str(item) for item in candidate.get("missingProperties") or [])
        candidate_steps = []
        for recipe in recipes:
            if remaining <= 0:
                break
            writes = set(recipe.get("writesProperties") or [])
            priority = str(recipe.get("priority") or "normal")
            if missing and not writes.intersection(missing) and priority != "required-preflight":
                continue
            step = dict(recipe)
            step["calculationId"] = f"{candidate.get('materialId', 'unknown')}-{recipe['id']}"
            step["materialId"] = candidate.get("materialId")
            step["formula"] = candidate.get("formula")
            expensive_blocked = recipe.get("costClass") == "expensive" and not budget.get("allowExpensiveCalculations")
            step["status"] = "blocked-pending-expensive-approval" if expensive_blocked else "planned"
            if expensive_blocked:
                step["blockedReason"] = "budget.allowExpensiveCalculations is false; explicit approval is required before execution."
            step["approvalRequired"] = True
            step["consumesBudget"] = recipe.get("costClass") != "metadata"
            candidate_steps.append(step)
            queue.append(step)
            remaining -= 1
        candidate["plannedCalculations"] = [step["calculationId"] for step in candidate_steps]
    return queue


def _calculation_recipes(preset: str) -> list[dict[str, Any]]:
    universal_preflight = {
        "id": "structure-preflight",
        "label": "Structure fetch and normalization preflight",
        "priority": "required-preflight",
        "method": "fetch_structure + structural sanity checks",
        "costClass": "metadata",
        "estimatedWallTimeHours": 0.05,
        "writesProperties": ["structurePath", "cifPath", "structureQuality"],
        "rationale": "Property calculations need a traceable, normalized input structure.",
    }
    by_preset = {
        "solid-electrolyte": [
            universal_preflight,
            _recipe("li-migration-barrier", "Li migration barrier", "NEB or bond-valence pathway screen", "medium", 8.0, ["migrationBarrierEv"]),
            _recipe("aimd-ionic-conductivity", "Finite-temperature ionic conductivity", "AIMD or surrogate conductivity workflow", "expensive", 24.0, ["ionicConductivityScm"]),
            _recipe("electrochemical-window", "Electrochemical stability window", "grand-potential phase stability", "medium", 4.0, ["electrochemicalWindowV"]),
            _recipe("interface-stability", "Electrode interface reaction", "interfacial reaction energy screen", "medium", 5.0, ["interfaceReactionEnergyEv"]),
        ],
        "high-k-dielectric": [
            universal_preflight,
            _recipe("dfpt-dielectric-tensor", "DFPT dielectric tensor", "DFPT electronic + ionic dielectric calculation", "expensive", 12.0, ["dielectricTotal", "dielectricElectronic"]),
            _recipe("band-alignment", "Band offsets", "absolute band alignment against target channel", "medium", 6.0, ["bandOffsetElectronEv", "bandOffsetHoleEv"]),
            _recipe("interface-reaction", "Interface reaction energy", "interface thermodynamics against target channel", "medium", 6.0, ["interfaceReactionEnergyEv"]),
            _recipe("phonon-stability", "Phonon stability", "phonon or imaginary-mode screen", "expensive", 18.0, ["phononStability"]),
        ],
        "photovoltaic-absorber": [
            universal_preflight,
            _recipe("optical-absorption", "Optical absorption", "direct/indirect gap and absorption spectrum", "medium", 8.0, ["absorptionCoefficientCm1", "directBandGapEv"]),
            _recipe("band-edge-alignment", "Band-edge alignment", "absolute CBM/VBM alignment", "medium", 5.0, ["cbmEv", "vbmEv"]),
            _recipe("defect-tolerance", "Defect tolerance", "dominant intrinsic defect formation-energy screen", "expensive", 24.0, ["defectToleranceScore"]),
            _recipe("carrier-masses", "Carrier effective masses", "band curvature effective-mass calculation", "medium", 4.0, ["effectiveMassElectron", "effectiveMassHole"]),
        ],
        "thermoelectric": [
            universal_preflight,
            _recipe("boltzmann-transport", "Boltzmann transport", "Seebeck and power-factor sweep", "medium", 8.0, ["seebeckUvK", "powerFactorUwCmK2"]),
            _recipe("lattice-thermal-conductivity", "Lattice thermal conductivity", "phonon/BTE or surrogate kappa lattice", "expensive", 30.0, ["latticeThermalConductivityWmK"]),
            _recipe("carrier-concentration-sweep", "Carrier concentration sweep", "doping-dependent transport sweep", "medium", 8.0, ["carrierConcentrationCm3"]),
            _recipe("phonon-stability", "High-temperature stability", "phonon/dynamic stability screen", "expensive", 18.0, ["phononStability"]),
        ],
    }
    return by_preset.get(preset, [
        universal_preflight,
        _recipe("domain-property-model", "Domain property model", "domain-specific property calculation", "medium", 6.0, ["domainSpecificProperty"]),
    ])


def _recipe(id_: str, label: str, method: str, cost_class: str, hours: float, writes: list[str]) -> dict[str, Any]:
    return {
        "id": id_,
        "label": label,
        "priority": "property",
        "method": method,
        "costClass": cost_class,
        "estimatedWallTimeHours": hours,
        "writesProperties": writes,
        "rationale": f"Promotes proxy evidence into property-backed evidence for {', '.join(writes)}.",
    }


def _approval_gates(queue: list[dict[str, Any]], budget: dict[str, Any], approval_policy: str) -> list[dict[str, Any]]:
    total_hours = round(sum(float(step.get("estimatedWallTimeHours") or 0.0) for step in queue), 3)
    expensive = [step["calculationId"] for step in queue if step.get("costClass") == "expensive"]
    return [
        {
            "gateId": "gate-0-human-plan-review",
            "status": "pending",
            "required": approval_policy != "plan-only",
            "blocks": [step["calculationId"] for step in queue],
            "prompt": "Review objective, selected candidates, budget, and stop criteria before any calculation is executed.",
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
            "prompt": "Approve expensive DFPT/AIMD/phonon/defect calculations explicitly.",
        },
        {
            "gateId": "gate-3-rerank-acceptance",
            "status": "pending",
            "required": True,
            "blocks": ["update-shortlist", "export-final-report"],
            "prompt": "Accept parsed property results before they replace the proxy shortlist.",
        },
    ]


def _reranking_policy(preset: str) -> dict[str, Any]:
    return {
        "tool": "materials_compare_candidates",
        "criteriaPatch": {
            "preset": preset,
            "screeningLevel": "property-backed-screen",
            "evidenceWeight": 0.20,
        },
        "promoteWhen": [
            "domainEvidence.sourceLevel is mixed-property-proxy or property-backed",
            "domainEvidence.missingCount decreases versus previous iteration",
            "no fail gate appears in a required safety/stability criterion",
        ],
    }


def _stop_criteria(preset: str) -> list[str]:
    return [
        "at least one candidate reaches domainEvidence.tier == research-shortlist",
        "domainCoverage.sourceLevelCounts.property-backed is nonzero",
        "budget.maxCalculations or budget.maxWallTimeHours is exhausted",
        "all candidates retain fail gates after required property calculations",
        f"human reviewer stops the {preset} loop",
    ]


def _domain_property_schema(preset: str) -> list[str]:
    return {
        "solid-electrolyte": ["ionicConductivityScm", "migrationBarrierEv", "electrochemicalWindowV", "interfaceReactionEnergyEv"],
        "high-k-dielectric": ["dielectricTotal", "dielectricElectronic", "bandOffsetElectronEv", "bandOffsetHoleEv", "interfaceReactionEnergyEv", "phononStability"],
        "photovoltaic-absorber": ["absorptionCoefficientCm1", "directBandGapEv", "cbmEv", "vbmEv", "defectToleranceScore", "effectiveMassElectron", "effectiveMassHole"],
        "thermoelectric": ["seebeckUvK", "powerFactorUwCmK2", "latticeThermalConductivityWmK", "carrierConcentrationCm3", "phononStability"],
    }.get(preset, ["domainSpecificProperty"])


def _research_plan_warnings(
    selected: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    budget: dict[str, Any],
    approval_policy: str,
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
        warnings.append("Expensive calculations are present but blocked until allowExpensiveCalculations and human approval are explicit.")
    missing_total = sum(len(candidate.get("missingProperties") or []) for candidate in selected)
    if missing_total:
        warnings.append(f"Selected candidates still have {missing_total} missing research-grade property field(s).")
    return warnings


def _research_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        f"# Research Loop Plan: {plan['preset']}",
        "",
        "## Objective",
        "",
        str(plan["objective"]),
        "",
        "## Autonomy Boundary",
        "",
        f"- Execution status: `{plan['executionStatus']}`",
        f"- Approval policy: `{plan['autonomyBoundary']['approvalPolicy']}`",
        f"- Can execute without approval: `{plan['autonomyBoundary']['canExecuteWithoutApproval']}`",
        "",
        "## Selected Candidates",
        "",
        "| Rank | Material | Formula | Evidence Tier | Source Level | Missing Properties | Planned Calculations |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for candidate in plan["selectedCandidates"]:
        missing = ", ".join(candidate.get("missingProperties") or []) or "-"
        planned = ", ".join(candidate.get("plannedCalculations") or []) or "-"
        lines.append(
            f"| {candidate.get('rank', '')} | {candidate.get('materialId', '')} | {candidate.get('formula', '')} | "
            f"{candidate.get('evidenceTier', '')} | {candidate.get('sourceLevel', '')} | {missing} | {planned} |"
        )
    lines.extend([
        "",
        "## Calculation Queue",
        "",
        "| ID | Material | Label | Method | Cost | Est. Hours | Writes |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ])
    for step in plan["calculationQueue"]:
        lines.append(
            f"| {step['calculationId']} | {step.get('materialId', '')} | {step['label']} | {step['method']} | "
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
    surrogate_count = sum(1 for gate in gates if gate.get("source") == "surrogate-property")
    proxy_count = sum(1 for gate in gates if str(gate.get("source") or "").endswith("proxy") or gate.get("source") == "composition-proxy")
    if property_count >= max(2, len(gates) // 2):
        return "property-backed"
    if property_count > 0:
        return "mixed-property-proxy"
    if surrogate_count >= max(2, len(gates) // 2):
        return "surrogate-backed"
    if surrogate_count > 0:
        return "mixed-surrogate-proxy"
    if proxy_count:
        return "proxy-only"
    return "summary-only"


def _property_source(candidate: dict[str, Any], *keys: str) -> str:
    provenance = candidate.get("propertyProvenance")
    if not isinstance(provenance, dict):
        return "property"
    for key in keys:
        entry = provenance.get(key)
        if isinstance(entry, dict) and entry.get("backend") == "local-surrogate":
            return "surrogate-property"
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
