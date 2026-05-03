---
name: material-science-research
description: Run a careful materials-science research workflow using the Materials Lab plugin tools.
---

# Material Science Research

Use this workflow when the user wants to explore candidate materials, inspect structures, compare options, document findings, and export a report.

## Goals

- Restate the research goal in concrete terms before acting.
- Define evaluation criteria before ranking candidates.
- Compile an evidence schema before presenting any research-grade claim.
- Use structured tool outputs instead of making unsupported claims.
- Save intermediate notes so the work is reproducible.
- Export a final report when the user wants a durable summary.
- Ask for approval before expensive workflows such as ASE relaxation or batch screening.

## Workflow

### 1. Clarify the goal

- Restate the requested use case in one or two sentences.
- Identify key target properties such as stability, band gap, density, chemistry constraints, or cost proxies.
- If the goal is vague, narrow it with explicit assumptions and state them clearly.

Reference prompt: `prompts/goal_refinement.md`

### 2. Compile the research protocol

Use `materials_plan_research_loop` when the user asks for an open-ended research campaign, when candidates are not known yet, or when a ranked list needs property-backed validation.

- Pass `researchGoal`, `targetApplication`, constraints, candidate-generation hints, literature/database queries, and explicit evidence requirements when available.
- If only the topic is known, pass `researchGoal` and let the bounded autonomous discovery compiler create the database query log, candidate-pool JSONL, evidence-ledger JSONL, and candidate-backed protocol.
- Use `candidateGeneration.allowDevelopmentFixtures: true` only for smoke tests; live research should use Materials Project or other database evidence.
- Treat the output as an evidence contract: candidate generation, literature review, database search, validation matrix, claim policy, and approval gates.
- Do not present research-grade discovery claims unless the compiled claim policy is satisfied by parsed evidence artifacts.

### 3. Define evaluation criteria

Before searching, write down the criteria you will use to compare candidates. Common criteria:

- thermodynamic stability,
- band gap or metallic behavior,
- density or volumetric constraints,
- elemental composition constraints,
- structural simplicity,
- synthesis or literature familiarity if relevant.

Do not imply the ranking is objective. Explain that rankings depend on the chosen criteria and available evidence.

### 4. Search candidates

Use `materials_search_mp` to find candidate materials.

- Start broad enough to avoid premature narrowing.
- Prefer a manageable first pass, then refine.
- If Materials Project access is unavailable, do not silently continue with fixture data. Use development fixture data only when the user explicitly wants a smoke test.

### 5. Inspect structures

Use `materials_fetch_structure` to retrieve promising structures and save local artifacts.

- Fetch the top candidates you intend to analyze, not every result.
- Keep track of artifact paths so later notes and reports can reference them.

Use `materials_analyze_structure` to derive structural metrics and a readable summary.

- Note the limits of the analysis.
- Do not overclaim coordination or property interpretation if the evidence is weak.

### 6. Compare and rank

Use `materials_compare_candidates` with explicit criteria and explain the tradeoffs.

- Mention when one candidate is more stable but less aligned with another target metric.
- Prefer ranked shortlists over single-candidate certainty.

### 7. Save notes as you go

Use `materials_save_note` for:

- assumptions,
- observations,
- failed paths,
- candidate rationales,
- open questions,
- next-step plans.

Document weak evidence and dead ends instead of quietly dropping them.

### 8. Export a final report

Use `materials_export_report` when the user wants a durable artifact.

The report should include:

- goal,
- evaluation criteria,
- candidate summaries,
- ranking rationale,
- assumptions and limitations,
- generated artifacts and references,
- recommended next steps.

Reference prompt: `prompts/report_template.md`

### 9. Approval policy

Always request approval before:

- `materials_ase_relax`
- `materials_batch_screen`

These workflows can be slow, write multiple artifacts, or trigger heavier local computation.

## Working Style

- Prefer clarity over jargon when the user does not ask for deep technical detail.
- If data is incomplete, say so plainly.
- Separate observed outputs from interpretation.
- Keep the user informed about what is live data, local analysis, or explicitly requested development fixture fallback.
