import test from "node:test";
import assert from "node:assert/strict";
import { decideEvidence, type JevEvidenceJudgement } from "./policy.js";

const base: JevEvidenceJudgement = {
  evidenceId: "PIA26560", title: "Curiosity Views Boxwork Patterns", stance: "supports", stanceConfidence: 0.8,
  relevanceScore: 3, relevanceConfidence: 0.9, directSupportProbability: 0.9,
  noveltyScore: 2, noveltyConfidence: 0.7, model: "jev-1.14.0", tokens: { input: 100, output: 20 },
};

test("strong supporting result remains a candidate, not a confirmed finding", () => {
  const result = decideEvidence(base, false);
  assert.equal(result.label, "SUPPORTING_CANDIDATE");
  assert.equal(result.geospatialLinkage, "NOT_GEOREFERENCED");
  assert.equal(result.routeEngineAction, "NO_AUTOMATIC_ROUTE_CHANGE");
});

test("relevant contradictory evidence is retained as counter-evidence", () => {
  const result = decideEvidence({ ...base, stance: "contradicts" }, false);
  assert.equal(result.label, "COUNTER_EVIDENCE");
  assert.equal(result.routeEngineAction, "NO_AUTOMATIC_ROUTE_CHANGE");
});

test("low-confidence contradiction is sent to human review", () => {
  const result = decideEvidence({ ...base, stance: "contradicts", stanceConfidence: 0.2 }, false);
  assert.equal(result.label, "HUMAN_REVIEW");
});

test("low relevance triggers human review", () => {
  const result = decideEvidence({ ...base, relevanceScore: 0.5 }, false);
  assert.equal(result.label, "HUMAN_REVIEW");
});

test("missing geospatial registration never links evidence to route coordinates", () => {
  const result = decideEvidence(base, false);
  assert.equal(result.geospatialLinkage, "NOT_GEOREFERENCED");
});
