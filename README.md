# MedReasonerAgent

A Multi-Agent Biomedical Knowledge Graph Reasoning System with LangGraph orchestration, DRG retrieval, SGLang/LLM reasoning, FastAPI streaming, and React Flow visualization.

## Backend

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

`POST /run` executes the graph and returns the final state. `WS /ws/run` streams events in this shape:

```json
{
  "event": "node_start",
  "node": "reasoning",
  "timestamp": 123,
  "state": {}
}
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE` if the API is not running on `http://localhost:8000`.

## Model Routing

- `OPENAI_API_KEY` enables OpenAI-compatible LLM calls.
- `SGLANG_BASE_URL` routes the reasoning agent to an SGLang OpenAI-compatible endpoint.
- Without model credentials, the project uses deterministic offline responses so the execution chain and UI remain testable.
