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
| mp-21713-structure-preflight | mp-21713 | structure-preflight | 4 |
| mp-21713-phase-stability | mp-21713 | phase-stability | 6 |
| mp-21713-structure-validity | mp-21713 | structure-validity | 6 |
| mp-21713-optical-absorption | mp-21713 | optical-absorption | 6 |
| mp-21713-defect-transport | mp-21713 | defect-transport | 6 |
| mp-21713-reproducibility | mp-21713 | reproducibility | 6 |
| mp-1224609-structure-preflight | mp-1224609 | structure-preflight | 4 |

## Notes

- This adapter prepares reproducible backend inputs and optional submission scripts.
- It does not mark candidates as property-backed until completed outputs are parsed into propertyUpdates.
- Review pseudopotentials, k-points, cutoffs, scheduler resources, and code licenses before submission.

## Warnings

- No warnings.
