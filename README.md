# FraudGraph AI

Agentic Fraud Investigation & Next-Best Action for the TigerGraph HHGOA challenge.

## Quick start

### Backend
```bash
cd backend
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000  
Frontend: http://localhost:5173

## Environment
Copy `.env.example` to `.env`. Never commit credentials, tokens, or private datasets.

## TigerGraph
See `tigergraph/schema.gsql`, `tigergraph/loading.gsql`, and `tigergraph/queries.gsql`.

## Submission
The challenge requires a working agent, GitHub repository, 20 case outputs, graph-written cases, SAR where required, initial/final next-best action, demo video, technical blog, and a social post tagging TigerGraph.
