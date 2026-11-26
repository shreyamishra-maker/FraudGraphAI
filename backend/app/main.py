from pathlib import Path
import json
import math
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .mcp_client import TigerGraphMCPClient
from .policy import allowed

app = FastAPI(
    title="FraudGraph AI — Benchmark Investigation Demo",
    description=(
        "Replays the repository's benchmark case artifacts. "
        "Live TigerGraph investigation and financial action execution are not enabled."
    ),
    version="1.1.0",
)

# Set CORS_ORIGINS to a comma-separated allow-list in the deployment environment.
_default_origins = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "https://fraudgraphai-puce.vercel.app"
)
allowed_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

tg = TigerGraphMCPClient()

# Support both repository-root and Docker application-root layouts.
_here = Path(__file__).resolve()
_case_dirs = (_here.parents[2] / "cases", _here.parents[1] / "cases")
CASES_DIR = next(
    (
        directory
        for directory in _case_dirs
        if directory.is_dir() and any(directory.glob("HHG-*.json"))
    ),
    _case_dirs[-1],
)


class InvestigationRequest(BaseModel):
    case_id: str = Field(min_length=7, max_length=7, pattern=r"^HHG-\d{3}$")
    trigger: str = Field(default="analyst", min_length=1, max_length=80)

    @field_validator("case_id", mode="before")
    @classmethod
    def normalize_case_id(cls, value):
        if not isinstance(value, str):
            raise ValueError("case_id must be a string")
        return value.strip().upper()

    @field_validator("trigger", mode="before")
    @classmethod
    def normalize_trigger(cls, value):
        if not isinstance(value, str):
            raise ValueError("trigger must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("trigger cannot be blank")
        return cleaned


def _finite_number(value, field_name, *, minimum=None, maximum=None):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark artifact contains an invalid {field_name}",
        )
    if not math.isfinite(number):
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark artifact contains an invalid {field_name}",
        )
    if minimum is not None and number < minimum:
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark artifact contains an invalid {field_name}",
        )
    if maximum is not None and number > maximum:
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark artifact contains an invalid {field_name}",
        )
    return number


def load_case(case_id: str):
    normalized_id = case_id.strip().upper()
    if not re.fullmatch(r"HHG-\d{3}", normalized_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid case ID. Use HHG-001 to HHG-020.",
        )

    path = CASES_DIR / f"{normalized_id}.json"
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Benchmark case {normalized_id} not found",
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read benchmark case {normalized_id}",
        ) from exc

    if (
        not isinstance(data, dict)
        or data.get("case_id") != normalized_id
        or not isinstance(data.get("case"), dict)
    ):
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark case {normalized_id} has an invalid structure",
        )

    case = data["case"]
    if "fraud_probability" in case:
        _finite_number(
            case["fraud_probability"],
            "fraud_probability",
            minimum=0,
            maximum=1,
        )
    if "exposure_usd" in case:
        _finite_number(case["exposure_usd"], "exposure_usd", minimum=0)
    if "evidence" in case and not isinstance(case["evidence"], list):
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark case {normalized_id} has invalid evidence",
        )

    actions = data.get("next_best_actions", {})
    if not isinstance(actions, dict):
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark case {normalized_id} has invalid action data",
        )
    for stage in ("initial", "final"):
        items = actions.get(stage, [])
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise HTTPException(
                status_code=500,
                detail=f"Benchmark case {normalized_id} has invalid {stage} actions",
            )

    return data


@app.get("/")
def root():
    return {
        "service": "FraudGraph AI",
        "status": "ok",
        "mode": "benchmark-demo",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    available_cases = (
        len(list(CASES_DIR.glob("HHG-*.json"))) if CASES_DIR.is_dir() else 0
    )
    return {
        "status": "ok" if available_cases else "degraded",
        "service": "FraudGraph AI",
        "mode": "benchmark-demo",
        "available_cases": available_cases,
        "case_store_ready": available_cases > 0,
        "tigergraph": tg.status(),
    }


@app.get("/tg-status")
def tg_status():
    return {
        "connected": False,
        "tigergraph": tg.status(),
        "message": (
            "MCP authentication is not verified; benchmark investigation "
            "runs from repository case artifacts."
        ),
    }


@app.get("/case/{case_id}")
def get_case(case_id: str):
    return load_case(case_id)


@app.post("/investigate")
def investigate(req: InvestigationRequest):
    case_id = req.case_id
    data = load_case(case_id)
    case = data["case"]
    actions = data.get("next_best_actions", {})
    exposure = _finite_number(case.get("exposure_usd", 0), "exposure_usd", minimum=0)

    def prepare_actions(items):
        prepared = []
        for item in items:
            action = str(item.get("action") or "ESCALATE_TO_ANALYST")
            decision = allowed(action, exposure)
            prepared.append(
                {
                    **item,
                    "supported": decision["supported"],
                    "approval": decision["route"],
                }
            )
        return prepared

    return {
        "case_id": case_id,
        "trigger": req.trigger,
        "mode": "benchmark-artifact-replay",
        "workflow": [
            "trigger",
            "load_benchmark_artifact",
            "review_recorded_evidence",
            "review_recorded_uncertainty",
            "validate_action_routes",
            "explain",
            "case_memory_status",
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
            "written_to_graph": bool(case.get("written_to_graph", False)),
        },
        "tigergraph": {
            "configured": tg.configured(),
            "graph": tg.graph,
            "connected": False,
            "mcp_status": "auth-not-verified",
        },
        "demo_note": (
            "This response replays a benchmark JSON artifact and validates action "
            "approval routes. It does not run live graph queries, call an LLM, "
            "or execute financial actions."
        ),
    }
