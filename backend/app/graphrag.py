"""GraphRAG boundary: retrieve compact graph evidence, policy/typology text and closed-case memory.
The raw transaction table is never sent to the LLM."""
def build_context(graph_context, document_context, case_memory):
    return {"graph_context":graph_context,"document_context":document_context,"case_memory":case_memory}
