from pathlib import Path
import json
import math
import os
import re
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

load_dotenv()

from .mcp_client import TigerGraphMCPClient
from .policy import allowed

app = FastAPI(
    title="FraudGraph AI — Benchmark Investigation Demo",
    description=(
        "Replays repository benchmark artifacts. Live TigerGraph investigation, "
        "LLM reasoning and financial action execution are not enabled."
    ),
    version="1.2.0",
)

_DEFAULT_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://fraudgraphai-puce.vercel.app",
)
_raw_origins = os.getenv("CORS_ORIGINS")
if _raw_origins and _raw_origins.strip() == "*":
    allowed_origins = ["*"]  # Explicit opt-in only; credentials remain disabled.
elif _raw_origins:
    allowed_origins = [
        value.strip().rstrip("/")
        for value in _raw_origins.split(",")
        if value.strip()
    ]
else:
    allowed_origins = list(_DEFAULT_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

tg = TigerGraphMCPClient()

# Support repository-root execution and the repository-root Docker build.
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
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=7, max_length=7, pattern=r"^HHG-\d{3}$")
    trigger: str = Field(default="analyst", min_length=1, max_length=80)

    @field_validator("case_id", mode="before")
    @classmethod
    def normalize_case_id(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("case_id must be a string")
        return value.strip().upper()

    @field_validator("trigger", mode="before")
    @classmethod
    def normalize_trigger(cls, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("trigger must be a non-empty string")
        return value.strip()


def _finite_number(
    value: Any,
    field_name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool):
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark artifact contains an invalid {field_name}",
        )
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


def _invalid_artifact(case_id: str, detail: str) -> HTTPException:
    return HTTPException(
        status_code=500,
        detail=f"Benchmark case {case_id} has invalid {detail}",
    )


def validate_case_artifact(data: Any, expected_id: str) -> dict[str, Any]:
    """Validate all fields consumed by the API before returning an artifact."""
    if not isinstance(data, dict) or data.get("case_id") != expected_id:
        raise _invalid_artifact(expected_id, "case ID or root structure")

    case = data.get("case")
    if not isinstance(case, dict):
        raise _invalid_artifact(expected_id, "case object")

    valid_status_verdict = {
        "open": "uncertain",
        "closed_fraud": "fraud",
        "closed_legitimate": "legitimate",
    }
    status = case.get("status")
    verdict = case.get("verdict")
    if status not in valid_status_verdict or valid_status_verdict[status] != verdict:
        raise _invalid_artifact(expected_id, "status/verdict combination")

    _finite_number(
        case.get("fraud_probability"),
        "fraud_probability",
        minimum=0,
        maximum=1,
    )
    exposure = _finite_number(case.get("exposure_usd"), "exposure_usd", minimum=0)

    if not isinstance(case.get("summary"), str):
        raise _invalid_artifact(expected_id, "summary")
    evidence = case.get("evidence")
    if not isinstance(evidence, list):
        raise _invalid_artifact(expected_id, "evidence list")
    for index, item in enumerate(evidence):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("claim"), str)
            or not item["claim"].strip()
            or not isinstance(item.get("source"), str)
            or not item["source"].strip()
        ):
            raise _invalid_artifact(expected_id, f"evidence item {index}")

    evidence_requests = data.get("evidence_requests", [])
    if not isinstance(evidence_requests, list) or any(
        not isinstance(item, dict) for item in evidence_requests
    ):
        raise _invalid_artifact(expected_id, "evidence requests")

    actions = data.get("next_best_actions")
    if not isinstance(actions, dict):
        raise _invalid_artifact(expected_id, "next-best-action object")
    for stage in ("initial", "final"):
        items = actions.get(stage)
        if not isinstance(items, list):
            raise _invalid_artifact(expected_id, f"{stage} action list")
        for index, item in enumerate(items):
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("action"), str)
                or not item["action"].strip()
            ):
                raise _invalid_artifact(expected_id, f"{stage} action {index}")
    if not isinstance(actions.get("what_changed", ""), str):
        raise _invalid_artifact(expected_id, "action comparison")

    sar = data.get("sar")
    if not isinstance(sar, dict) or not isinstance(sar.get("file"), bool):
        raise _invalid_artifact(expected_id, "SAR assessment")
    if "total_amount_usd" in sar:
        _finite_number(sar["total_amount_usd"], "SAR total amount", minimum=0)

    if not isinstance(case.get("written_to_graph"), bool):
        raise _invalid_artifact(expected_id, "graph-write flag")
    if not isinstance(case.get("graph_case_id", ""), str):
        raise _invalid_artifact(expected_id, "graph case ID")

    # The value is checked above so it is safe to use for routing below.
    case["exposure_usd"] = exposure
    return data


def load_case(case_id: str) -> dict[str, Any]:
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
    return validate_case_artifact(data, normalized_id)


def _prepare_actions(items: list[dict[str, Any]], exposure: float) -> list[dict[str, Any]]:
    prepared = []
    for item in items:
        decision = allowed(item["action"], exposure)
        prepared.append(
            {
                **item,
                "action": decision["action"],
                "supported": decision["supported"],
                "approval": decision["route"],
                "approval_policy": "provisional_default_not_bank_policy",
            }
        )
    return prepared


@app.get("/")
def root():
    return {
        "service": "FraudGraph AI",
        "status": "ok",
        "mode": "benchmark-artifact-replay",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    available_cases = len(list(CASES_DIR.glob("HHG-*.json"))) if CASES_DIR.is_dir() else 0
    return {
        "status": "ok" if available_cases else "degraded",
        "service": "FraudGraph AI",
        "mode": "benchmark-artifact-replay",
        "available_cases": available_cases,
        "case_store_ready": available_cases > 0,
        "tigergraph_configured": tg.configured(),
    }


@app.get("/tg-status")
def tg_status():
    return {
        "configured": tg.configured(),
        "connected": False,
        "tigergraph": tg.status(),
        "message": "Configuration presence does not verify MCP authentication or graph connectivity.",
    }


@app.get("/case/{case_id}")
def get_case(case_id: str):
    return load_case(case_id)


@app.post("/investigate")
def investigate(req: InvestigationRequest):
    data = load_case(req.case_id)
    case = data["case"]
    actions = data["next_best_actions"]
    exposure = case["exposure_usd"]

    return {
        "case_id": req.case_id,
        "trigger": req.trigger,
        "mode": "benchmark-artifact-replay",
        "workflow": [
            "validate_request",
            "load_benchmark_artifact",
            "review_recorded_evidence",
            "review_recorded_evidence_requests",
            "label_provisional_approval_routes",
            "return_recorded_recommendations",
        ],
        "case_status": case["status"],
        "verdict": case["verdict"],
        "fraud_probability": case["fraud_probability"],
        "pattern": case.get("pattern"),
        "pattern_description": case.get("pattern_description", ""),
        "summary": case["summary"],
        "evidence": case["evidence"],
        "evidence_requests": data["evidence_requests"],
        "next_best_action": {
            "initial": _prepare_actions(actions["initial"], exposure),
            "final": _prepare_actions(actions["final"], exposure),
            "what_changed": actions.get("what_changed", ""),
        },
        "sar": data["sar"],
        "stop_reason": data.get("stop_reason", ""),
        "case_memory": {
            "graph_case_id": case.get("graph_case_id", ""),
            "written_to_graph": case["written_to_graph"],
        },
        "tigergraph": {
            "configured": tg.configured(),
            "graph": tg.graph,
            "connected": False,
            "mcp_status": "not_verified",
        },
        "disclaimer": (
            "This endpoint replays a pre-authored benchmark JSON artifact and applies "
            "provisional approval labels. It does not run live graph queries, "
            "independently calculate the verdict, invoke an LLM, write to TigerGraph, "
            "or execute financial actions."
        ),
    }
