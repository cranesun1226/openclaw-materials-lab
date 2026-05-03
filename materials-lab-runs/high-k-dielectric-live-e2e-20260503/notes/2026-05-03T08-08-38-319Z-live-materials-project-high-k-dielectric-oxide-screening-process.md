---
title: "Live Materials Project high-k dielectric oxide screening process"
createdAt: 2026-05-03T08:08:38.317Z
noteType: "process"
tags: ["materials-project", "dielectric", "high-k", "oxide", "openclaw-e2e"]
candidateIds: ["mp-1143", "mp-2652", "mp-733790", "mp-1968", "mp-2858", "mp-5020", "mp-352", "mp-1439", "mp-1238961"]
artifacts: ["/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/candidate-ranking.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/domain-evidence.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/candidate-ranking.csv", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/candidate-ranking.jsonl", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1143/mp-1143.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1143/mp-1143.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1143/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-2652/mp-2652.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-2652/mp-2652.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-2652/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-733790/mp-733790.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-733790/mp-733790.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-733790/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1968/mp-1968.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1968/mp-1968.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1968/structure-metrics.png"]
---

Question: Which stable wide-bandgap oxide candidates are worth shortlisting as high-k dielectric proxy candidates?

Process:
1. Queried live Materials Project formula families for common high-k/wide-bandgap oxides.
2. Disabled offline fallback in every query and structure fetch.
3. Ranked candidates with a generic proxy score emphasizing stability, wide band gap near 5.5 eV, and density near 6.0 g/cm3.
4. Enforced formula diversity to avoid repeated polymorph domination.
5. Exported ranking PNG plus CSV/JSONL table artifacts.
6. Fetched JSON/CIF structures for top ranked candidates and generated unit-aware metric plots.
7. Exported an enhanced markdown report and machine-readable validation summary.
