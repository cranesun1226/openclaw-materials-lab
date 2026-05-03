# Research Backend Preparation: Quantum ESPRESSO

## Summary

- Backend: `quantum-espresso`
- Execution mode: `prepare`
- Allow blocked steps: `False`
- Prepared calculations: 7
- Submitted calculations: 0
- Skipped calculations: 9
- Parsed property updates: `0`

## Prepared Steps

| Calculation | Material | Type | Inputs |
| --- | --- | --- | ---: |
| mp-675030-structure-preflight | mp-675030 | structure-preflight | 4 |
| mp-675030-phase-stability | mp-675030 | phase-stability | 6 |
| mp-675030-structure-validity | mp-675030 | structure-validity | 6 |
| mp-675030-surface-activity | mp-675030 | surface-activity | 6 |
| mp-675030-operando-stability | mp-675030 | operando-stability | 6 |
| mp-675030-reproducibility | mp-675030 | reproducibility | 6 |
| mp-690546-structure-preflight | mp-690546 | structure-preflight | 4 |

## Notes

- This adapter prepares reproducible backend inputs and optional submission scripts.
- It does not mark candidates as property-backed until completed outputs are parsed into propertyUpdates.
- Review pseudopotentials, k-points, cutoffs, scheduler resources, and code licenses before submission.

## Warnings

- No warnings.
