---
title: "Live Materials Project solid-state electrolyte screening v2 process"
createdAt: 2026-05-26T11:06:21.644Z
noteType: "process"
tags: ["materials-project", "solid-electrolyte", "battery", "openclaw-e2e", "diversity", "proxy-screen"]
candidateIds: ["mp-556886", "mp-554203", "mp-567652", "mp-11175", "mp-985583", "mp-950995", "mp-942733", "mp-766132", "mp-10499", "mp-1223569", "mp-696138", "mp-769074"]
artifacts: ["/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/plots/solid-electrolyte-ranking-v2/candidate-ranking.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/plots/solid-electrolyte-ranking-v2/domain-evidence.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/plots/solid-electrolyte-ranking-v2/candidate-ranking.csv", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/plots/solid-electrolyte-ranking-v2/candidate-ranking.jsonl", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-556886/mp-556886.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-556886/mp-556886.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-556886/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-11175/mp-11175.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-11175/mp-11175.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-11175/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-942733/mp-942733.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-942733/mp-942733.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-942733/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-766132/mp-766132.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-766132/mp-766132.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-poster-live-20260526-200337/structures/mp-766132/structure-metrics.png"]
---

Question: Can the patched Materials Lab solid-electrolyte preset produce a more defensible live proxy shortlist than the first E2E run?

Process:
1. Queried live Materials Project data across oxide, sulfide, halide, oxyhalide, NASICON-like, LGPS-like, and phosphate electrolyte families.
2. Disabled offline fallback in every live MP query and structure fetch.
3. Merged duplicate material ids across searches.
4. Ranked candidates with the new solid-electrolyte preset: stability gate, minimum band-gap screen, density advisory, and formula/family diversity controls.
5. Applied chemistry risk filters and secondary tie-breaker scoring to reduce score saturation.
6. Exported score component plot plus CSV/JSONL ranking tables.
7. Fetched JSON/CIF structures with family-balanced candidate selection.
8. Ran pymatgen-based structure analysis with Li sublattice proxy descriptors and unit-aware metric plots.
9. Exported an enhanced markdown report plus a machine-readable validation summary.
