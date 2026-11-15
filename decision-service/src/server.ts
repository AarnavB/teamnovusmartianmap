import express, { type NextFunction, type Request, type Response } from "express";
import { createHash, timingSafeEqual } from "node:crypto";
import {
  evaluateNasaEvidence,
  evaluatePathfindingWeights,
  type JevProvider,
  type NasaEvidenceInput,
} from "./jevDecision.js";

const app = express();
const port = Number(process.env.PORT ?? process.env.MARSCOPE_JEV_PORT ?? 8100);
const host = process.env.HOST ?? "0.0.0.0";
const serviceToken = process.env.MARSCOPE_JEV_SERVICE_TOKEN?.trim() ?? "";
const requestTimeoutMs = Math.min(120_000, Math.max(15_000, Number(process.env.JEV_REQUEST_TIMEOUT_MS ?? 95_000)));
const rateWindowMs = 60_000;
const rateLimitPerWindow = 20;
const requestCounts = new Map<string, { count: number; startedAt: number }>();

app.disable("x-powered-by");
app.use((_req, res, next) => {
  res.setHeader("Cache-Control", "no-store, max-age=0");
  res.setHeader("Pragma", "no-cache");
  res.setHeader("X-Content-Type-Options", "nosniff");
  next();
});

function timingSafeTokenMatch(candidate: string, expected: string): boolean {
  const candidateDigest = createHash("sha256").update(candidate).digest();
  const expectedDigest = createHash("sha256").update(expected).digest();
  return timingSafeEqual(candidateDigest, expectedDigest);
}

function requireServiceToken(req: Request, res: Response, next: NextFunction): void {
  if (!serviceToken) {
    res.status(503).json({ detail: "JEV service authentication is not configured." });
    return;
  }
  const match = /^Bearer\s+(.+)$/i.exec(req.header("authorization") ?? "");
  const candidate = match?.[1] ?? "";
  if (!candidate || !timingSafeTokenMatch(candidate, serviceToken)) {
    res.status(401).json({ detail: "Unauthorized JEV service request." });
    return;
  }
  next();
}

function limitRequests(req: Request, res: Response, next: NextFunction): void {
  const now = Date.now();
  const key = req.ip || "unknown";
  const current = requestCounts.get(key);
  if (!current || now - current.startedAt >= rateWindowMs) {
    requestCounts.set(key, { count: 1, startedAt: now });
    next();
    return;
  }
  current.count += 1;
  if (current.count > rateLimitPerWindow) {
    res.status(429).json({ detail: "JEV request limit reached. Try again shortly." });
    return;
  }
  next();
}

function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  let timer: NodeJS.Timeout | undefined;
  const timeout = new Promise<never>((_resolve, reject) => {
    timer = setTimeout(() => reject(new Error("JEV request timed out.")), timeoutMs);
    timer.unref();
  });
  return Promise.race([promise, timeout]).finally(() => {
    if (timer) clearTimeout(timer);
  });
}

app.get("/health", (_req, res) => {
  res.status(200).json({
    status: "ok",
    service: "marscope-jev-decision-service",
    configured: Boolean(serviceToken),
  });
});

app.use("/v1", requireServiceToken);
app.use("/v1", express.json({ limit: "32kb", strict: true }));

app.post("/v1/pathfinding-weights", limitRequests, async (req: Request, res: Response) => {
  const body = req.body as Record<string, unknown> | null;
  if (!body || typeof body !== "object") {
    res.status(400).json({ detail: "A JSON request body is required." });
    return;
  }
  const { provider, apiKey, missionPrompt, availableLayers, missionContext } = body;
  if (provider !== "typesafe" && provider !== "opencode") {
    res.status(400).json({ detail: "Select a supported JEV provider." });
    return;
  }
  if (typeof apiKey !== "string" || apiKey.trim().length === 0 || apiKey.length > 1024) {
    res.status(400).json({ detail: "Enter a valid provider API key (maximum 1,024 characters)." });
    return;
  }
  if (typeof missionPrompt !== "string" || missionPrompt.trim().length < 1 || missionPrompt.length > 600) {
    res.status(400).json({ detail: "Mission prompt must contain 1–600 characters." });
    return;
  }
  if (!Array.isArray(availableLayers) || availableLayers.length > 32 ||
      availableLayers.some((value) => typeof value !== "string" || value.length > 64)) {
    res.status(400).json({ detail: "Available terrain layers are invalid." });
    return;
  }
  if (missionContext !== undefined &&
      (missionContext === null || typeof missionContext !== "object" || Array.isArray(missionContext))) {
    res.status(400).json({ detail: "Mission context must be a simple object." });
    return;
  }

  try {
    const result = await withTimeout(
      evaluatePathfindingWeights({
        apiKey,
        provider: provider as JevProvider,
        missionPrompt,
        availableLayers: availableLayers as string[],
        missionContext: missionContext as Record<string, string | number | boolean | null> | undefined,
      }),
      requestTimeoutMs,
    );
    res.status(200).json(result);
  } catch (error) {
    const timedOut = error instanceof Error && error.message === "JEV request timed out.";
    // Provider errors and request bodies are intentionally not logged: either may contain credentials.
    res.status(timedOut ? 504 : 502).json({
      detail: timedOut
        ? "JEV timed out. Use the static balanced route or retry."
        : "JEV could not produce a valid weight vector. No adaptive weights were applied.",
    });
  }
});

app.post("/v1/evidence-assessment", limitRequests, async (req: Request, res: Response) => {
  const body = req.body as Record<string, unknown> | null;
  if (!body || typeof body !== "object") {
    res.status(400).json({ detail: "A JSON request body is required." });
    return;
  }
  const { provider, apiKey, objective, hypothesis, evidence } = body;
  if (provider !== "typesafe" && provider !== "opencode") {
    res.status(400).json({ detail: "Select a supported JEV provider." });
    return;
  }
  if (typeof apiKey !== "string" || apiKey.trim().length === 0 || apiKey.length > 1024) {
    res.status(400).json({ detail: "Enter a valid provider API key (maximum 1,024 characters)." });
    return;
  }
  if (typeof objective !== "string" || !objective.trim() || objective.length > 500) {
    res.status(400).json({ detail: "Mission objective must contain 1–500 characters." });
    return;
  }
  if (typeof hypothesis !== "string" || !hypothesis.trim() || hypothesis.length > 700) {
    res.status(400).json({ detail: "Hypothesis must contain 1–700 characters." });
    return;
  }
  if (!Array.isArray(evidence) || evidence.length < 1 || evidence.length > 4) {
    res.status(400).json({ detail: "Provide between 1 and 4 NASA evidence records." });
    return;
  }
  for (const record of evidence) {
    if (!record || typeof record !== "object" || Array.isArray(record)) {
      res.status(400).json({ detail: "Each NASA evidence record must be an object." });
      return;
    }
    const item = record as Record<string, unknown>;
    if (["id", "title", "summary", "url"].some((key) =>
      typeof item[key] !== "string" || !(item[key] as string).trim() || (item[key] as string).length > 2_000
    )) {
      res.status(400).json({ detail: "Evidence records need an ID, title, summary and source URL." });
      return;
    }
  }

  try {
    const result = await withTimeout(
      evaluateNasaEvidence({
        apiKey,
        provider: provider as JevProvider,
        objective,
        hypothesis,
        evidence: evidence as NasaEvidenceInput[],
      }),
      requestTimeoutMs,
    );
    res.status(200).json(result);
  } catch (error) {
    const timedOut = error instanceof Error && error.message === "JEV request timed out.";
    // Never log provider error text or evidence payloads; they can contain credentials or user text.
    res.status(timedOut ? 504 : 502).json({
      detail: timedOut
        ? "JEV evidence review timed out. Retry or continue without AI assessment."
        : "JEV could not assess the supplied evidence. The original NASA record remains unchanged.",
    });
  }
});

app.use((error: unknown, _req: Request, res: Response, _next: NextFunction) => {
  const errorType = (error as { type?: string } | null)?.type;
  const isBodyError = error instanceof SyntaxError || errorType === "entity.too.large";
  res.status(isBodyError ? 400 : 500).json({
    detail: isBodyError ? "Invalid or oversized JSON request." : "JEV service request failed.",
  });
});

app.listen(port, host, () => {
  console.log(`MARSCOPE JEV decision service listening on ${host}:${port}`);
});
