---
title: "Live Materials Project perovskite solar screening process"
createdAt: 2026-05-03T06:20:15.133Z
noteType: "process"
tags: ["materials-project", "perovskite", "solar", "openclaw-e2e"]
candidateIds: ["mp-4514", "mp-27790", "mp-504457", "mp-1403610", "mp-5020", "mp-1218603", "mp-5477", "mp-5777"]
artifacts: ["/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/plots/live-candidate-ranking/candidate-ranking.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-4514/mp-4514.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-4514/mp-4514.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-4514/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-27790/mp-27790.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-27790/mp-27790.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-27790/structure-metrics.png", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-504457/mp-504457.json", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-504457/mp-504457.cif", "/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-504457/structure-metrics.png"]
---

Question: Which stable oxide perovskite-family candidates from Materials Project have band gaps near the target range for perovskite solar-material exploration?

Process:
1. Queried Materials Project live data for Sr-Ti-O, Ba-Ti-O, Ca-Ti-O, and Na-Nb-O oxide families with hull energy <= 0.05 eV and 1.0-4.2 eV band gaps.
2. Merged duplicate material ids across searches.
3. Ranked candidates using weighted stability, band-gap alignment, and density alignment.
4. Fetched structures for the top candidates and generated JSON/CIF artifacts.
5. Ran pymatgen-based structure analysis and generated metric plots.
6. Exported a markdown report with candidate ranking and artifact references.
