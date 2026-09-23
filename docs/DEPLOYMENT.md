# Deployment

## Backend — Render
Create a Web Service from this GitHub repository.
Root directory: `backend`
Build: `pip install -r requirements.txt`
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Frontend — Vercel
Import the repository and set the Root Directory to `frontend`.
Build command: `npm run build`
Output directory: `dist`
Environment variable:
`VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com`

## TigerGraph
Configure TigerGraph Savanna/Community Edition and the graph required by the challenge. Add credentials through platform environment variables, never source control.

## Note
This repository contains a deterministic local demo boundary. Full challenge operation still requires the HHGOA dataset, TigerGraph graph, TigerGraph MCP, GraphRAG retrieval, policy rules, and case-memory implementation.
