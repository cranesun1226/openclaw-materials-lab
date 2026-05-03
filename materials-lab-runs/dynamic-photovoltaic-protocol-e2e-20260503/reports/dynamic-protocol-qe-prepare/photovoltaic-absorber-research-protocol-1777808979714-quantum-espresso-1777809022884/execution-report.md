# Research Backend Preparation: Quantum ESPRESSO

## Summary

- Backend: `quantum-espresso`
- Execution mode: `prepare`
- Allow blocked steps: `False`
- Prepared calculations: 7
- Submitted calculations: 0
- Skipped calculations: 7
- Parsed property updates: `0`

## Prepared Steps

| Calculation | Material | Type | Inputs |
| --- | --- | --- | ---: |
| fixture-si-structure-preflight | fixture-si | structure-preflight | 4 |
| fixture-si-phase-stability | fixture-si | phase-stability | 6 |
| fixture-si-structure-validity | fixture-si | structure-validity | 6 |
| fixture-si-optical-absorption | fixture-si | optical-absorption | 6 |
| fixture-si-defect-transport | fixture-si | defect-transport | 6 |
| fixture-si-reproducibility | fixture-si | reproducibility | 6 |
| fixture-lifepo4-structure-preflight | fixture-lifepo4 | structure-preflight | 4 |

## Notes

- This adapter prepares reproducible backend inputs and optional submission scripts.
- It does not mark candidates as property-backed until completed outputs are parsed into propertyUpdates.
- Review pseudopotentials, k-points, cutoffs, scheduler resources, and code licenses before submission.

## Warnings

- No warnings.
