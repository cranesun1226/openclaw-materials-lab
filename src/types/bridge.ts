export type BridgeAction =
  | "ping"
  | "search_materials"
  | "fetch_structure"
  | "analyze_structure"
  | "compare_candidates"
  | "plan_research_loop"
  | "search_literature"
  | "ingest_evidence"
  | "evaluate_research_claim"
  | "close_evidence_gaps"
  | "execute_research_plan"
  | "ase_relax"
  | "batch_screen"
  | "export_report";

export interface BridgeErrorDetails {
  code: string;
  message: string;
  hint?: string;
  retriable?: boolean;
  details?: unknown;
  stderr?: string;
}

export interface BridgeRequest<TPayload = Record<string, unknown>> {
  action: BridgeAction;
  requestId: string;
  payload: TPayload;
}

export interface BridgeSuccess<TData = unknown> {
  ok: true;
  action: BridgeAction;
  requestId: string;
  summary: string;
  data: TData;
  artifacts?: string[];
  warnings?: string[];
}

export interface BridgeFailure {
  ok: false;
  action?: BridgeAction;
  requestId?: string;
  error: BridgeErrorDetails;
}

export type BridgeResponse<TData = unknown> = BridgeSuccess<TData> | BridgeFailure;

export interface CandidateSummary {
  materialId: string;
  formula: string;
  energyAboveHullEv?: number;
  bandGapEv?: number;
  densityGcm3?: number;
  volume?: number;
  sites?: number;
  spacegroup?: string;
  elements?: string[];
  source: "materials-project" | "dev-fixture";
  notes?: string[];
  materialsProjectUrl?: string;
  family?: string;
  duplicateGroup?: string;
  duplicateCount?: number;
  warnings?: string[];
  screeningLevel?: string;
  riskProfile?: Record<string, unknown>;
  compositionDescriptors?: Record<string, unknown>;
  dielectricTotal?: number;
  dielectricElectronic?: number;
  bandOffsetElectronEv?: number;
  bandOffsetHoleEv?: number;
  interfaceReactionEnergyEv?: number;
  ionicConductivityScm?: number;
  migrationBarrierEv?: number;
  electrochemicalWindowV?: number;
  absorptionCoefficientCm1?: number;
  directBandGapEv?: number;
  effectiveMassElectron?: number;
  effectiveMassHole?: number;
  seebeckUvK?: number;
  powerFactorUwCmK2?: number;
  latticeThermalConductivityWmK?: number;
  carrierConcentrationCm3?: number;
  phononStability?: number;
  cbmEv?: number;
  vbmEv?: number;
  defectToleranceScore?: number;
  structureQuality?: number;
  propertyProvenance?: Record<string, unknown>;
  calculationStatus?: Record<string, unknown>;
}

export interface SearchMaterialsPayload {
  textQuery?: string;
  formula?: string;
  elementsAll?: string[];
  elementsAny?: string[];
  maxEnergyAboveHullEv?: number;
  minBandGapEv?: number;
  maxBandGapEv?: number;
  limit?: number;
  allowOffline?: boolean;
}

export interface SearchMaterialsResult {
  candidates: CandidateSummary[];
  usedOfflineData: boolean;
  usedDevelopmentFixtureData?: boolean;
}

export interface FetchStructurePayload {
  materialId: string;
  format?: "json" | "cif" | "both";
  artifactDir: string;
  allowOffline?: boolean;
}

export interface FetchStructureResult {
  material: CandidateSummary;
  structurePath?: string;
  cifPath?: string;
  structure?: Record<string, unknown>;
  usedOfflineData: boolean;
  usedDevelopmentFixtureData?: boolean;
}

export interface AnalyzeStructurePayload {
  materialId?: string;
  structurePath?: string;
  structure?: Record<string, unknown>;
  artifactDir: string;
  allowOffline?: boolean;
}

export interface AnalyzeStructureResult {
  materialId?: string;
  formula?: string;
  summaryMetrics: Record<string, number | string | boolean | null>;
  readableSummary: string;
  plotPath?: string;
  usedOfflineData: boolean;
  usedDevelopmentFixtureData?: boolean;
}

export interface CompareCriteria {
  preset?: "generic" | "solid-electrolyte" | "high-k-dielectric" | "photovoltaic-absorber" | "thermoelectric";
  screeningLevel?: "technical-smoke" | "proxy-screen" | "property-backed-screen" | "research-shortlist" | "closed-loop-plan" | "validated-candidate";
  stabilityWeight?: number;
  bandGapWeight?: number;
  densityWeight?: number;
  bandGapScoringMode?: "target" | "minimum";
  minimumBandGapEv?: number;
  bandGapTargetEv?: number;
  densityScoringMode?: "target" | "advisory" | "none";
  densityTargetGcm3?: number;
  secondaryWeight?: number;
  evidenceWeight?: number;
  riskPenaltyWeight?: number;
  preferredBandGapEv?: number;
  preferredLiFractionMin?: number;
  preferredLiFractionMax?: number;
  excludeToxicElements?: boolean;
  excludeRiskyChemistry?: boolean;
  filterMolecularSalts?: boolean;
  requiresLithium?: boolean;
  excludedElements?: string[];
  flaggedElements?: string[];
  maxHydrogenAtomicFraction?: number;
  diversifyBy?: "none" | "formula" | "family" | "formula-and-family";
  maxPerFormula?: number;
  maxPerFamily?: number;
}

export interface CompareCandidatesPayload {
  candidates: CandidateSummary[];
  criteria?: CompareCriteria;
  artifactDir: string;
  topK?: number;
}

export interface ComparedCandidate extends CandidateSummary {
  score: number;
  primaryScore?: number;
  secondaryScore?: number;
  domainEvidenceScore?: number;
  riskPenalty?: number;
  domainEvidence?: Record<string, unknown>;
  rawRank?: number;
  reasons: string[];
  rank: number;
  scoreComponents?: {
    raw?: Record<string, number>;
    weighted?: Record<string, number>;
    secondary?: Record<string, number>;
    domainEvidence?: Record<string, number>;
  };
}

export interface CompareCandidatesResult {
  ranked: ComparedCandidate[];
  criteria: Required<CompareCriteria>;
  plotPath?: string;
  evidencePlotPath?: string;
  tablePaths?: string[];
  screeningLevel?: string;
  diversity?: Record<string, unknown>;
  domainCoverage?: Record<string, unknown>;
  excludedCandidates?: Array<Record<string, unknown>>;
}

export interface ResearchBudget {
  maxCandidates?: number;
  maxCalculations?: number;
  maxWallTimeHours?: number;
  computeBudgetUsd?: number;
  maxLoopIterations?: number;
  allowExpensiveCalculations?: boolean;
}

export type EvidenceType = "database" | "literature" | "dft" | "dfpt" | "md" | "workflow" | "experiment" | "safety";

export interface EvidenceRequirementInput {
  id?: string;
  label: string;
  description?: string;
  propertyKeys?: string[];
  evidenceTypes?: EvidenceType[];
  acceptanceCriteria?: string;
  requiredForClaim?: boolean;
  [key: string]: unknown;
}

export interface CandidateGenerationInput {
  strategy?: string;
  autoDiscover?: boolean;
  discoverAdditionalCandidates?: boolean;
  allowDevelopmentFixtures?: boolean;
  maxQueries?: number;
  perQueryLimit?: number;
  seedMaterials?: string[];
  elementsInclude?: string[];
  elementsExclude?: string[];
  formulas?: string[];
  databaseQueries?: string[];
  literatureQueries?: string[];
  [key: string]: unknown;
}

export interface PlanResearchLoopPayload {
  candidates?: ComparedCandidate[];
  researchGoal?: string;
  targetApplication?: string;
  hypothesis?: string;
  constraints?: string[];
  literatureQueries?: string[];
  databaseQueries?: string[];
  evidenceRequirements?: EvidenceRequirementInput[];
  validationMethods?: EvidenceType[];
  candidateGeneration?: CandidateGenerationInput;
  autonomyMode?: "bounded" | "high-autonomy-plan" | "human-gated";
  criteria?: CompareCriteria;
  objective?: string;
  mode?: "property-backed" | "closed-loop";
  approvalPolicy?: "plan-only" | "approval-required";
  budget?: ResearchBudget;
  artifactDir: string;
}

export interface PlanResearchLoopResult {
  plan: Record<string, unknown>;
  manifestPath: string;
  reportPath: string;
  queryLogPath?: string;
  candidatePoolPath?: string;
  evidenceLedgerPath?: string;
  summaryPath?: string;
}

export interface SearchLiteraturePayload {
  planPath?: string;
  plan?: Record<string, unknown>;
  candidateId?: string;
  queries?: string[];
  query?: string;
  researchGoal?: string;
  providers?: Array<"openalex" | "crossref">;
  maxResultsPerQuery?: number;
  timeoutSeconds?: number;
  allowNetwork?: boolean;
  allowDevelopmentFixtures?: boolean;
  evidenceRequirementId?: string;
  evidenceLedgerPath?: string;
  outputLedgerPath?: string;
  sourceLabel?: string;
  artifactDir: string;
}

export interface SearchLiteratureResult {
  candidateId?: string;
  queries: string[];
  providers: string[];
  records: Array<Record<string, unknown>>;
  recordCount: number;
  evidenceRows: EvidenceLedgerInput[];
  evidenceRowCount: number;
  evidenceLedgerPath: string;
  queryLogPath: string;
  recordsPath: string;
  reportPath: string;
  usedDevelopmentFixtureData?: boolean;
  warnings: string[];
}

export interface EvidenceLedgerInput {
  candidateId?: string;
  formula?: string;
  evidenceRequirementId: string;
  claim?: string;
  status: string;
  sourceType: string;
  source?: string;
  confidence?: string;
  propertyValues?: Record<string, unknown>;
  artifactPath?: string;
  sourcePath?: string;
  citation?: string;
  queryIds?: string[];
  [key: string]: unknown;
}

export interface EvaluateResearchClaimPayload {
  planPath?: string;
  plan?: Record<string, unknown>;
  evidenceLedgerPath?: string;
  evidenceRows?: EvidenceLedgerInput[];
  candidateId?: string;
  requestedClaimLevel?: "candidate-hypothesis" | "proxy-shortlist" | "property-backed-shortlist" | "research-grade-candidate";
  artifactDir: string;
}

export interface EvaluateResearchClaimResult {
  candidateId?: string;
  claimStatus: Record<string, unknown>;
  reviewPath: string;
  reportPath: string;
  ledgerPath?: string;
  mergedLedgerPath?: string;
  missingEvidence: Array<Record<string, unknown>>;
  satisfiedEvidence: Array<Record<string, unknown>>;
  blockingEvidence: Array<Record<string, unknown>>;
  conflictingEvidence?: Array<Record<string, unknown>>;
  uncertaintySummary?: Record<string, unknown>;
  auditCertificate?: Record<string, unknown>;
  evidenceRowsReviewed: number;
}

export interface CloseEvidenceGapsPayload {
  planPath?: string;
  plan?: Record<string, unknown>;
  evidenceLedgerPath?: string;
  evidenceRows?: EvidenceLedgerInput[];
  candidateId?: string;
  requestedClaimLevel?: "candidate-hypothesis" | "proxy-shortlist" | "property-backed-shortlist" | "research-grade-candidate";
  runLiteratureSearch?: boolean;
  providers?: Array<"openalex" | "crossref">;
  allowNetwork?: boolean;
  allowDevelopmentFixtures?: boolean;
  maxLiteratureQueries?: number;
  maxResultsPerQuery?: number;
  timeoutSeconds?: number;
  artifactDir: string;
}

export interface CloseEvidenceGapsResult {
  candidateId?: string;
  claimStatus: Record<string, unknown>;
  missingEvidence: Array<Record<string, unknown>>;
  blockingEvidence: Array<Record<string, unknown>>;
  conflictingEvidence?: Array<Record<string, unknown>>;
  closurePlan: Record<string, unknown>;
  closurePlanPath: string;
  reportPath: string;
  reviewPath: string;
  reviewReportPath: string;
  evidenceLedgerPath: string;
  literatureSearch?: Record<string, unknown>;
  warnings: string[];
}

export interface IngestEvidencePayload {
  planPath?: string;
  plan?: Record<string, unknown>;
  candidateId?: string;
  parser?:
    | "auto"
    | "quantum-espresso"
    | "vasp"
    | "lammps"
    | "md"
    | "literature-json"
    | "literature-text"
    | "literature-markdown"
    | "literature-pdf"
    | "experiment-json"
    | "evidence-jsonl"
    | "csv";
  artifactPaths?: string[];
  evidenceRows?: EvidenceLedgerInput[];
  evidenceRequirementId?: string;
  evidenceLedgerPath?: string;
  outputLedgerPath?: string;
  defaultStatus?: string;
  sourceLabel?: string;
  artifactDir: string;
}

export interface IngestEvidenceResult {
  candidateId?: string;
  parser: string;
  evidenceRows: EvidenceLedgerInput[];
  evidenceRowCount: number;
  evidenceLedgerPath: string;
  reportPath: string;
  parsedArtifacts: Array<Record<string, unknown>>;
  warnings: string[];
}

export interface ExecuteResearchPlanPayload {
  planPath?: string;
  plan?: Record<string, unknown>;
  backend?: "dev-smoke" | "quantum-espresso" | "vasp" | "atomate2" | "aiida";
  executionMode?: "prepare" | "submit" | "monitor";
  executionManifestPath?: string;
  maxSteps?: number;
  allowBlockedDevSmoke?: boolean;
  allowExecution?: boolean;
  backendConfig?: Record<string, unknown>;
  artifactDir: string;
}

export interface ExecuteResearchPlanResult {
  runId: string;
  backend: string;
  scheduler?: Record<string, unknown>;
  statusSummary?: string;
  manifestPath: string;
  reportPath: string;
  resultPaths: string[];
  inputPaths?: string[];
  completedCalculations: number;
  preparedCalculations?: number;
  submittedCalculations?: number;
  skippedCalculations: number;
  propertyUpdates: ComparedCandidate[];
  rerankingPayload?: Record<string, unknown>;
  parsedEvidenceRows?: number;
  evidenceLedgerPath?: string;
  claimReviews?: Array<Record<string, unknown>>;
}

export interface AseRelaxPayload {
  materialId?: string;
  structurePath?: string;
  artifactDir: string;
  steps?: number;
  fmaxEvA?: number;
  calculator?: string;
  allowOffline?: boolean;
}

export interface AseRelaxResult {
  summaryMetrics: Record<string, number | string | boolean | null>;
  relaxedStructurePath?: string;
  trajectoryPath?: string;
  usedOfflineData: boolean;
  usedDevelopmentFixtureData?: boolean;
}

export interface BatchScreenPayload {
  candidateIds: string[];
  limit: number;
  artifactDir: string;
  allowOffline?: boolean;
}

export interface BatchScreenResult {
  screened: CandidateSummary[];
  ranked: ComparedCandidate[];
  tablePaths?: string[];
  excludedCandidates?: Array<Record<string, unknown>>;
  usedOfflineData: boolean;
  usedDevelopmentFixtureData?: boolean;
}

export interface ExportReportPayload {
  title: string;
  goal: string;
  evaluationCriteria: string[];
  rankedCandidates: ComparedCandidate[];
  notePaths?: string[];
  artifactPaths?: string[];
  outputPath: string;
  screeningLevel?: string;
  domainWarnings?: string[];
  methodNotes?: string[];
  provenance?: Record<string, unknown>;
}

export interface ExportReportResult {
  outputPath: string;
  references: string[];
}
