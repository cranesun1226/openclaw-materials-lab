---
title: "Live Materials Project solid-state electrolyte screening process"
createdAt: 2026-05-03T06:39:02.323Z
noteType: "process"
tags: ["materials-project", "solid-electrolyte", "battery", "openclaw-e2e"]
candidateIds: ["mp-759280", "mp-10499", "mp-773068", "mp-681439", "mp-541661", "mp-1223743", "mp-773074", "mp-1222872", "mp-942733", "mp-11175"]
artifacts: ["/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/plots/solid-electrolyte-ranking/candidate-ranking.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-759280/mp-759280.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-759280/mp-759280.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-759280/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-10499/mp-10499.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-10499/mp-10499.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-10499/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-773068/mp-773068.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-773068/mp-773068.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-773068/structure-metrics.png"]
---

Question: Which stable lithium-containing inorganic materials from Materials Project are promising proxy candidates for solid-state battery electrolyte exploration?

Process:
1. Queried Materials Project live data for garnet, thiophosphate, LGPS-like, NASICON-like, and phosphate electrolyte families.
2. Disabled offline fallback in every query and structure fetch.
3. Merged duplicate material ids across searches.
4. Ranked candidates using weighted stability, high band-gap alignment, and density alignment.
5. Fetched JSON/CIF structures for the top candidates that had retrievable structures.
6. Ran pymatgen-based structure analysis and generated metric plots.
7. Exported a markdown report plus a machine-readable validation summary.
