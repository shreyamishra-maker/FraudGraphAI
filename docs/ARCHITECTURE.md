# FraudGraph AI architecture

## Implemented today

The current repository implements a **benchmark-artifact demo**, not a live agentic fraud investigator.

```text
Analyst
  ↓
React / Vite dashboard
  ↓
FastAPI API
  ↓
Validate case ID and benchmark artifact
  ↓
Review recorded evidence, verdict and probability
  ↓
Deterministic approval-route validation
  ↓
Display SAR metadata and graph-write status
```

- The 20 JSON files in cases/ are pre-authored benchmark artifacts.
- FastAPI validates the request and artifact structure before returning a result.
- The policy module labels known actions with conservative approval routes. It does not execute them.
- The dashboard displays artifact evidence and clearly identifies replay mode.
- The TigerGraph MCP client is integration scaffolding. Authentication and live graph queries are not verified.
- graphrag.py is a context-shaping helper only; it does not retrieve documents or graph data.
- No LLM is called and no case is written to TigerGraph by POST /investigate.

## Intended future architecture

The target design is:

Trigger → Live graph retrieval → GraphRAG context → Pattern/risk assessment → uncertainty gate → evidence request → deterministic policy validation → human approval → action execution → case memory.

Each stage must be implemented and independently tested before the project is described as operational. In particular, the live graph schema, query installation, MCP authentication, dataset-to-graph identity mapping, bank policy and case-write semantics must be validated against the challenge environment.

## Safety boundary

The current API is a public demo with no authentication or role-based access control. Do not connect it to real payment operations or use it to make customer-impacting decisions. The approval routes are conservative prototype defaults, not a substitute for the challenge's bank policy.
