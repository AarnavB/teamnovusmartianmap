export type EvidenceStance = "supports" | "contradicts" | "contextual" | "insufficient";
export type DecisionLabel = "SUPPORTING_CANDIDATE" | "COUNTER_EVIDENCE" | "INVESTIGATE_FURTHER" | "HUMAN_REVIEW";

export interface JevEvidenceJudgement {
  evidenceId: string;
  title: string;
  stance: EvidenceStance;
  stanceConfidence: number;
  relevanceScore: number;
  relevanceConfidence: number;
  directSupportProbability: number;
  noveltyScore: number;
  noveltyConfidence: number;
  model: string;
  tokens: { input: number | null; output: number | null };
}

export interface PolicyDecision {
  label: DecisionLabel;
  rationale: string;
  geospatialLinkage: "NOT_GEOREFERENCED" | "VERIFIED_FOOTPRINT_AVAILABLE";
  routeEngineAction: "NO_AUTOMATIC_ROUTE_CHANGE";
  policyVersion: string;
}

const clamp01 = (value: number): number => Math.min(1, Math.max(0, Number.isFinite(value) ? value : 0));

/**
 * Application policy over Jev's judgments. It deliberately does not treat
 * Jev confidence as correctness probability, and never turns rover imagery
 * into a coordinate or an automatic navigation instruction.
 */
export function decideEvidence(judgement: JevEvidenceJudgement, georeferenced: boolean): PolicyDecision {
  const relevance = Math.max(0, Math.min(3, judgement.relevanceScore));
  const support = clamp01(judgement.directSupportProbability);
  const relevanceConfidence = clamp01(judgement.relevanceConfidence);
  const stanceConfidence = clamp01(judgement.stanceConfidence);
  const geospatialLinkage: PolicyDecision["geospatialLinkage"] = georeferenced ? "VERIFIED_FOOTPRINT_AVAILABLE" : "NOT_GEOREFERENCED";
  const shared = { geospatialLinkage, routeEngineAction: "NO_AUTOMATIC_ROUTE_CHANGE" as const, policyVersion: "jev-evidence-triage-0.4.0" };

  // These are transparent prototype triage thresholds, not calibrated scientific cutoffs.
  // They must be tuned against human-labelled evidence before research claims are made.
  if (judgement.stance === "insufficient" || relevance < 1.5 || relevanceConfidence < 0.45 || stanceConfidence < 0.45) {
    return {
      ...shared,
      label: "HUMAN_REVIEW",
      rationale: "The record is inconclusive, weakly relevant, or the model judgment is not sufficiently concentrated under this provisional rubric. Inspect the original product and its label.",
    };
  }

  if (judgement.stance === "contradicts") {
    return {
      ...shared,
      label: "COUNTER_EVIDENCE",
      rationale: "Jev classified this sufficiently relevant record as potentially contradictory. Preserve it as counter-evidence for scientific review; this is not a validated falsification.",
    };
  }

  if (judgement.stance === "supports" && relevance >= 2.35 && support >= 0.78 && relevanceConfidence >= 0.60 && stanceConfidence >= 0.60) {
    return {
      ...shared,
      label: "SUPPORTING_CANDIDATE",
      rationale: "The record meets the prototype's provisional relevance and model-judgment thresholds. It is a supporting candidate for human review, not a confirmed geological conclusion or calibrated probability.",
    };
  }

  return {
    ...shared,
    label: "INVESTIGATE_FURTHER",
    rationale: "The record may help answer the question, but it does not meet the provisional supporting-candidate threshold. Seek corroborating observations or inspect the original product.",
  };
}

export function clampProbability(value: unknown): number {
  return clamp01(Number(value));
}
