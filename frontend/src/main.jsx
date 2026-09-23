import React, {useState} from "react";
import {createRoot} from "react-dom/client";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App(){
  const [caseId,setCaseId]=useState("HHG-001");
  const [result,setResult]=useState(null);
  const [loading,setLoading]=useState(false);
  async function investigate(){
    setLoading(true);
    try{
      const r=await fetch(API+"/investigate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({case_id:caseId,trigger:"analyst"})});
      setResult(await r.json());
    }catch(e){ setResult({error:"Backend unavailable"}); }
    setLoading(false);
  }
  return <main>
    <section className="hero"><div className="badge">TigerGraph HHGOA</div><h1>FraudGraph AI</h1><p>Agentic fraud investigation & next-best action</p></section>
    <section className="card">
      <label>Benchmark case ID</label>
      <input value={caseId} onChange={e=>setCaseId(e.target.value)} />
      <button onClick={investigate} disabled={loading}>{loading?"Investigating…":"Investigate case"}</button>
      {result && <pre>{JSON.stringify(result,null,2)}</pre>}
    </section>
  </main>
}
createRoot(document.getElementById("root")).render(<App/>);
