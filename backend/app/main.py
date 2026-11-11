from pathlib import Path
import json
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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

# Support both deployment layouts:
# 1) repository root contains /cases (Render Python runtime)
# 2) application root contains /cases (Docker image)
_here = Path(__file__).resolve()
_case_dirs = (_here.parents[2] / "cases", _here.parents[1] / "cases")
CASES_DIR = next(
    (directory for directory in _case_dirs
     if directory.is_dir() and any(directory.glob("HHG-*.json"))),
    _case_dirs[-1],
)


class InvestigationRequest(BaseModel):
    case_id: str = Field(min_length=7, max_length=7, pattern=r"^HHG-\\d{3}$")
    trigger: str = Field(default="analyst", min_length=1, max_length=80)


def load_case(case_id: str):
    normalized_id = case_id.strip().upper()
    if not re.fullmatch(r"HHG-\\d{3}", normalized_id):
        raise HTTPException(status_code=400, detail="Invalid case ID. Use HHG-001 to HHG-020.")

    path = CASES_DIR / f"{normalized_id}.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Benchmark case {normalized_id} not found")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"Unable to read benchmark case {normalized_id}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("case"), dict):
        raise HTTPException(status_code=500, detail=f"Benchmark case {normalized_id} has an invalid structure")
    return data


@app.get("/")
def root():
    return {
        "service": "FraudGraph AI",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    available_cases = len(list(CASES_DIR.glob("HHG-*.json"))) if CASES_DIR.is_dir() else 0
    return {
        "status": "ok",
        "service": "FraudGraph AI",
        "mode": "benchmark-demo",
        "available_cases": available_cases,
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
    case_id = req.case_id.strip().upper()
    data = load_case(case_id)
    case = data["case"]
    actions = data.get("next_best_actions", {})
    exposure = float(case.get("exposure_usd") or 0)

    def prepare_actions(items):
        prepared = []
        for item in items or []:
            action = item.get("action", "ESCALATE_TO_ANALYST")
            decision = allowed(action, exposure)
            prepared.append({
                **item,
                "approval": decision.get("route", item.get("route", "L2")),
            })
        return prepared

    return {
        "case_id": case_id,
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
            "initial": prepare_actions(actions.get("initial", [])),
            "final": prepare_actions(actions.get("final", [])),
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
