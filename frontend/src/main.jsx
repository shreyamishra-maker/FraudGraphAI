import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = (
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_BACKEND_URL ||
  "https://fraudgraphai-m72y.onrender.com"
).replace(/\\/+$/, "");

function App() {
  const [caseId, setCaseId] = useState("HHG-001");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function investigate() {
    const normalizedCaseId = caseId.trim().toUpperCase();
    if (!/^HHG-\\d{3}$/.test(normalizedCaseId)) {
      setResult({ error: "Enter a valid case ID, for example HHG-001." });
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(`${API}/investigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: normalizedCaseId, trigger: "analyst" }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || `Investigation failed (HTTP ${response.status}).`);
      }
      setResult(data);
    } catch (error) {
      setResult({
        error: error instanceof Error
          ? error.message
          : "Unable to reach the investigation service. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <section className="hero">
        <div className="badge">TigerGraph HHGOA • Agentic Investigation</div>
        <h1>FraudGraph AI</h1>
        <p>Graph-grounded investigation, uncertainty assessment and next-best action.</p>
      </section>

      <section className="card">
        <label htmlFor="case-id">Benchmark case ID</label>
        <div className="row">
          <input
            id="case-id"
            value={caseId}
            onChange={(event) => setCaseId(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !loading) investigate();
            }}
            placeholder="HHG-001"
            maxLength={7}
            autoComplete="off"
          />
          <button onClick={investigate} disabled={loading || !caseId.trim()}>
            {loading ? "Investigating…" : "Investigate"}
          </button>
        </div>

        {result && !result.error && (
          <div className="result">
            <div className="grid">
              <div><span>Case</span><strong>{result.case_id}</strong></div>
              <div><span>Status</span><strong>{result.case_status || "—"}</strong></div>
              <div><span>Verdict</span><strong>{result.verdict || "—"}</strong></div>
              <div><span>Fraud probability</span><strong>{result.fraud_probability ?? "—"}</strong></div>
            </div>

            <h3>Investigation workflow</h3>
            <div className="steps">
              {(result.workflow || []).map((step, index) => (
                <span key={step}>{index + 1}. {step.replaceAll("_", " ")}</span>
              ))}
            </div>

            <h3>Evidence</h3>
            <div className="evidence">
              {(result.evidence || []).map((item, index) => (
                <div className="item" key={item.ref || index}>
                  <b>{item.source || "evidence"}</b>
                  <p>{item.claim || "No evidence description available."}</p>
                </div>
              ))}
            </div>

            <h3>Next-best action</h3>
            <div className="action">
              {((result.next_best_action || {}).final || []).map((action, index) => (
                <div key={`${action.action || "action"}-${index}`}>
                  <b>{action.action || "Review required"}</b>
                  <span>Approval: {action.approval || action.route || "L2"}</span>
                  <p>{action.reason || ""}</p>
                </div>
              ))}
            </div>

            <h3>Case memory</h3>
            <p className="muted">
              {result.case_memory?.written_to_graph
                ? "Written to graph"
                : "Graph write pending MCP authentication"}
              .
            </p>

            <details>
              <summary>Agent JSON</summary>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </details>
          </div>
        )}

        {result?.error && <div className="error" role="alert">{result.error}</div>}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
