from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))

from materials_lab import ase_ops
from materials_lab.schemas import WorkerError


SIMPLE_STRUCTURE = {
    "formula": "Cu",
    "lattice": [[3.6, 0.0, 0.0], [0.0, 3.6, 0.0], [0.0, 0.0, 3.6]],
    "sites": [{"element": "Cu", "coords": [0.0, 0.0, 0.0]}],
}


class FakeAtoms:
    def __init__(self, *, symbols, scaled_positions, cell, pbc):
        self.symbols = symbols
        self.scaled_positions = scaled_positions
        self.cell = cell
        self.pbc = pbc
        self.calc = None

    def get_chemical_symbols(self):
        return self.symbols

    def get_potential_energy(self):
        return -1.25

    def get_forces(self):
        return [[0.01, 0.0, 0.0]]

    def __len__(self):
        return len(self.symbols)


class FakeBFGS:
    def __init__(self, atoms, logfile=None):
        self.atoms = atoms
        self.logfile = logfile

    def run(self, *, fmax, steps):
        self.atoms.relaxation_run = {"fmax": fmax, "steps": steps}


class FakeEMT:
    pass


def fake_write(path, atoms):
    Path(path).write_text("fake xyz\n", encoding="utf-8")


class AseOpsSevenNetTest(unittest.TestCase):
    def test_emt_regression_still_writes_summary_and_relaxed_structure(self):
        with TemporaryDirectory() as temp_dir, self._fake_ase_runtime():
            summary, artifacts, warnings = ase_ops.run_relaxation(
                structure_data=SIMPLE_STRUCTURE,
                artifact_dir=temp_dir,
                calculator="EMT",
                steps=4,
                fmax_ev_a=0.04,
            )

            self.assertEqual(warnings, [])
            self.assertEqual(summary["calculator"], "EMT")
            self.assertEqual(summary["finalEnergyEv"], -1.25)
            self.assertTrue(any(path.endswith("relaxed.xyz") for path in artifacts))
            summary_path = Path(temp_dir) / "relaxation-summary.json"
            self.assertEqual(json.loads(summary_path.read_text("utf-8"))["calculator"], "EMT")

    def test_missing_sevennet_reports_clear_worker_error(self):
        with TemporaryDirectory() as temp_dir, self._fake_ase_runtime():
            with patch.dict(sys.modules, {"sevenn": None, "sevenn.calculator": None}):
                with self.assertRaises(WorkerError) as raised:
                    ase_ops.run_relaxation(
                        structure_data=SIMPLE_STRUCTURE,
                        artifact_dir=temp_dir,
                        calculator="SevenNet",
                    )

        self.assertEqual(raised.exception.code, "SEVENNET_UNAVAILABLE")
        self.assertIn("requirements-sevennet.txt", raised.exception.hint or "")

    def test_sevennet_calculator_receives_model_modal_and_device(self):
        class FakeSevenNetCalculator:
            last_kwargs = None

            def __init__(self, **kwargs):
                FakeSevenNetCalculator.last_kwargs = kwargs

        sevenn_module = types.ModuleType("sevenn")
        calculator_module = types.ModuleType("sevenn.calculator")
        calculator_module.SevenNetCalculator = FakeSevenNetCalculator

        with TemporaryDirectory() as temp_dir, self._fake_ase_runtime():
            with patch.dict(sys.modules, {"sevenn": sevenn_module, "sevenn.calculator": calculator_module}):
                summary, artifacts, warnings = ase_ops.run_relaxation(
                    structure_data=SIMPLE_STRUCTURE,
                    artifact_dir=temp_dir,
                    calculator="SevenNet",
                    seven_net_model="custom-checkpoint.pt",
                    seven_net_modal="mpa",
                    device="cpu",
                )

        self.assertEqual(warnings, [])
        self.assertEqual(FakeSevenNetCalculator.last_kwargs, {
            "model": "custom-checkpoint.pt",
            "modal": "mpa",
            "device": "cpu",
        })
        self.assertEqual(summary["calculator"], "SevenNet")
        self.assertEqual(summary["sevenNetModel"], "custom-checkpoint.pt")
        self.assertEqual(summary["sevenNetModal"], "mpa")
        self.assertEqual(summary["device"], "cpu")
        self.assertIn("citationHint", summary)
        self.assertTrue(any(path.endswith("relaxation-summary.json") for path in artifacts))

    def _fake_ase_runtime(self):
        return patch.multiple(
            ase_ops,
            Atoms=FakeAtoms,
            BFGS=FakeBFGS,
            EMT=FakeEMT,
            write=fake_write,
        )


if __name__ == "__main__":
    unittest.main()
