from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="FraudGraph AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvestigationRequest(BaseModel):
    case_id: str
    trigger: str = "analyst"

@app.get("/health")
def health():
    return {"status": "ok", "service": "FraudGraph AI"}

@app.post("/investigate")
def investigate(req: InvestigationRequest):
    # Deterministic demo response; connect TigerGraph/MCP + LLM in production mode.
    return {
        "case_id": req.case_id,
        "trigger": req.trigger,
        "verdict": "needs_review",
        "fraud_probability": 0.50,
        "next_best_action": "request_evidence",
        "approval_route": "analyst",
        "explanation": "Demo mode. Connect TigerGraph/MCP and the challenge dataset for live graph-backed investigation."
    }
