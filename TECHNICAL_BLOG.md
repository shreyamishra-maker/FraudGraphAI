# FraudGraph AI: Building an Agentic Fraud Investigation System with TigerGraph

Fraud investigation is rarely about a single suspicious transaction. Investigators need to connect transactions with customers, cards, devices, identities, merchants, previous cases, policy rules, and supporting evidence before deciding what should happen next.

For the TigerGraph HHGOA Agentic Investigation challenge, I built **FraudGraph AI**, a graph-grounded investigation workflow that combines TigerGraph, GraphRAG, policy-driven actions, case memory, and an analyst dashboard.

## 1. What I Built

FraudGraph AI follows an investigation loop:

**Trigger → Investigate → Gather Evidence → Assess Uncertainty → Next Best Action → Explain → Case Memory**

The system is designed around three core requirements:

1. Ground investigation in connected evidence rather than only LLM-generated reasoning.
2. Separate fraud/risk assessment from the final action decision.
3. Make the recommended action explainable and subject to an explicit approval route.

The application supports benchmark case IDs and produces structured investigation output including:

- case status and verdict
- fraud probability
- fraud pattern assessment
- evidence and evidence sources
- controlled evidence requests
- initial and final next-best actions
- approval route
- SAR decision information
- investigation stop reason
- case-memory state

## 2. Architecture

The main architecture is:

```
                  ┌─────────────────────┐
                  │   Analyst / Trigger │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Investigation Agent │
                  │  Reason + Tool Use  │
                  └──────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌──────────────┐
       │ TigerGraph │ │  GraphRAG  │ │ Case Memory  │
       │   Graph    │ │  Boundary  │ │ / History    │
       └─────┬──────┘ └─────┬──────┘ └──────┬───────┘
             │              │               │
             └──────────────┼───────────────┘
                            ▼
                   ┌─────────────────┐
                   │ Risk + Pattern  │
                   │   Assessment    │
                   └────────┬────────┘
                            ▼
                   ┌─────────────────┐
                   │ Uncertainty     │
                   │     Gate        │
                   └────────┬────────┘
                            ▼
                   ┌─────────────────┐
                   │ Policy Engine   │
                   │ + Next Action   │
                   └────────┬────────┘
                            ▼
                   ┌─────────────────┐
                   │ Explanation +   │
                   │ Case Update     │
                   └─────────────────┘
```

The important design decision is that the LLM is not treated as the fraud analytics engine. The graph and deterministic policy layer provide structured evidence and action constraints; the agent synthesizes that context and orchestrates the investigation.

## 3. How TigerGraph Is Used

TigerGraph is the relationship layer of FraudGraph AI.

The graph contains entities such as:

- Payment_Transaction
- Card
- Device
- Party
- Merchant
- Merchant_Category
- Identity-related entities
- InvestigationCase
- Evidence
- Action

The investigation model also includes explicit case relationships:

- Case_Evidence
- Case_Action
- Case_Transaction
- Case_Card
- Case_Device
- Case_Party

This allows an investigation to represent not only the suspicious transaction, but also the evidence and actions associated with the case.

For example, an investigation can conceptually move from:

**Transaction → Card → Customer/Party → Device → Other Transactions → Case History**

rather than treating every record as an isolated row.

TigerGraph is also where graph-oriented investigation queries and analytics belong. This keeps relationship traversal and graph analysis outside the LLM.

## 4. GraphRAG Boundary

FraudGraph AI uses a GraphRAG boundary to keep the LLM context compact and grounded.

The context is divided into:

- graph context
- policy/document context
- case-memory context

The raw transaction table is not simply dumped into the LLM. Instead, the agent should receive the relevant evidence extracted through graph/query operations.

This design follows the broader principle that graph retrieval and semantic retrieval solve different problems: graph retrieval provides connected relationship context, while semantic retrieval can provide relevant policy or document context. TigerGraph describes this combination as a foundation for agentic, relationship-aware reasoning. 

## 5. TigerGraph MCP

The project also includes a TigerGraph MCP client boundary.

The intended production flow is:

```
Agent
  ↓
MCP Client
  ↓
TigerGraph MCP
  ↓
TigerGraph
  ↓
Graph Queries / Analytics
  ↓
Agent Context
```

MCP provides a controlled interface for exposing graph capabilities to the agent.

During the benchmark/demo phase, live MCP authentication was not fully verified, so the application does **not** pretend that a live graph write succeeded. Instead, the demo uses grounded benchmark artifacts while clearly exposing the live-MCP status.

That distinction is important for trustworthy agentic systems: a simulated or benchmark-grounded result should never be presented as a live database operation when it was not actually performed.

## 6. Policy and Next-Best Action

A major part of the system is the policy boundary.

The agent does not directly invent an operational action. Candidate actions are passed through a deterministic policy layer that assigns an approval route.

Examples include:

- CLOSE_NO_FRAUD
- MONITOR_CARD
- MONITOR_CONNECTED_CARDS
- VERIFY_WITH_CUSTOMER
- STEP_UP_AUTH
- GENERATE_REPORT
- CREATE_CASE
- ESCALATE_TO_ANALYST
- DECLINE_TRANSACTION
- BLOCK_CARD

The system distinguishes automated actions from actions requiring an approval level.

This creates a simple control boundary:

**Agent reasoning → Policy validation → Approval route → Action**

The result is easier to audit than allowing an LLM to directly execute unrestricted actions.

## 7. Benchmark Case: HHG-001

For the benchmark demonstration, the dashboard investigates case **HHG-001**.

The current benchmark artifact reports:

- Status: closed_legitimate
- Verdict: legitimate
- Fraud probability: 0.08
- Flagged transaction: 3514030
- Customer: C12382
- Risk score: 0.61
- Transaction amount: $77.07
- Next-best action: CLOSE_NO_FRAUD
- Approval route: auto

The investigation evidence includes prior billing-region usage, extensive in-person history, and available prior-case memory.

The important point is that the 0.61 risk score is treated as an input signal, not as the final verdict. The final decision is based on the broader evidence represented by the investigation artifact.

## 8. Case Memory

Fraud investigations should not start from zero every time.

FraudGraph AI models investigation memory using:

**InvestigationCase → Evidence / Action / Transaction / Card / Device / Party**

This makes it possible to preserve:

- what triggered the case
- what evidence was gathered
- what actions were considered
- what action was taken
- why the action was taken
- what should be remembered for future investigations

The long-term goal is to write completed cases back into TigerGraph so future investigations can use prior case patterns as connected context.

## 9. Analyst Dashboard

The frontend provides a simple investigation console.

The analyst enters a benchmark case ID and selects **Investigate**.

The dashboard then shows:

1. Case status
2. Verdict
3. Fraud probability
4. Investigation workflow
5. Evidence
6. Next-best action
7. Approval route
8. Case-memory status
9. Structured agent JSON

This makes the agent's process visible rather than presenting only a final sentence.

## 10. Deployment

FraudGraph AI is split into:

- **Frontend:** Vite/React dashboard deployed on Vercel
- **Backend:** FastAPI service deployed on Render
- **Graph:** TigerGraph Savanna / Transaction_Fraud
- **Repository:** GitHub
- **Agent integration boundary:** TigerGraph MCP
- **Retrieval boundary:** GraphRAG

The backend exposes endpoints for health, case retrieval, TigerGraph status, and investigation execution.

## 11. Results

The implementation successfully demonstrates an end-to-end benchmark investigation workflow:

**Case trigger → evidence → uncertainty assessment → policy-controlled next action → explanation → case memory**

The HHGOA benchmark artifacts provide structured outputs for the benchmark cases, while the dashboard turns those outputs into an analyst-facing investigation experience.

For HHG-001, the demonstrated result is a legitimate-case assessment with a fraud probability of 0.08 and an automated CLOSE_NO_FRAUD action.

The project also keeps the distinction between benchmark/demo behavior and live MCP graph operations explicit. Live graph writes remain dependent on successful MCP authentication and connection.

## 12. What I Learned

The biggest architectural lesson was that an agent should not be responsible for everything.

A reliable fraud investigation agent needs separate responsibilities:

**Graph:** relationships and graph analytics  
**GraphRAG:** grounded context retrieval  
**Agent:** reasoning, planning, and tool selection  
**Policy engine:** action constraints and approval routing  
**Case memory:** investigation history  
**UI:** analyst visibility and explainability

This separation makes the system easier to debug, easier to audit, and safer to extend.

## 13. Future Improvements

The next iteration would focus on:

- completing live TigerGraph MCP authentication
- writing InvestigationCase, Evidence, and Action records directly to the graph
- improving HHGOA identity/card/transaction relationship mapping
- executing graph-based fraud-pattern queries on every benchmark case
- adding richer graph visualizations
- comparing initial versus final next-best action after additional evidence
- adding production-grade authentication and role-based permissions

## Conclusion

FraudGraph AI demonstrates how a graph can become the grounding and memory layer for an agentic fraud investigation workflow.

Instead of asking an LLM to decide from a flat transaction record, the architecture gives the agent access to connected evidence, case history, policy constraints, uncertainty handling, and explicit action routes.

The result is a workflow designed around a simple principle:

**Investigate with connected evidence. Decide with controlled policies. Explain with traceable context.**

### Project

GitHub: https://github.com/shreyamishra-maker/FraudGraphAI

### Technology

TigerGraph • TigerGraph MCP • GraphRAG • FastAPI • React/Vite • Python • Docker • Vercel • Render
