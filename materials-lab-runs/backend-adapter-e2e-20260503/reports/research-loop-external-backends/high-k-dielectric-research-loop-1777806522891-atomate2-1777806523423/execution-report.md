# Research Backend Preparation: atomate2/jobflow

## Summary

- Backend: `atomate2`
- Execution mode: `prepare`
- Allow blocked steps: `False`
- Prepared calculations: 3
- Submitted calculations: 0
- Skipped calculations: 0
- Parsed property updates: `0`

## Prepared Steps

| Calculation | Material | Type | Inputs |
| --- | --- | --- | ---: |
| mp-mock-hfo2-structure-preflight | mp-mock-hfo2 | structure-preflight | 2 |
| mp-mock-hfo2-dfpt-dielectric-tensor | mp-mock-hfo2 | dfpt-dielectric-tensor | 3 |
| mp-mock-hfo2-band-alignment | mp-mock-hfo2 | band-alignment | 3 |

## Notes

- This adapter prepares reproducible backend inputs and optional submission scripts.
- It does not mark candidates as property-backed until completed outputs are parsed into propertyUpdates.
- Review pseudopotentials, k-points, cutoffs, scheduler resources, and code licenses before submission.

## Warnings

- No warnings.
