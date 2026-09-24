import React,{useState} from "react";
import {createRoot} from "react-dom/client";
import "./style.css";

const API = import.meta.env.VITE_API_URL || import.meta.env.VITE_BACKEND_URL || "https://fraudgraphai-m72y.onrender.com";

function App(){
  const [caseId,setCaseId]=useState("HHG-001");
  const [result,setResult]=useState(null);
  const [loading,setLoading]=useState(false);

  async function investigate(){
    setLoading(true);
    setResult(null);
    try{
      const r=await fetch(API+"/investigate",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({case_id:caseId.trim().toUpperCase(),trigger:"analyst"})
      });
      const data=await r.json();
      if(!r.ok) throw new Error(data.detail || "Investigation failed");
      setResult(data);
    }catch(e){
      setResult({error:e.message});
    }
    setLoading(false);
  }

  return <main>
    <section className="hero">
      <div className="badge">TigerGraph HHGOA • Agentic Investigation</div>
      <h1>FraudGraph AI</h1>
      <p>Graph-grounded investigation, uncertainty assessment and next-best action.</p>
    </section>

    <section className="card">
      <label>Benchmark case ID</label>
      <div className="row">
        <input value={caseId} onChange={e=>setCaseId(e.target.value)} onKeyDown={e=>e.key==="Enter"&&investigate()} />
        <button onClick={investigate} disabled={loading}>{loading?"Investigating…":"Investigate"}</button>
      </div>

      {result && !result.error && <div className="result">
        <div className="grid">
          <div><span>Case</span><strong>{result.case_id}</strong></div>
          <div><span>Status</span><strong>{result.case_status}</strong></div>
          <div><span>Verdict</span><strong>{result.verdict}</strong></div>
          <div><span>Fraud probability</span><strong>{result.fraud_probability}</strong></div>
        </div>

        <h3>Investigation workflow</h3>
        <div className="steps">{result.workflow.map((s,i)=><span key={s}>{i+1}. {s.replaceAll("_"," ")}</span>)}</div>

        <h3>Evidence</h3>
        <div className="evidence">{result.evidence.map((e,i)=><div className="item" key={i}><b>{e.source}</b><p>{e.claim}</p></div>)}</div>

        <h3>Next-best action</h3>
        <div className="action">
          {(result.next_best_action.final || []).map((a,i)=><div key={i}><b>{a.action}</b><span>Approval: {a.approval}</span><p>{a.reason}</p></div>)}
        </div>

        <h3>Case memory</h3>
        <p className="muted">{result.case_memory.written_to_graph ? "Written to graph" : "Graph write pending MCP authentication"}.</p>

        <details><summary>Agent JSON</summary><pre>{JSON.stringify(result,null,2)}</pre></details>
      </div>}

      {result?.error && <div className="error">{result.error}</div>}
    </section>
  </main>
}
createRoot(document.getElementById("root")).render(<App/>);
