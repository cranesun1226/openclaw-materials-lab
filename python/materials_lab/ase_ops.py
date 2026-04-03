from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from ase import Atoms  # type: ignore
    from ase.calculators.emt import EMT  # type: ignore
    from ase.io import write  # type: ignore
    from ase.optimize import BFGS  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    Atoms = None
    EMT = None
    BFGS = None
    write = None

from .schemas import WorkerError


SUPPORTED_EMT_ELEMENTS = {"Al", "Cu", "Ag", "Au", "Ni", "Pd", "Pt", "C", "H", "O", "N"}


def run_relaxation(
    *,
    structure_data: dict[str, Any],
    artifact_dir: str,
    steps: int = 100,
    fmax_ev_a: float = 0.05,
    calculator: str = "EMT",
) -> tuple[dict[str, Any], list[str], list[str]]:
    artifact_root = Path(artifact_dir)
    artifact_root.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    artifacts: list[str] = []

    if Atoms is None or EMT is None or BFGS is None or write is None:
        warnings.append("ASE is unavailable; returning a stub relaxation result.")
        summary_metrics = {"executed": False, "calculator": calculator, "reason": "ASE not installed"}
        stub_path = artifact_root / "relaxation-stub.json"
        stub_path.write_text(json.dumps(summary_metrics, indent=2) + "\n", encoding="utf-8")
        artifacts.append(str(stub_path))
        return summary_metrics, artifacts, warnings

    sites = structure_data.get("sites") or []
    species = [site.get("element") for site in sites if isinstance(site, dict)]
    if any(element not in SUPPORTED_EMT_ELEMENTS for element in species):
        warnings.append("Requested structure contains elements not supported by the EMT calculator; returning a stub result.")
        summary_metrics = {"executed": False, "calculator": calculator, "reason": "unsupported elements"}
        stub_path = artifact_root / "relaxation-stub.json"
        stub_path.write_text(json.dumps(summary_metrics, indent=2) + "\n", encoding="utf-8")
        artifacts.append(str(stub_path))
        return summary_metrics, artifacts, warnings

    if str(calculator).upper() != "EMT":
        raise WorkerError(
            "UNSUPPORTED_CALCULATOR",
            f"Calculator '{calculator}' is not supported in v1.",
            hint="Use the default EMT stub path or extend ase_ops.py with another calculator.",
        )

    positions = [site.get("coords") for site in sites]
    atoms = Atoms(symbols=species, scaled_positions=positions, cell=structure_data.get("lattice"), pbc=True)
    atoms.calc = EMT()
    optimizer = BFGS(atoms, logfile=None)
    optimizer.run(fmax=fmax_ev_a, steps=steps)

    xyz_path = artifact_root / "relaxed.xyz"
    write(str(xyz_path), atoms)
    artifacts.append(str(xyz_path))

    summary_metrics = {
        "executed": True,
        "calculator": calculator,
        "finalEnergyEv": float(atoms.get_potential_energy()),
        "numAtoms": len(atoms),
    }
    summary_path = artifact_root / "relaxation-summary.json"
    summary_path.write_text(json.dumps(summary_metrics, indent=2) + "\n", encoding="utf-8")
    artifacts.append(str(summary_path))
    return summary_metrics, artifacts, warnings
