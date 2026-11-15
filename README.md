# MARSCOPE 0.4.0

**From orbit to bootprint: evidence-informed Mars exploration research.**

MARSCOPE combines a React/Three.js mission interface, a FastAPI science and route-planning backend, and a standalone TypeScript Jev decision service. Jev can review NASA/JPL evidence and produce preference weights for the balanced route profile.

> **Research prototype only.** The planner's default terrain is not a verified geographic surface. A route returned by this software is not certified astronaut guidance. Jev weights express preferences, not probabilities of route success or safety. Import and verify real planetary data before interpreting routes geographically.

## Repository layout

- \`frontend/\`: React + Vite interface.
- \`backend/\`: FastAPI, terrain, route planning, NASA/PDS data and Jev proxy endpoints.
- \`decision-service/\`: Node/TypeScript Jev service. It supports TypeSafe and OpenCode providers.
- \`docs/JEV-INTEGRATION.md\`: Jev architecture, security boundaries, deployment and verification.

The release notes retained under \`MARSCOPE_0.4.0/\` are documentation only. **Run all commands from the repository root or the indicated source directory; do not run them from the \`MARSCOPE_0.4.0/\` folder.**

## Local development

Requirements: Python 3.11+, Node.js 22.15+, and internet access for the first dependency install.

Start the three services in three separate terminals.

### 1. Jev decision service

From the repository root:

\`\`\`bash
cd decision-service
npm ci
npm run build
\`\`\`

Set a private service token and start the service.

PowerShell:

\`\`\`powershell
$env:PORT = "8100"
$env:MARSCOPE_JEV_SERVICE_TOKEN = "<same-random-token-used-by-backend>"
npm start
\`\`\`

macOS/Linux:

\`\`\`bash
export PORT=8100
export MARSCOPE_JEV_SERVICE_TOKEN="<same-random-token-used-by-backend>"
npm start
\`\`\`

### 2. Python API

In a second terminal, from the repository root:

\`\`\`bash
cd backend
python -m venv .venv
\`\`\`

Activate the environment:

PowerShell: \`.venv\\Scripts\\Activate.ps1\`

macOS/Linux: \`source .venv/bin/activate\`

Then install and start:

\`\`\`bash
python -m pip install -r requirements.txt
\`\`\`

PowerShell:

\`\`\`powershell
$env:JEV_SERVICE_URL = "http://127.0.0.1:8100"
$env:MARSCOPE_JEV_SERVICE_TOKEN = "<same-random-token-used-by-jev-service>"
python -m uvicorn app.main:app --reload --port 8000
\`\`\`

macOS/Linux:

\`\`\`bash
export JEV_SERVICE_URL="http://127.0.0.1:8100"
export MARSCOPE_JEV_SERVICE_TOKEN="<same-random-token-used-by-jev-service>"
python -m uvicorn app.main:app --reload --port 8000
\`\`\`

The token must match exactly in both terminals. Generate a fresh random value for your own machine; never commit it or paste it into frontend variables.

### 3. Frontend

In a third terminal, from the repository root:

\`\`\`bash
cd frontend
npm ci
npm run dev
\`\`\`

Open <http://localhost:5173>. During local development the frontend calls the API at <http://localhost:8000>.

## Configure Jev in the app

Open **JEV INTEL**, choose **TypeSafe** or **OpenCode Console**, and enter the matching provider API key. The provider key is held in page memory and sent to the local Node service for the request; it is not a build-time \`VITE_*\` variable. Refreshing the page clears it.

The internal service token and the provider API key are different secrets:

- \`MARSCOPE_JEV_SERVICE_TOKEN\`: shared only between the Python API and the Node decision service.
- TypeSafe or OpenCode API key: supplied by the user in the JEV INTEL panel.

The evidence assessment and adaptive pathfinding endpoints are:

- \`POST /api/jev/evidence-assessment\`
- \`POST /api/jev/pathfinding-weights\`

Diagnostics:

- Frontend: <http://localhost:5173>
- FastAPI health: <http://localhost:8000/api/health>
- Jev service health: <http://localhost:8100/health>
- FastAPI interactive docs: <http://localhost:8000/docs>

If Jev is unavailable or returns an invalid decision, the app must not apply stale or fabricated weights. The ordinary planner remains available with its static route profiles.

## Deployment

The root \`render.yaml\` defines two Render web services:

1. \`marswalk-api\`: Python/FastAPI.
2. \`marscope-jev\`: Node decision service.

The blueprint creates a shared \`marscope-jev-secrets\` environment-variable group with a generated \`MARSCOPE_JEV_SERVICE_TOKEN\`. Both services must receive that same value. The backend's \`JEV_SERVICE_URL\` must point to the actual public URL of the Node service; update it if Render assigns a different hostname.

For a separately hosted production frontend, set \`VITE_API_BASE\` to the public URL of \`marswalk-api\` at build time and configure the backend's \`CORS_ORIGINS\` to include the frontend origin. Never expose either server-side token as a \`VITE_*\` variable.

See [Jev integration notes](docs/JEV-INTEGRATION.md) for the request flow, local token setup and deployment details.

## Tests

Run each suite from its project directory.

Backend:

\`\`\`bash
cd backend
python -m pip install pytest
python -m pytest -q
\`\`\`

Jev decision service:

\`\`\`bash
cd decision-service
npm ci
npm run build
npm test
\`\`\`

Frontend:

\`\`\`bash
cd frontend
npm ci
npm run build
\`\`\`

The unit tests verify local code and policy behaviour. A real provider call still requires a valid provider key and provider-side model access.

## Scientific and engineering boundaries

- NASA/PDS and orbital archive results are discovery metadata until the original product label and documentation are checked.
- A rover panorama or map tile is imagery, not a DEM or an astronaut-scale hazard map.
- Imported elevation and science layers require verified footprints, coordinate systems, units and provenance.
- Jev's scores and probabilities are not calibrated scientific posteriors.
- The planner's terrain, mobility and resource assumptions are research estimates, not validated operational models.

See [algorithm notes](docs/ALGORITHM.md), [science and data notes](docs/SCIENCE_AND_DATA.md), and [validation boundaries](docs/VALIDATION.md).
