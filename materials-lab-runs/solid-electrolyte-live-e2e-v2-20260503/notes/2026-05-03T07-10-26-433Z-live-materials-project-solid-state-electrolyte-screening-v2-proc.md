---
title: "Live Materials Project solid-state electrolyte screening v2 process"
createdAt: 2026-05-03T07:10:26.431Z
noteType: "process"
tags: ["materials-project", "solid-electrolyte", "battery", "openclaw-e2e", "diversity", "proxy-screen"]
candidateIds: ["mp-985583", "mp-11175", "mp-760046", "mp-10499", "mp-1139957", "mp-567652", "mp-30301", "mp-766132", "mp-1223569", "mp-942733", "mp-769074", "mp-696138"]
artifacts: ["/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/plots/solid-electrolyte-ranking-v2/candidate-ranking.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/plots/solid-electrolyte-ranking-v2/candidate-ranking.csv", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/plots/solid-electrolyte-ranking-v2/candidate-ranking.jsonl", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-985583/mp-985583.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-985583/mp-985583.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-985583/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-11175/mp-11175.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-11175/mp-11175.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-11175/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-760046/mp-760046.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-760046/mp-760046.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-760046/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-10499/mp-10499.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-10499/mp-10499.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-10499/structure-metrics.png"]
---

Question: Can the patched Materials Lab solid-electrolyte preset produce a more defensible live proxy shortlist than the first E2E run?

Process:
1. Queried live Materials Project data across oxide, sulfide, halide, oxyhalide, NASICON-like, LGPS-like, and phosphate electrolyte families.
2. Disabled offline fallback in every live MP query and structure fetch.
3. Merged duplicate material ids across searches.
4. Ranked candidates with the new solid-electrolyte preset: stability gate, minimum band-gap screen, density advisory, and formula/family diversity controls.
5. Exported score component plot plus CSV/JSONL ranking tables.
6. Fetched JSON/CIF structures for diverse top candidates.
7. Ran pymatgen-based structure analysis with Li sublattice proxy descriptors and unit-aware metric plots.
8. Exported an enhanced markdown report plus a machine-readable validation summary.
