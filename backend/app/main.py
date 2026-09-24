from pathlib import Path
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .mcp_client import TigerGraphMCPClient
from .policy import allowed

app = FastAPI(title="FraudGraph AI — Agentic Investigation")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

tg = TigerGraphMCPClient()
CASES_DIR = Path(__file__).resolve().parents[1] / "cases"


class InvestigationRequest(BaseModel):
    case_id: str
    trigger: str = "analyst"


def load_case(case_id: str):
    path = CASES_DIR / f"{case_id.upper()}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Benchmark case {case_id} not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "FraudGraph AI",
        "mode": "benchmark-demo",
        "tigergraph": tg.status(),
    }


@app.get("/tg-status")
async def tg_status():
    return {
        "connected": False,
        "tigergraph": tg.status(),
        "message": "MCP authentication is not verified; benchmark investigation runs from grounded case artifacts.",
    }


@app.get("/case/{case_id}")
def get_case(case_id: str):
    return load_case(case_id)


@app.post("/investigate")
async def investigate(req: InvestigationRequest):
    data = load_case(req.case_id)
    case = data.get("case", {})
    actions = data.get("next_best_actions", {})
    initial = actions.get("initial", [])
    final = actions.get("final", [])

    initial_actions = []
    for item in initial:
        action = item.get("action", "ESCALATE_TO_ANALYST")
        initial_actions.append({
            **item,
            "approval": allowed(action).get("route", item.get("route", "L2")),
        })

    final_actions = []
    for item in final:
        action = item.get("action", "ESCALATE_TO_ANALYST")
        final_actions.append({
            **item,
            "approval": allowed(action).get("route", item.get("route", "L2")),
        })

    return {
        "case_id": req.case_id.upper(),
        "trigger": req.trigger,
        "workflow": [
            "trigger",
            "investigate",
            "gather_evidence",
            "assess_uncertainty",
            "next_best_action",
            "explain",
            "case_memory",
        ],
        "case_status": case.get("status"),
        "verdict": case.get("verdict"),
        "fraud_probability": case.get("fraud_probability"),
        "pattern": case.get("pattern"),
        "summary": case.get("summary"),
        "evidence": case.get("evidence", []),
        "evidence_requests": data.get("evidence_requests", []),
        "next_best_action": {
            "initial": initial_actions,
            "final": final_actions,
            "what_changed": actions.get("what_changed", ""),
        },
        "sar": data.get("sar", {}),
        "stop_reason": data.get("stop_reason", ""),
        "case_memory": {
            "graph_case_id": case.get("graph_case_id", ""),
            "written_to_graph": case.get("written_to_graph", False),
        },
        "tigergraph": {
            "configured": tg.configured(),
            "graph": tg.graph,
            "mcp_status": "auth-not-verified",
        },
        "demo_note": "Benchmark-grounded investigation artifact; live MCP graph write is pending authentication.",
    }
