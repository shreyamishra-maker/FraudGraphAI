# FraudGraph AI: A Benchmark Investigation Dashboard for TigerGraph HHGOA

Fraud investigation requires more than a single risk score. An analyst needs to review evidence, understand uncertainty, consider customer impact and follow an approval process.

For the TigerGraph HHGOA agentic fraud-investigation challenge, I built **FraudGraph AI**, a prototype dashboard and FastAPI service for reviewing structured benchmark investigation artifacts.

> **Implementation note:** The current version is a benchmark-artifact replay demo. It does not yet perform live TigerGraph traversals, call an LLM, retrieve GraphRAG context or write cases to TigerGraph. This article distinguishes the working prototype from the planned architecture.

## What works in the current prototype

The repository contains 20 benchmark JSON artifacts (HHG-001 through HHG-020). The analyst dashboard lets a user select a case and review:

- recorded case status and verdict
- recorded fraud probability and pattern
- evidence statements and evidence requests
- initial and final next-best-action recommendations
- deterministic approval routes
- SAR metadata and investigation stop reason
- whether the artifact records a TigerGraph case write

The FastAPI service validates case IDs, checks artifact structure and returns a normalized investigation response. The React/Vite frontend displays that response and labels it as benchmark replay.

## Current request flow

```text
Analyst
  ↓
React / Vite dashboard
  ↓
FastAPI /investigate
  ↓
Validate case ID
  ↓
Load cases/HHG-NNN.json
  ↓
Validate evidence and action structure
  ↓
Apply deterministic approval-route labels
  ↓
Return JSON to dashboard
```

The case JSON files are benchmark answer artifacts. Their contents are not independently recalculated by the API and should not be described as live graph findings.

## Approval routing

A small deterministic policy module assigns approval routes to actions. Low-impact actions such as monitoring and verification can be labelled auto. Customer-impacting or regulated actions—declining a transaction, blocking a card, filing a report and escalating to an analyst—are routed to L2 in this prototype.

This is a conservative demonstration default, not a claim about the challenge bank's official approval matrix. The actual bank policy must be reviewed and encoded before operational use. The policy module only labels routes; it never performs a financial action.

## TigerGraph and MCP integration status

The repository includes a TigerGraph MCP client boundary and draft GSQL query examples for the observed Transaction_Fraud graph. These are integration scaffolding.

At the time of writing:

- MCP authentication has not been verified.
- The API does not run live graph queries during POST /investigate.
- The API does not write InvestigationCase, Evidence or Action vertices.
- The graphrag.py module only shapes supplied context; it does not retrieve graph or document context.
- No external LLM is invoked.

The application intentionally reports this limitation instead of presenting a simulated response as a successful database operation.

## Example benchmark artifact: HHG-001

The HHG-001 artifact records a legitimate-case assessment with a fraud probability of 0.08 and exposure of $77.07. It includes evidence statements about prior billing-region use and in-person history, and recommends CLOSE_NO_FRAUD.

Those are the recorded values in the repository artifact. The current service displays them; it does not independently verify them against the live HHGOA dataset or TigerGraph.

## Engineering safeguards

The prototype includes:

- strict case-ID validation and normalization
- validation of benchmark JSON structure and numeric probability/exposure fields
- explicit handling of missing case files
- conservative L2 routing for high-impact actions
- no raw TigerGraph host or token in the public status response
- configurable CORS origin allow-list
- automated backend regression/API tests and frontend production build

The API remains a public demo and currently has no user authentication or role-based authorization. It must not be connected to real payment operations.

## Planned next steps

To move from benchmark replay to a live investigation system, the next implementation stages are:

1. Read the HHGOA dataset documentation and validate the dataset-to-graph identity mapping.
2. Verify TigerGraph schema and install/test GSQL queries on the target graph.
3. Complete MCP authentication and execute read-only graph queries.
4. Build real GraphRAG retrieval for graph evidence, policy documents and prior closed cases.
5. Add a controlled agent loop with tool-call logging and uncertainty gates.
6. Persist case/evidence/action records with idempotency and audit history.
7. Implement human approval and authorization before any customer-impacting action.
8. Evaluate all 20 benchmark cases against independently reproducible outputs.

## Technology

Python • FastAPI • React • Vite • TigerGraph MCP integration scaffold • Docker • Render • Vercel

## Project

GitHub: https://github.com/shreyamishra-maker/FraudGraphAI
