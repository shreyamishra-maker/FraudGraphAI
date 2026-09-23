# FraudGraph AI

Agentic Fraud Investigation & Next-Best Action for the TigerGraph HHGOA challenge.

## What is included
- Dataset-grounded investigation design
- Deterministic Fraud Policy R1–R10 boundary
- TigerGraph schema and investigation queries
- TigerGraph MCP configuration boundary
- GraphRAG retrieval boundary
- Analyst dashboard (Vite/React)
- 20 benchmark JSON answer records under `cases/`
- Vercel + Render deployment configuration

## Dataset
The HHGOA_IEEE dataset is **not committed to GitHub** because `transactions.csv` is about 708 MB and contains the challenge data. Put the supplied files in a local/private data directory and run the dataset-backed investigation pipeline.

Expected files:
- `transactions.csv`
- `identity.csv`
- `closed_cases_history.csv`
- `case_pack.csv`

Read the supplied README before loading the data.

## Quick start
```bash
cd backend
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Production architecture
Trigger → Case → TigerGraph/MCP → GraphRAG → Pattern assessment → uncertainty gate → evidence request → policy engine → next-best action → explanation → case memory.

The LLM should synthesize retrieved evidence and select tools; graph traversal and fraud-pattern analysis remain graph/query responsibilities.

## Important benchmark status
The 20 JSON files are **dataset-grounded candidate outputs**. They currently set `written_to_graph=false` because no TigerGraph instance was connected during generation. After connecting TigerGraph/MCP, rerun the cases and update each record with the real graph case ID and write status.

## Secrets
Never commit `.env`, TigerGraph credentials, API keys, or private dataset files.
