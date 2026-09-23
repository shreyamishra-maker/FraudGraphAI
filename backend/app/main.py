from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app=FastAPI(title="FraudGraph AI — Agentic Investigation")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
class InvestigationRequest(BaseModel):
    case_id:str
    trigger:str="analyst"
@app.get("/health")
def health(): return {"status":"ok","service":"FraudGraph AI","mode":"dataset-agent"}
@app.post("/investigate")
def investigate(req:InvestigationRequest):
    return {"case_id":req.case_id,"trigger":req.trigger,"workflow":["trigger","investigate","gather_evidence","assess_uncertainty","next_best_action","explain","case_memory"],"next_best_action":{"action":"CONNECT_TIGERGRAPH_MCP","route":"analyst"},"message":"Configure TigerGraph MCP and HHGOA data paths for live graph execution."}
