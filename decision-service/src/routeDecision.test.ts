import assert from "node:assert/strict";
import test from "node:test";
import { evaluateRouteCandidates, type RouteCandidateInput } from "./jevDecision.js";

const metrics: RouteCandidateInput["metrics"] = {
  distance_m: 600,
  duration_min: 40,
  energy_wh: 35,
  terrain_risk_pct: 40,
  environment_risk_pct: null,
  radiation_index_pct: null,
  uncertainty_pct: 35,
  scientific_value_pct: 50,
  return_feasible: true,
};

function candidates(): RouteCandidateInput[] {
  return [
    { id: "A", name: "Conservative route", profile: "conservative", metrics: { ...metrics, distance_m: 600 } },
    { id: "B", name: "Balanced route", profile: "balanced", metrics: { ...metrics, distance_m: 610 } },
    { id: "C", name: "Science-first route", profile: "science_first", metrics: { ...metrics, distance_m: 620 } },
  ];
}

const mockAnswers = {
  preferred_route: { choice: "B", confidence: 0.8, probabilities: { A: 0.1, B: 0.8, C: 0.1 } },
  route_score_A: { score: 2, confidence: 0.7 },
  route_score_B: { score: 3, confidence: 0.9 },
  route_score_C: { score: 1, confidence: 0.6 },
  mission_fit_A: { noul: 0.55 },
  mission_fit_B: { noul: 0.75 },
  mission_fit_C: { noul: 0.9 },
};

async function withMockOpenCodeResponse<T>(answers: typeof mockAnswers, run: () => Promise<T>): Promise<T> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({
    model: "jev-1.13-free",
    answers,
    usage: { input_tokens: 120, output_tokens: 45 },
  }), { status: 200, headers: { "content-type": "application/json" } });
  try {
    return await run();
  } finally {
    globalThis.fetch = originalFetch;
  }
}

test("Jev Choice, Score and Noul fuse into a validated route selection", async () => {
  const requestCandidates = candidates();
  const result = await withMockOpenCodeResponse(mockAnswers, () => evaluateRouteCandidates({
    apiKey: "test-key",
    provider: "opencode",
    missionPrompt: "Prefer a balanced route but preserve scientific value.",
    candidates: requestCandidates,
  }));

  assert.equal(result.model, "jev-1.13-free");
  assert.equal(result.selectedRouteId, "B");
  assert.equal(result.choiceRouteId, "B");
  assert.equal(result.policyVersion, "jev-route-fusion-0.1.0");
  assert.equal(result.results[0].routeId, "B");
  assert.ok(Math.abs(result.results[0].fusionScore - 0.885) < 1e-9);
  assert.equal(result.usage.input_tokens, 120);
});

test("Jev is never called with a route that fails deterministic feasibility", async () => {
  const invalidCandidates = candidates();
  invalidCandidates[1].metrics.return_feasible = false;
  let called = false;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => {
    called = true;
    throw new Error("The model must not be called for an infeasible route set.");
  };
  try {
    await assert.rejects(
      evaluateRouteCandidates({ apiKey: "test-key", provider: "opencode", missionPrompt: "Test feasibility", candidates: invalidCandidates }),
      /Only routes that pass MARSCOPE's deterministic return-resource feasibility check/,
    );
    assert.equal(called, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("Jev cannot select a route ID outside the supplied alternatives", async () => {
  const invalidAnswers = { ...mockAnswers, preferred_route: { choice: "Z", confidence: 0.99, probabilities: { Z: 1 } } } as unknown as typeof mockAnswers;
  await withMockOpenCodeResponse(invalidAnswers, async () => {
    await assert.rejects(
      evaluateRouteCandidates({ apiKey: "test-key", provider: "opencode", missionPrompt: "Test candidate validation", candidates: candidates() }),
      /did not match a supplied candidate ID/,
    );
  });
});
