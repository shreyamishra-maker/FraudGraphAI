import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class TigerGraphMCPClient:
    def __init__(self):
        self.host = os.getenv("TG_HOST") or os.getenv("TIGERGRAPH_HOST", "")
        self.graph = os.getenv("TG_GRAPHNAME") or os.getenv("TIGERGRAPH_GRAPH", "Transaction_Fraud")
        self.token = os.getenv("TG_API_TOKEN") or os.getenv("TIGERGRAPH_TOKEN", "")

    def configured(self):
        return bool(self.host and self.graph and self.token)

    def status(self):
        return {
            "configured": self.configured(),
            "host": self.host,
            "graph": self.graph,
            "mcp": "tigergraph-mcp"
        }

    def _env(self):
        env = os.environ.copy()
        env["TG_HOST"] = self.host
        env["TG_GRAPHNAME"] = self.graph
        env["TG_API_TOKEN"] = self.token
        return env

    async def list_graphs(self):
        if not self.configured():
            raise RuntimeError("TigerGraph MCP is not configured")
        params = StdioServerParameters(
            command="tigergraph-mcp",
            args=[],
            env=self._env(),
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "tigergraph__list_graphs",
                    arguments={}
                )
                return [getattr(item, "text", str(item)) for item in result.content]
