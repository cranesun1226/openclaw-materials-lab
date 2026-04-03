from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .schemas import WorkerError

try:
    from pymatgen.core import Lattice, Structure  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    Lattice = None
    Structure = None


def load_structure(*, structure_path: str | None = None, structure_data: dict[str, Any] | None = None) -> tuple[Any | None, dict[str, Any]]:
    payload = structure_data
    if structure_path:
        file_path = Path(structure_path)
        if not file_path.exists():
            raise WorkerError("STRUCTURE_NOT_FOUND", f"Structure file '{structure_path}' does not exist.")
        if file_path.suffix.lower() == ".json":
            payload = json.loads(file_path.read_text("utf-8"))
        elif Structure is not None:
            structure = Structure.from_file(str(file_path))
            return structure, structure.as_dict()
        else:
            raise WorkerError(
                "UNSUPPORTED_STRUCTURE_FORMAT",
                f"Cannot load '{structure_path}' without pymatgen.",
                hint="Use a JSON structure artifact or install pymatgen in the worker environment.",
            )

    if payload is None:
        raise WorkerError("INVALID_PARAMS", "A structure payload or structurePath is required.")

    if Structure is not None and isinstance(payload, dict) and "lattice" in payload and "sites" in payload:
        structure = _structure_from_simple_payload(payload)
        return structure, payload

    return None, payload


def analyze_structure(*, structure_path: str | None = None, structure_data: dict[str, Any] | None = None) -> dict[str, Any]:
    structure, payload = load_structure(structure_path=structure_path, structure_data=structure_data)

    if structure is not None:
        formula = structure.composition.reduced_formula
        metrics = {
            "formula": formula,
            "numSites": int(structure.num_sites),
            "volume": round(float(structure.volume), 4),
            "densityGcm3": round(float(structure.density), 4),
            "a": round(float(structure.lattice.a), 4),
            "b": round(float(structure.lattice.b), 4),
            "c": round(float(structure.lattice.c), 4),
            "alpha": round(float(structure.lattice.alpha), 3),
            "beta": round(float(structure.lattice.beta), 3),
            "gamma": round(float(structure.lattice.gamma), 3),
            "numElements": len(structure.composition.elements),
        }
        summary = (
            f"{formula} has {metrics['numSites']} sites, volume {metrics['volume']} A^3, "
            f"density {metrics['densityGcm3']} g/cm^3, and {metrics['numElements']} distinct elements."
        )
        return {"summaryMetrics": metrics, "readableSummary": summary}

    lattice = payload.get("lattice") or []
    sites = payload.get("sites") or []
    formula = payload.get("formula") or "unknown"
    lengths = [_vector_length(vector) for vector in lattice[:3]]
    volume = _triple_product(lattice) if len(lattice) >= 3 else None
    unique_elements = sorted({site.get("element", "?") for site in sites if isinstance(site, dict)})
    metrics = {
        "formula": formula,
        "numSites": len(sites),
        "volume": round(volume, 4) if volume is not None else None,
        "a": round(lengths[0], 4) if len(lengths) > 0 else None,
        "b": round(lengths[1], 4) if len(lengths) > 1 else None,
        "c": round(lengths[2], 4) if len(lengths) > 2 else None,
        "numElements": len(unique_elements),
    }
    summary = f"{formula} fallback analysis found {len(sites)} listed sites and elements {', '.join(unique_elements) or 'unknown'}."
    return {"summaryMetrics": metrics, "readableSummary": summary}


def write_structure_json(structure_data: dict[str, Any], output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(structure_data, indent=2) + "\n", encoding="utf-8")
    return str(path)


def write_cif(structure_data: dict[str, Any], output_path: str) -> str | None:
    structure = None
    if Structure is not None:
        try:
            structure = _structure_from_simple_payload(structure_data)
        except Exception:
            if isinstance(structure_data, dict) and "@module" in structure_data:
                structure = Structure.from_dict(structure_data)

    if structure is None:
        return None

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    structure.to(fmt="cif", filename=str(path))
    return str(path)


def _structure_from_simple_payload(payload: dict[str, Any]) -> Any:
    if Structure is None or Lattice is None:
        raise WorkerError("PYMATGEN_UNAVAILABLE", "pymatgen is not installed in this Python environment.")

    lattice = payload.get("lattice")
    sites = payload.get("sites")
    if not isinstance(lattice, list) or not isinstance(sites, list):
        raise WorkerError("INVALID_STRUCTURE", "Structure payload must contain lattice and sites arrays.")
    species = [site["element"] for site in sites]
    coords = [site["coords"] for site in sites]
    return Structure(Lattice(lattice), species, coords)


def _vector_length(vector: Any) -> float:
    return math.sqrt(sum(float(component) ** 2 for component in vector))


def _triple_product(lattice: list[list[float]]) -> float:
    a, b, c = lattice[:3]
    return abs(
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )
