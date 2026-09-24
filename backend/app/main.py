from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .mcp_client import TigerGraphMCPClient

app=FastAPI(title="FraudGraph AI — Agentic Investigation")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])

tg = TigerGraphMCPClient()

class InvestigationRequest(BaseModel):
    case_id:str
    trigger:str="analyst"

@app.get("/health")
def health():
    return {
        "status":"ok",
        "service":"FraudGraph AI",
        "mode":"mcp-connected",
        "tigergraph":tg.status()
    }

@app.get("/tg-status")
async def tg_status():
    try:
        graphs = await tg.list_graphs()
        return {"connected": True, "tigergraph": tg.status(), "graphs": graphs}
    except Exception as e:
        return {"connected": False, "tigergraph": tg.status(), "error": str(e)}

@app.post("/investigate")
async def investigate(req:InvestigationRequest):
    try:
        graphs = await tg.list_graphs()
        return {
            "case_id":req.case_id,
            "trigger":req.trigger,
            "workflow":["trigger","investigate","gather_evidence","assess_uncertainty","next_best_action","explain","case_memory"],
            "tigergraph_connected": True,
            "available_graphs": graphs,
            "next_best_action":{"action":"RUN_GRAPH_INVESTIGATION","route":"analyst"},
            "message":"TigerGraph MCP connection is active. Investigation execution is the next integration step."
        }
    except Exception as e:
        return {
            "case_id":req.case_id,
            "trigger":req.trigger,
            "tigergraph_connected": False,
            "error": str(e)
        }
