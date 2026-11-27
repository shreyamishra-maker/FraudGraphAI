import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = (
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_BACKEND_URL ||
  "https://fraudgraphai-m72y.onrender.com"
).replace(/\/+$/, "");

function percent(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `${(number * 100).toFixed(1)}%` : "—";
}

function money(value) {
  const number = Number(value);
  return Number.isFinite(number)
    ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(number)
    : "Not available";
}

function ActionList({ title, actions }) {
  return (
    <section className="action-section">
      <h4>{title}</h4>
      {actions?.length ? (
        <div className="action">
          {actions.map((action, index) => (
            <article className="item" key={`${action.action || "action"}-${index}`}>
              <div className="action-heading">
                <b>{action.action || "Review required"}</b>
                <span className="route">Approval: {action.approval || action.route || "L2"}</span>
              </div>
              {action.supported === false && (
                <p className="error inline-error">
                  Unsupported action. Manual review is required; this demo does not execute actions.
                </p>
              )}
              <p>{action.reason || "No reason was supplied in the benchmark artifact."}</p>
            </article>
          ))}
        </div>
      ) : <p className="muted">No actions recorded for this stage.</p>}
    </section>
  );
}

function App() {
  const [caseId, setCaseId] = useState("HHG-001");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function investigate(event) {
    event?.preventDefault();
    const normalizedCaseId = caseId.trim().toUpperCase();
    if (!/^HHG-\d{3}$/.test(normalizedCaseId)) {
      setResult({ error: "Enter a valid case ID, for example HHG-001." });
      return;
    }

    setLoading(true);
    setResult(null);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 25000);

    try {
      const response = await fetch(`${API}/investigate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: normalizedCaseId, trigger: "analyst" }),
        signal: controller.signal,
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : `Investigation request failed (HTTP ${response.status}).`
        );
      }
      setResult(data);
    } catch (error) {
      setResult({
        error: error?.name === "AbortError"
          ? "The backend took too long to respond. Please retry."
          : error instanceof Error
            ? error.message
            : "Unable to reach the investigation service. Please try again.",
      });
    } finally {
      window.clearTimeout(timeoutId);
      setLoading(false);
    }
  }

  return (
    <main>
      <section className="hero">
        <div className="badge">TigerGraph HHGOA • Benchmark Demo</div>
        <h1>FraudGraph AI</h1>
        <p>Review recorded evidence, uncertainty, recommendations and provisional approval routes.</p>
      </section>

      <section className="card">
        <form onSubmit={investigate}>
          <label htmlFor="case-id">Benchmark case ID</label>
          <div className="row">
            <input
              id="case-id"
              value={caseId}
              onChange={(event) => setCaseId(event.target.value)}
              placeholder="HHG-001"
              maxLength={7}
              autoComplete="off"
              aria-describedby="case-help"
            />
            <button type="submit" disabled={loading || !caseId.trim()}>
              {loading ? "Loading case…" : "View investigation"}
            </button>
          </div>
          <p id="case-help" className="muted">Available benchmark cases: HHG-001 to HHG-020.</p>
        </form>

        <div aria-live="polite" aria-busy={loading}>
          {loading && <p className="muted" role="status">Loading the recorded case artifact…</p>}

          {result && !result.error && (
            <div className="result">
              <div className="notice" role="note">
                Benchmark artifact replay only. This page does not run live graph queries, recalculate the verdict,
                call an LLM, write to TigerGraph or execute financial actions.
              </div>

              <div className="grid">
                <div><span>Case</span><strong>{result.case_id}</strong></div>
                <div><span>Status</span><strong>{result.case_status || "—"}</strong></div>
                <div><span>Recorded verdict</span><strong>{result.verdict || "—"}</strong></div>
                <div><span>Recorded fraud probability</span><strong>{percent(result.fraud_probability)}</strong></div>
              </div>

              {result.summary && <section><h3>Case summary</h3><p className="body-copy">{result.summary}</p></section>}

              {(result.pattern || result.pattern_description) && (
                <section>
                  <h3>Recorded pattern</h3>
                  <p className="body-copy"><b>{result.pattern || "Not specified"}</b></p>
                  {result.pattern_description && <p className="body-copy">{result.pattern_description}</p>}
                </section>
              )}

              <h3>Recorded evidence ({result.evidence?.length || 0})</h3>
              <div className="evidence">
                {(result.evidence || []).map((item, index) => (
                  <article className="item" key={item.ref || index}>
                    <b>{item.source || "Evidence"}</b>
                    <p>{item.claim || "No evidence description available."}</p>
                    {item.ref && <span className="muted">Reference: {item.ref}</span>}
                  </article>
                ))}
              </div>

              {(result.evidence_requests || []).length > 0 && (
                <>
                  <h3>Pending evidence requests</h3>
                  <div className="evidence">
                    {result.evidence_requests.map((request, index) => (
                      <article className="item" key={`${request.type || "request"}-${index}`}>
                        <b>{(request.type || "Evidence request").replaceAll("_", " ")}</b>
                        <p>{request.assumed_response || request.reason || "Awaiting evidence."}</p>
                      </article>
                    ))}
                  </div>
                </>
              )}

              <h3>Next-best actions</h3>
              <p className="muted">Routes are provisional software labels, not the challenge bank's confirmed approval policy.</p>
              <div className="action-columns">
                <ActionList title="Initial recommendations" actions={result.next_best_action?.initial} />
                <ActionList title="Final recommendations" actions={result.next_best_action?.final} />
              </div>
              {result.next_best_action?.what_changed && (
                <p className="body-copy"><b>What changed:</b> {result.next_best_action.what_changed}</p>
              )}

              <h3>SAR assessment</h3>
              <article className="item">
                <b>{result.sar?.file ? "SAR marked for filing in artifact" : "No SAR marked for filing in artifact"}</b>
                <p>{result.sar?.reason || "No SAR rationale supplied."}</p>
                {result.sar?.narrative && <p>{result.sar.narrative}</p>}
                <span className="muted">Recorded amount: {money(result.sar?.total_amount_usd)}</span>
              </article>

              {result.stop_reason && (
                <section>
                  <h3>Recorded stop reason</h3>
                  <p className="body-copy">{result.stop_reason}</p>
                </section>
              )}

              <h3>Case memory & TigerGraph</h3>
              <article className="item">
                <b>{result.case_memory?.written_to_graph ? "Artifact says graph write completed" : "No graph write recorded"}</b>
                <p>{result.case_memory?.written_to_graph
                  ? `Graph case ID: ${result.case_memory.graph_case_id || "Not supplied"}`
                  : "This demo has not written the case to TigerGraph."}</p>
                <span className="muted">
                  MCP configured: {result.tigergraph?.configured ? "Yes (credentials present)" : "No"} ·
                  Connection verified: {result.tigergraph?.connected ? "Yes" : "No"}
                </span>
              </article>

              <details>
                <summary>View response JSON</summary>
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </details>
            </div>
          )}

          {result?.error && <div className="error" role="alert">{result.error}</div>}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
