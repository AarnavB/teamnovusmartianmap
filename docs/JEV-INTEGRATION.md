# MARSCOPE JEV integration

## Architecture

The browser calls the existing FastAPI backend at /api/jev/pathfinding-weights.
FastAPI obtains the selected site's actual available_layers inventory and
forwards the mission prompt, provider selection and request-scoped provider key
to the standalone Node service.

The Node service uses the TypeSafe or OpenCode adapter in
decision-service/src/jevDecision.ts. It returns a validated objective vector.
The Python planner applies that vector only to Route B (the balanced profile).
Route A (conservative) and Route C (science-first) continue to use their static
profiles. The normal planner and LPA* waypoint/obstacle repair both receive the
same MissionConstraints.objective_weights vector.

JEV controls preference ranking only. Slope, obstacles, nodata, resource budgets,
temperature, oxygen, EVA time and return-reserve feasibility remain deterministic
planner checks. An absent layer is not interpreted as zero risk or zero evidence.

## Local development

Run the JEV service in one terminal:

    cd decision-service
    npm ci
    npm run build
    $env:PORT = "8100"
    $env:MARSCOPE_JEV_SERVICE_TOKEN = "<same-random-token-as-backend>"
    npm start

Run FastAPI in another terminal, from backend:

    $env:JEV_SERVICE_URL = "http://127.0.0.1:8100"
    $env:MARSCOPE_JEV_SERVICE_TOKEN = "<same-random-token-as-jev-service>"
    uvicorn app.main:app --reload --port 8000

Use a unique random token; for example, create one in PowerShell:

    [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLower()

The provider API key is entered in JEV Intel. It remains in React memory and is
sent in an HTTPS JSON request body; it is not written to local storage, a cookie,
a URL, a server environment variable, or an audit file. Refreshing the page
clears it. The service intentionally does not log request payloads or provider
error text.

## Render configuration

The blueprint defines two web services:

- marswalk-api: the existing FastAPI backend.
- marscope-jev: the standalone Node decision service.

Set MARSCOPE_JEV_SERVICE_TOKEN to the same independently generated secret on
both services. Render prompts for this value because it is marked sync: false;
do not commit the token into this repository. The backend's JEV_SERVICE_URL
defaults to https://marscope-jev.onrender.com in the blueprint. Adjust that
value if the Node service is given a different Render hostname.

The JEV Node service exposes only /health publicly without a token. All /v1/*
routes require the shared service token. The user-supplied TypeSafe or OpenCode
API key is separate from this service token.

## Fallback behaviour

If the Node service is not configured, unavailable, rate-limited, times out, or
returns an invalid vector, FastAPI reports a safe error. The frontend clears
the adaptive decision and replans with the static balanced profile. It never
reuses a stale vector. Existing route planning continues to work without JEV.

## Verification commands

Node decision service: npm ci, npm run build, npm test (from decision-service).
Frontend: npm ci, npm run build (from frontend).
Backend: python -m pytest -q (from backend).

Provider integration calls require a valid provider key and should be exercised
manually in a local environment with the Node and FastAPI services configured.
Unit tests do not claim that remote provider credentials or model availability
have been verified.
