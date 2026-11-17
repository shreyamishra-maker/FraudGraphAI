# FraudGraph AI

A benchmark-facing prototype for the TigerGraph HHGOA agentic fraud-investigation challenge.

## Current implementation status

- FastAPI serves the 20 benchmark case artifacts from the repository-root `cases/` directory.
- The React/Vite dashboard retrieves an artifact by case ID and displays its evidence, uncertainty, SAR metadata and next-best-action recommendations.
- A deterministic approval-routing module assigns an approval route to each recommended action.
- A TigerGraph MCP client boundary is included, but live MCP authentication and graph writes are **not verified** in the current deployment.
- The current `/investigate` endpoint replays the selected benchmark JSON. It does **not** independently recompute fraud probability, run live graph traversals, call an LLM, or write a case to TigerGraph.
- The 20 case JSON files are benchmark answer artifacts, not proof that the live graph independently reproduced those findings.

Please keep these distinctions explicit in demos and submissions.

## Repository layout

- `backend/app/`: FastAPI service, policy routing, MCP client boundary and GraphRAG context helper
- `cases/`: HHG-001.json through HHG-020.json benchmark artifacts
- `frontend/`: React + Vite analyst dashboard
- `tigergraph/`: current graph investigation query draft and MCP environment example
- `Dockerfile`: repository-root Docker build
- `render.yaml`: Render Docker Blueprint configuration
- `vercel.json`: Vite static frontend configuration

The HHGOA dataset is not included. The transaction CSV is large and should only be stored locally or in an approved private data location. Read the dataset's supplied README before importing it.

## Run locally

### Backend

From the repository root:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Frontend

In a second terminal:

```bash
cd frontend
npm install
# Optional: set VITE_API_URL=http://127.0.0.1:8000 in frontend/.env.local
npm run dev
```

For a production frontend build:

```bash
npm run build
```

## API

- `GET /`: service information
- `GET /health`: service health and number of available case files
- `GET /case/HHG-001`: retrieve a benchmark artifact
- `GET /tg-status`: report MCP configuration status (not a connectivity proof)
- `POST /investigate`: replay a benchmark artifact and attach deterministic approval routes

Example:

```bash
curl -X POST http://127.0.0.1:8000/investigate \
  -H "Content-Type: application/json" \
  -d '{"case_id":"HHG-001","trigger":"analyst"}'
```

Valid case IDs use the form `HHG-001` through `HHG-020`.

## Deployment

### Render backend

The repository Blueprint uses the root `Dockerfile` and root build context. The image copies `backend/app` and `cases/` into the container. If deploying manually, choose Docker, set Dockerfile path to `./Dockerfile`, build context to `.`, and health check path to `/health`.

### Vercel frontend

Set the Vercel project root directory to `frontend`. Set the environment variable `VITE_API_URL` to the deployed backend base URL (without a trailing slash). The Vite build output is `dist`.

## TigerGraph and GraphRAG

The repository contains an MCP client boundary and a helper for composing graph, document and case-memory context. They are integration scaffolding, not evidence of a live graph connection. Configure secrets as environment variables; never commit tokens, passwords, private dataset files or `.env` files.

The current TigerGraph query file is a draft for the observed `Transaction_Fraud` graph schema. Validate and install queries against the target TigerGraph instance before treating them as operational.

## Policy routing

The policy module only returns approval routes; it does not execute actions. Analyst escalation and report filing route to L2, transaction decline routes to L1, and card blocking routes to L1 or L2 based on exposure. Confirm all thresholds and action permissions against the challenge's supplied bank policy before production use.

## Security and limitations

- This is a demonstration prototype, not a production fraud-control system.
- The API currently has no authentication or role-based authorization.
- CORS is permissive for demo use; restrict allowed origins before production.
- No real financial action is executed by this API.
- A benchmark artifact must not be described as a live TigerGraph or LLM investigation.
- Do not expose private case data or credentials in public logs or screenshots.

## Project

GitHub: https://github.com/shreyamishra-maker/FraudGraphAI
