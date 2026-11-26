# Deployment

## Backend — Render

The repository's render.yaml uses the repository-root Dockerfile and build context:

- Runtime: Docker
- Dockerfile: ./Dockerfile
- Build context: repository root
- Health check: /health

If configuring the service manually, use the same values. The Dockerfile copies both backend/app and the root cases/ directory into the image.

Optional environment variables:

- CORS_ORIGINS: comma-separated allowed browser origins. Include the exact Vercel production URL.
- TG_HOST, TG_GRAPHNAME, TG_API_TOKEN: reserved for TigerGraph MCP integration. Their presence does not prove authentication or graph connectivity.

## Frontend — Vercel

- Root Directory: frontend
- Build command: npm run build
- Output directory: dist
- Environment variable: VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com

After changing environment variables, trigger a new deployment. Ensure the backend's CORS_ORIGINS includes the exact deployed frontend origin.

## Local development

From the repository root:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm install
# Optional: VITE_API_URL=http://127.0.0.1:8000
npm run dev
```

## Current limitation

Deployment configuration and CI builds do not prove that Render or Vercel is live. The current API replays benchmark JSON artifacts. Live TigerGraph MCP authentication, graph retrieval, GraphRAG retrieval, LLM orchestration and graph case writes are not verified or implemented end-to-end.
