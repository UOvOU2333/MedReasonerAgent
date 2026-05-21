# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Backend
pip install -r requirements.txt
uvicorn app:app --reload

# Frontend
cd frontend && npm install && npm run dev
npm run build  # production build
npm run lint   # ESLint
```

## Architecture

MedReasonerAgent is a multi-agent biomedical knowledge graph reasoning system. It uses a **LangGraph state graph** to orchestrate a linear pipeline of agents, each mutating a shared `DRGState` TypedDict. The backend is FastAPI; the frontend is Next.js with `@xyflow/react` graph visualization and Zustand state management.

### Agent pipeline (linear DAG)

```
supervisor → entity → medical_report → retrieval → reasoning → ranking → treatment_plan → explain
```

Each agent is a plain function in `agents/` that takes and returns the shared `DRGState` dict. The graph is defined in `graph/workflow.py`; the state schema is in `graph/state.py`.

### Runtime layer (`runtime/`)

- **`EventBus`** — global pub/sub singleton. Nodes emit `node_start`/`node_end` events. The WebSocket endpoint subscribes to it for streaming, and `GET /trace/replay` replays all events.
- **`Executor`** — wraps each node function to emit lifecycle events and snapshot state before/after execution.
- **`DecisionPolicy`** — hardcoded decision options per node (e.g., supervisor can choose `simple`/`multi-hop`/`deep-reasoning`). These are embedded in emitted events for frontend trace visualization.
- **`ModelRouter`** — routes reasoning calls to SGLang (`SGLANG_BASE_URL`) or the default LLM API based on `REASONING_ENGINE` env var.

### Tools (`tools/`)

- **`llm.py`** — OpenAI-compatible client. Falls back to deterministic offline responses when no API key is set, so the pipeline is testable without credentials.
- **`sglang_client.py`** — separate HTTP client targeting an SGLang OpenAI-compatible endpoint for the reasoning agent specifically.
- **`trace.py`** — `append_trace(state, node, output)` appends to `state["trace"]` for end-of-run replay.

### KG layer (`kg/`)

- **`drg_loader.py`** — hardcoded static DRG (Diagnosis Related Group) graph edges (symptom→disease, disease→drg_group, disease→treatment, etc.).
- **`query.py`** — `get_subgraph(entities, hops)` matches extracted entities against the static graph to produce a subgraph for reasoning.

### Frontend (`frontend/`)

Next.js app. Key components:
- `ConversationPanel` — chat input, sends query via REST `POST /run` or WebSocket `WS /ws/run`.
- `AgentGraph` — React Flow canvas rendering the agent DAG with live node status from WebSocket events.
- `TracePanel` / `ReportCard` / `TreatmentCard` — display reasoning trace, medical report, and treatment plan respectively.

State is managed via Zustand (`store/traceStore.ts`); API calls go through `lib/api.ts` and `lib/websocket.ts`.

### Model routing

- Set `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` + `OPENAI_BASE_URL` for LLM-based agents.
- Set `SGLANG_BASE_URL` for SGLang-based reasoning.
- `REASONING_ENGINE=sglang` (default) routes the reasoning node to SGLang; `REASONING_ENGINE=llm` uses the OpenAI-compatible endpoint.
- Without credentials, all agents use deterministic offline responses so the pipeline and UI remain functional.
