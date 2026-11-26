import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class TigerGraphMCPClient:
    def __init__(self):
        self.host = (os.getenv("TG_HOST") or os.getenv("TIGERGRAPH_HOST") or "").strip()
        self.graph = (
            os.getenv("TG_GRAPHNAME")
            or os.getenv("TIGERGRAPH_GRAPH")
            or "Transaction_Fraud"
        ).strip()
        self.token = (
            os.getenv("TG_API_TOKEN")
            or os.getenv("TIGERGRAPH_TOKEN")
            or ""
        ).strip()

    def configured(self):
        return bool(self.host and self.graph and self.token)

    def status(self):
        # Do not return host URLs or credentials through public status endpoints.
        return {
            "configured": self.configured(),
            "host_configured": bool(self.host),
            "graph": self.graph,
            "mcp": "tigergraph-mcp",
            "authentication": "not-verified",
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
                    arguments={},
                )
                if getattr(result, "isError", False):
                    raise RuntimeError("TigerGraph MCP list_graphs tool returned an error")
                return [
                    getattr(item, "text", str(item))
                    for item in getattr(result, "content", [])
                ]
