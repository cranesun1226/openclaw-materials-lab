---
title: "Perovskite solar materials exploration process note"
createdAt: 2026-05-03T05:34:53.057Z
noteType: "observation"
tags: ["perovskite", "solar", "offline-demo", "openclaw"]
candidateIds: ["mp-mock-si", "mp-mock-lifepo4", "mp-mock-srtio3"]
artifacts: ["/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-demo-20260503/structures/mp-mock-srtio3/mp-mock-srtio3.json"]
---

## Question

Can we identify a stable perovskite or perovskite-adjacent solar absorber candidate with a band gap near 1.1-2.2 eV using the current Materials Lab OpenClaw plugin?

## Process

1. Tried a halide perovskite style query: Pb + I, band gap 1.0-2.2 eV, hull energy <= 0.1 eV.
2. Because no Materials Project API key was configured, the plugin used offline/mock mode. The halide query returned 0 candidates.
3. Broadened to an oxide perovskite fallback query around SrTiO3.
4. Added stable absorber-window mock candidates with band gap 1.0-4.0 eV and hull energy <= 0.05 eV.
5. Compared candidates with stability weight 0.45, band-gap weight 0.45, density weight 0.1, target band gap 1.5 eV.
6. Fetched and analyzed the SrTiO3 mock structure as the perovskite reference point.

## Main Finding

The offline dataset did not contain a true Pb/Sn halide perovskite solar absorber. In this limited demo set, Si ranks highest for absorber-like band-gap alignment, while SrTiO3 is the perovskite-structured reference but has a wide band gap and is better treated as a perovskite oxide reference than as a primary photovoltaic absorber.
