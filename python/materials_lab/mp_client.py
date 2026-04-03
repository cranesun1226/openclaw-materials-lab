from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from .schemas import WorkerError

try:
    from mp_api.client import MPRester  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    MPRester = None


MOCK_MATERIALS: list[dict[str, Any]] = [
    {
        "material_id": "mp-mock-si",
        "formula": "Si",
        "energy_above_hull_ev": 0.0,
        "band_gap_ev": 1.12,
        "density_gcm3": 2.33,
        "volume": 160.1,
        "sites": 8,
        "spacegroup": "Fd-3m",
        "elements": ["Si"],
        "source": "mock",
        "structure": {
            "formula": "Si",
            "lattice": [[5.43, 0.0, 0.0], [0.0, 5.43, 0.0], [0.0, 0.0, 5.43]],
            "sites": [
                {"element": "Si", "coords": [0.0, 0.0, 0.0]},
                {"element": "Si", "coords": [0.25, 0.25, 0.25]},
            ],
        },
    },
    {
        "material_id": "mp-mock-lifepo4",
        "formula": "LiFePO4",
        "energy_above_hull_ev": 0.0,
        "band_gap_ev": 3.8,
        "density_gcm3": 3.6,
        "volume": 291.0,
        "sites": 28,
        "spacegroup": "Pnma",
        "elements": ["Li", "Fe", "P", "O"],
        "source": "mock",
        "structure": {
            "formula": "LiFePO4",
            "lattice": [[10.33, 0.0, 0.0], [0.0, 6.01, 0.0], [0.0, 0.0, 4.69]],
            "sites": [
                {"element": "Li", "coords": [0.09, 0.25, 0.98]},
                {"element": "Fe", "coords": [0.28, 0.25, 0.47]},
                {"element": "P", "coords": [0.09, 0.25, 0.42]},
                {"element": "O", "coords": [0.16, 0.04, 0.28]},
            ],
        },
    },
    {
        "material_id": "mp-mock-srtio3",
        "formula": "SrTiO3",
        "energy_above_hull_ev": 0.012,
        "band_gap_ev": 3.25,
        "density_gcm3": 5.11,
        "volume": 59.5,
        "sites": 5,
        "spacegroup": "Pm-3m",
        "elements": ["Sr", "Ti", "O"],
        "source": "mock",
        "structure": {
            "formula": "SrTiO3",
            "lattice": [[3.905, 0.0, 0.0], [0.0, 3.905, 0.0], [0.0, 0.0, 3.905]],
            "sites": [
                {"element": "Sr", "coords": [0.0, 0.0, 0.0]},
                {"element": "Ti", "coords": [0.5, 0.5, 0.5]},
                {"element": "O", "coords": [0.5, 0.5, 0.0]},
            ],
        },
    },
    {
        "material_id": "mp-mock-al2o3",
        "formula": "Al2O3",
        "energy_above_hull_ev": 0.0,
        "band_gap_ev": 8.8,
        "density_gcm3": 3.95,
        "volume": 254.2,
        "sites": 30,
        "spacegroup": "R-3c",
        "elements": ["Al", "O"],
        "source": "mock",
        "structure": {
            "formula": "Al2O3",
            "lattice": [[4.76, 0.0, 0.0], [-2.38, 4.12, 0.0], [0.0, 0.0, 12.99]],
            "sites": [
                {"element": "Al", "coords": [0.35, 0.0, 0.25]},
                {"element": "O", "coords": [0.31, 0.0, 0.056]},
            ],
        },
    },
    {
        "material_id": "mp-mock-hfo2",
        "formula": "HfO2",
        "energy_above_hull_ev": 0.0,
        "band_gap_ev": 5.7,
        "density_gcm3": 9.68,
        "volume": 138.4,
        "sites": 12,
        "spacegroup": "P21/c",
        "elements": ["Hf", "O"],
        "source": "mock",
        "structure": {
            "formula": "HfO2",
            "lattice": [[5.12, 0.0, 0.0], [0.0, 5.17, 0.0], [0.0, 0.0, 5.29]],
            "sites": [
                {"element": "Hf", "coords": [0.28, 0.04, 0.21]},
                {"element": "O", "coords": [0.07, 0.33, 0.35]},
            ],
        },
    },
]


def search_materials(payload: dict[str, Any], *, api_key: str | None) -> tuple[list[dict[str, Any]], bool]:
    allow_offline = bool(payload.get("allowOffline", True))
    if api_key and MPRester is not None:
        try:
            return _live_search(payload, api_key), False
        except Exception as exc:  # pragma: no cover - network dependent
            if not allow_offline:
                raise WorkerError(
                    "MATERIALS_PROJECT_SEARCH_FAILED",
                    f"Materials Project search failed: {exc}",
                    hint="Check mpApiKey and network access, or rerun with allowOffline=true.",
                ) from exc

    if not allow_offline:
        raise WorkerError(
            "OFFLINE_NOT_ALLOWED",
            "Materials Project access is unavailable and offline mode was disabled.",
            hint="Configure mpApiKey or set allowOffline to true.",
        )

    results = [deepcopy(item) for item in MOCK_MATERIALS]
    filtered = _apply_filters(results, payload)
    limit = int(payload.get("limit") or 10)
    return filtered[:limit], True


def fetch_material(material_id: str, *, api_key: str | None, allow_offline: bool = True) -> tuple[dict[str, Any], bool]:
    if api_key and MPRester is not None:
        try:
            return _live_fetch(material_id, api_key), False
        except Exception as exc:  # pragma: no cover - network dependent
            if not allow_offline:
                raise WorkerError(
                    "MATERIALS_PROJECT_FETCH_FAILED",
                    f"Materials Project structure fetch failed: {exc}",
                    hint="Check mpApiKey and network access, or rerun with allowOffline=true.",
                ) from exc

    for material in MOCK_MATERIALS:
        if material["material_id"] == material_id:
            return deepcopy(material), True

    raise WorkerError(
        "MATERIAL_NOT_FOUND",
        f"Material '{material_id}' was not found in the available dataset.",
        hint="Search candidates first or enable live Materials Project access.",
    )


def _apply_filters(items: list[dict[str, Any]], payload: dict[str, Any]) -> list[dict[str, Any]]:
    text_query = str(payload.get("textQuery") or "").strip().lower()
    formula = str(payload.get("formula") or "").strip().lower()
    elements_all = [str(item).strip() for item in payload.get("elementsAll") or []]
    elements_any = [str(item).strip() for item in payload.get("elementsAny") or []]
    max_energy = payload.get("maxEnergyAboveHullEv")
    min_gap = payload.get("minBandGapEv")
    max_gap = payload.get("maxBandGapEv")

    def include(item: dict[str, Any]) -> bool:
        searchable = " ".join([item["material_id"], item["formula"], *item.get("elements", [])]).lower()
        if text_query and text_query not in searchable:
            return False
        if formula and formula not in item["formula"].lower():
            return False
        if elements_all and not set(elements_all).issubset(set(item.get("elements", []))):
            return False
        if elements_any and not set(elements_any).intersection(set(item.get("elements", []))):
            return False
        if max_energy is not None and item.get("energy_above_hull_ev", math.inf) > float(max_energy):
            return False
        if min_gap is not None and item.get("band_gap_ev", -math.inf) < float(min_gap):
            return False
        if max_gap is not None and item.get("band_gap_ev", math.inf) > float(max_gap):
            return False
        return True

    return [item for item in items if include(item)]


def _live_search(payload: dict[str, Any], api_key: str) -> list[dict[str, Any]]:
    if MPRester is None:  # pragma: no cover - import guarded above
        raise RuntimeError("mp-api is not installed in this Python environment.")

    fields = [
        "material_id",
        "formula_pretty",
        "energy_above_hull",
        "band_gap",
        "density",
        "volume",
        "nsites",
        "symmetry",
        "elements",
    ]
    with MPRester(api_key) as mpr:  # pragma: no cover - network dependent
        docs = mpr.materials.summary.search(
            formula=payload.get("formula") or None,
            elements=payload.get("elementsAll") or payload.get("elementsAny") or None,
            band_gap=_range_tuple(payload.get("minBandGapEv"), payload.get("maxBandGapEv")),
            energy_above_hull=(0.0, payload.get("maxEnergyAboveHullEv")) if payload.get("maxEnergyAboveHullEv") is not None else None,
            fields=fields,
            chunk_size=int(payload.get("limit") or 10),
            num_chunks=1,
        )
        return [_summary_from_mp_doc(doc) for doc in docs]


def _live_fetch(material_id: str, api_key: str) -> dict[str, Any]:
    if MPRester is None:  # pragma: no cover - import guarded above
        raise RuntimeError("mp-api is not installed in this Python environment.")

    with MPRester(api_key) as mpr:  # pragma: no cover - network dependent
        summary_docs = mpr.materials.summary.search(material_ids=[material_id], fields=["material_id", "formula_pretty", "energy_above_hull", "band_gap", "density", "volume", "nsites", "symmetry", "elements"])
        if not summary_docs:
            raise WorkerError("MATERIAL_NOT_FOUND", f"Material '{material_id}' was not found in Materials Project.")
        structure_doc = mpr.materials.search(material_ids=[material_id], fields=["material_id", "structure"])
        summary = _summary_from_mp_doc(summary_docs[0])
        structure = structure_doc[0].structure.as_dict() if structure_doc else None
        summary["structure"] = structure
        return summary


def _summary_from_mp_doc(doc: Any) -> dict[str, Any]:
    symmetry = getattr(doc, "symmetry", None)
    spacegroup = getattr(symmetry, "symbol", None) if symmetry is not None else None
    elements = [str(item) for item in getattr(doc, "elements", [])]
    return {
        "material_id": str(getattr(doc, "material_id")),
        "formula": str(getattr(doc, "formula_pretty")),
        "energy_above_hull_ev": _safe_float(getattr(doc, "energy_above_hull", None)),
        "band_gap_ev": _safe_float(getattr(doc, "band_gap", None)),
        "density_gcm3": _safe_float(getattr(doc, "density", None)),
        "volume": _safe_float(getattr(doc, "volume", None)),
        "sites": int(getattr(doc, "nsites", 0) or 0),
        "spacegroup": spacegroup,
        "elements": elements,
        "source": "materials-project",
    }


def _range_tuple(lower: Any, upper: Any) -> tuple[float | None, float | None] | None:
    if lower is None and upper is None:
        return None
    return (_safe_float(lower), _safe_float(upper))


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None
