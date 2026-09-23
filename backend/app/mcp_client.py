import os
class TigerGraphMCPClient:
    def __init__(self):
        self.host=os.getenv("TG_HOST",""); self.graph=os.getenv("TG_GRAPHNAME","FraudGraph")
        self.token=os.getenv("TG_API_TOKEN","")
    def configured(self): return bool(self.host and self.graph and self.token)
    def status(self): return {"configured":self.configured(),"host":self.host,"graph":self.graph}
