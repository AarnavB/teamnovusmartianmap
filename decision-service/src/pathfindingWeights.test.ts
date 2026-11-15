import assert from "node:assert/strict";
import test from "node:test";
import { evaluatePathfindingWeights, PATHFINDING_OBJECTIVES } from "./jevDecision.js";

const allLayerIds = ["atmosphere", "radiation", "science"];

function makeAnswers() {
  const answers: Record<string, unknown> = {
    mission_strategy: { choice: "science_first", confidence: 0.91 },
  };
  for (const objective of PATHFINDING_OBJECTIVES) {
    const isScience = objective.id === "science_opportunity_cost";
    const isTerrain = objective.id === "terrain_risk";
    answers[`priority_${objective.id}`] = { score: isScience ? 3 : isTerrain ? 2 : 1, confidence: 0.8 };
    answers[`relevance_${objective.id}`] = { noul: isScience ? 0.95 : isTerrain ? 0.75 : 0.25 };
  }
  return answers;
}

async function withMockResponse<T>(answers: Record<string, unknown>, run: () => Promise<T>): Promise<T> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({
    model: "jev-1.13-free",
    answers,
    usage: { input_tokens: 300, output_tokens: 80 },
  }), { status: 200, headers: { "content-type": "application/json" } });
  try {
    return await run();
  } finally {
    globalThis.fetch = originalFetch;
  }
}

test("Jev Choice, Score and Noul produce the direct A* objective-weight vector", async () => {
  const result = await withMockResponse(makeAnswers(), () => evaluatePathfindingWeights({
    apiKey: "test-key",
    provider: "opencode",
    missionPrompt: "Prioritize scientifically valuable terrain without ignoring mobility constraints.",
    availableLayers: allLayerIds,
  }));

  assert.equal(result.model, "jev-1.13-free");
  assert.equal(result.strategy, "science_first");
  assert.equal(result.policyVersion, "jev-weighted-a-star-1.0.0");
  assert.equal(result.jevInfluenceShare, 0.9);
  assert.equal(result.strategyPriorShare, 0.1);
  assert.ok(Math.abs(Object.values(result.weights).reduce((sum, value) => sum + value, 0) - 1) < 1e-9);
  assert.ok(result.weights.science_opportunity_cost > result.weights.distance);
  assert.ok(result.weights.terrain_risk > result.weights.distance);
  assert.equal(result.usage.input_tokens, 300);
});

test("Jev receives no questions for spatial objectives without their data layers", async () => {
  const answers = makeAnswers();
  delete answers.priority_environment_risk;
  delete answers.relevance_environment_risk;
  delete answers.priority_radiation;
  delete answers.relevance_radiation;
  delete answers.priority_science_opportunity_cost;
  delete answers.relevance_science_opportunity_cost;
  const result = await withMockResponse(answers, () => evaluatePathfindingWeights({
    apiKey: "test-key",
    provider: "opencode",
    missionPrompt: "Prefer lower uncertainty and terrain difficulty.",
    availableLayers: [],
  }));
  assert.equal(result.weights.environment_risk, 0);
  assert.equal(result.weights.radiation, 0);
  assert.equal(result.weights.science_opportunity_cost, 0);
  assert.ok(result.weights.uncertainty > 0);
});
