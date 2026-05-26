from __future__ import annotations

import json
import math
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
SEVENNET_DEFAULT_MODEL = "7net-omni"
SEVENNET_DEFAULT_MODAL = "mpa"
SEVENNET_DEFAULT_DEVICE = "auto"
SEVENNET_CITATION_HINT = (
    "SevenNet / 7net-omni ML interatomic potential; cite MDIL-SNU/SevenNet and the selected model in reports."
)


def run_relaxation(
    *,
    structure_data: dict[str, Any],
    artifact_dir: str,
    steps: int = 100,
    fmax_ev_a: float = 0.05,
    calculator: str = "EMT",
    seven_net_model: str | None = None,
    seven_net_modal: str | None = None,
    device: str | None = None,
) -> tuple[dict[str, Any], list[str], list[str]]:
    artifact_root = Path(artifact_dir)
    artifact_root.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    artifacts: list[str] = []
    calculator_name = _normalize_calculator(calculator)

    ase_core_missing = Atoms is None or BFGS is None or write is None
    calculator_missing = calculator_name == "EMT" and EMT is None
    if ase_core_missing or calculator_missing:
        if calculator_name == "SevenNet":
            raise WorkerError(
                "ASE_UNAVAILABLE",
                "SevenNet relaxation requires ASE in the Python environment.",
                hint="Install the base Materials Lab Python requirements before installing optional SevenNet support.",
            )
        warnings.append("ASE is unavailable; returning a stub relaxation result.")
        summary_metrics = {"executed": False, "calculator": calculator_name, "reason": "ASE not installed"}
        stub_path = artifact_root / "relaxation-stub.json"
        stub_path.write_text(json.dumps(summary_metrics, indent=2) + "\n", encoding="utf-8")
        artifacts.append(str(stub_path))
        return summary_metrics, artifacts, warnings

    atoms = _atoms_from_structure_data(structure_data)
    species = atoms.get_chemical_symbols()

    if calculator_name == "EMT" and any(element not in SUPPORTED_EMT_ELEMENTS for element in species):
        warnings.append("Requested structure contains elements not supported by the EMT calculator; returning a stub result.")
        summary_metrics = {"executed": False, "calculator": calculator_name, "reason": "unsupported elements"}
        stub_path = artifact_root / "relaxation-stub.json"
        stub_path.write_text(json.dumps(summary_metrics, indent=2) + "\n", encoding="utf-8")
        artifacts.append(str(stub_path))
        return summary_metrics, artifacts, warnings

    if calculator_name == "EMT":
        atoms.calc = EMT()
        calculator_summary: dict[str, Any] = {"calculator": "EMT"}
    elif calculator_name == "SevenNet":
        model = seven_net_model or SEVENNET_DEFAULT_MODEL
        modal = seven_net_modal or SEVENNET_DEFAULT_MODAL
        resolved_device = device or SEVENNET_DEFAULT_DEVICE
        atoms.calc = _load_sevennet_calculator(model=model, modal=modal, device=resolved_device)
        calculator_summary = {
            "calculator": "SevenNet",
            "sevenNetModel": model,
            "sevenNetModal": modal,
            "device": resolved_device,
            "citationHint": SEVENNET_CITATION_HINT,
        }
    else:
        raise WorkerError(
            "UNSUPPORTED_CALCULATOR",
            f"Calculator '{calculator}' is not supported in v1.",
            hint="Use EMT or SevenNet.",
        )

    optimizer = BFGS(atoms, logfile=None)
    optimizer.run(fmax=fmax_ev_a, steps=steps)

    xyz_path = artifact_root / "relaxed.xyz"
    write(str(xyz_path), atoms)
    artifacts.append(str(xyz_path))

    summary_metrics = {
        "executed": True,
        **calculator_summary,
        "finalEnergyEv": float(atoms.get_potential_energy()),
        "maxForceEvA": _max_force(atoms.get_forces()),
        "numAtoms": len(atoms),
    }
    summary_path = artifact_root / "relaxation-summary.json"
    summary_path.write_text(json.dumps(summary_metrics, indent=2) + "\n", encoding="utf-8")
    artifacts.append(str(summary_path))
    return summary_metrics, artifacts, warnings


def _normalize_calculator(calculator: str) -> str:
    normalized = str(calculator or "EMT").strip().lower().replace("-", "").replace("_", "")
    if normalized == "emt":
        return "EMT"
    if normalized == "sevennet":
        return "SevenNet"
    return str(calculator).strip()


def _atoms_from_structure_data(structure_data: dict[str, Any]) -> Any:
    sites = structure_data.get("sites") or []
    lattice = structure_data.get("lattice")
    if isinstance(lattice, list) and isinstance(sites, list) and all(_is_simple_site(site) for site in sites):
        species = [site.get("element") for site in sites]
        positions = [site.get("coords") for site in sites]
        return Atoms(symbols=species, scaled_positions=positions, cell=lattice, pbc=True)

    try:
        from pymatgen.core import Structure  # type: ignore
        from pymatgen.io.ase import AseAtomsAdaptor  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional runtime package details
        raise WorkerError(
            "PYMATGEN_UNAVAILABLE",
            "ASE relaxation could not convert the structure payload without pymatgen.",
            hint="Install pymatgen or pass a simple structure payload with lattice and {element, coords} sites.",
            details={"importError": str(exc)},
        ) from exc

    try:
        structure = Structure.from_dict(structure_data)
        return AseAtomsAdaptor.get_atoms(structure)
    except Exception as exc:
        raise WorkerError(
            "INVALID_STRUCTURE",
            "ASE relaxation could not convert the structure payload into ASE Atoms.",
            hint="Use a fetched Materials Project structure artifact or a simple lattice/sites JSON structure.",
            details={"conversionError": str(exc)},
        ) from exc


def _is_simple_site(site: Any) -> bool:
    return isinstance(site, dict) and isinstance(site.get("element"), str) and isinstance(site.get("coords"), list)


def _load_sevennet_calculator(*, model: str, modal: str, device: str) -> Any:
    try:
        from sevenn.calculator import SevenNetCalculator  # type: ignore
    except Exception as exc:
        raise WorkerError(
            "SEVENNET_UNAVAILABLE",
            "SevenNet is not installed or cannot import its PyTorch runtime in this Python environment.",
            hint=(
                "Install a compatible PyTorch build, then install optional SevenNet support with "
                "`pip install -r python/requirements-sevennet.txt`."
            ),
            details={"importError": str(exc)},
        ) from exc

    try:
        return SevenNetCalculator(model=model, modal=modal, device=device)
    except Exception as exc:
        raise WorkerError(
            "SEVENNET_CALCULATOR_ERROR",
            "SevenNet calculator initialization failed.",
            hint="Check sevenNetModel, sevenNetModal, device, checkpoint availability, and PyTorch/CUDA compatibility.",
            details={"error": str(exc), "model": model, "modal": modal, "device": device},
        ) from exc


def _max_force(forces: Any) -> float:
    max_value = 0.0
    for vector in forces:
        magnitude = math.sqrt(sum(float(component) ** 2 for component in vector))
        max_value = max(max_value, magnitude)
    return float(max_value)
