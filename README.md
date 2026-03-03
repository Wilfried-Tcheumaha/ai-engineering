# AI Engineering

An end-to-end **multi-service, multi-agent shopping assistant** system built around RAG (Retrieval-Augmented Generation).

At a high level, the **Streamlit UI** talks to a **FastAPI** backend that runs a **LangGraph** agent workflow (Product Q&A / Shopping Cart / Warehouse Manager + a Coordinator). Agents call tools that retrieve **Amazon item metadata** and **Amazon reviews** from **Qdrant**, optionally checkpoint state in **PostgreSQL**, and can also expose retrieval functionality via **MCP servers**. The repository also includes notebook-based work for building, experimenting with, and evaluating these components (prompt caching, routing, tools, and retriever evals).

## Tech Stack

- **Python** 3.12 (managed with [uv](https://docs.astral.sh/uv/))
- **API**: FastAPI, LangGraph, LiteLLM, LangSmith
- **Agents**: Google ADK, A2A SDK, LangGraph checkpointing (PostgreSQL)
- **Vector DB**: Qdrant
- **UI**: Streamlit
- **MCP**: FastMCP (items & reviews servers)

## Project Structure

```
ai-engineering/
├── apps/
│   ├── api/                    # FastAPI backend (agents, RAG, chat)
│   ├── chatbot_ui/             # Streamlit chat interface
│   ├── items_mcp_server/       # MCP server for items (Qdrant)
│   ├── reviews_mcp_server/     # MCP server for reviews
│   ├── a2a_warehouse_manager_agent/   # A2A warehouse agent (port 10001)
│   └── adk_warehouse_manager_agent/   # Google ADK warehouse agent
│   ├── ...                     # Other agent apps
├── notebooks/                  # Weekly learning notebooks
│   ├── week_1/ … week_6/       # RAG, agents, A2A, LangGraph, prompt caching
│   └── prerequisites/
├── scripts/                    # SQL and utility scripts
├── qdrant_storage/             # Qdrant persisted storage (docker-compose volume)
├── postgres_data/              # Postgres persisted storage (docker-compose volume)
├── docker-compose.yml          # Full stack (API, UI, Qdrant, Postgres, MCP servers)
├── pyproject.toml              # Workspace config and dependencies
└── .env                        # API keys and config (create from template below)
```

## Prerequisites

- **Python** 3.12
- **[uv](https://docs.astral.sh/uv/)** for dependency management
- **Docker** and **Docker Compose** (optional, for running the full stack in containers)

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd ai-engineering
uv sync
```

To include dev dependencies (notebooks, LangGraph, ADK, A2A, etc.):

```bash
uv sync --group dev
```

### 2. Environment variables

Create a `.env` file in the project root with at least:

```env
# LLM providers (at least one required for API/notebooks)
OPENAI_API_KEY=your-openai-key
GOOGLE_API_KEY=your-google-key
GROQ_API_KEY=your-groq-key

# Optional: Cohere (for some notebooks/features)
COHERE_API_KEY=

# Optional: LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=rag-tracing
```

Adjust variable names if your apps expect different ones (e.g. `GOOGLE_GENAI_API_KEY`).

### 3. Run with Docker Compose (recommended for full stack)

Starts API, Streamlit UI, Qdrant, PostgreSQL, and both MCP servers:

```bash
make run-docker-compose 
```

### Services & URLs (docker-compose)

| Service | URL / Port | Notes |
|---|---:|---|
| Streamlit Chat UI | `http://localhost:8501` | Chat frontend |
| API | `http://localhost:8000` | FastAPI backend |
| API Docs (Swagger) | `http://localhost:8000/docs` | Interactive docs |
| Qdrant | `http://localhost:6333` | Vector DB |
| PostgreSQL | `localhost:5433` | db `langgraph_db`, user `langgraph_user` |
| Items MCP | `http://localhost:8001` | MCP server for item retrieval |
| Reviews MCP | `http://localhost:8002` | MCP server for review retrieval |

### Warehouse agent services (standalone apps)

| Service | URL / Port | Notes |
|---|---:|---|
| A2A Warehouse Manager Agent | `http://localhost:10001` | Agent base URL |
| A2A Agent Card | `http://localhost:10001/.well-known/agent.json` | Public agent metadata |

### 4. Run locally (without Docker)

Ensure PostgreSQL and Qdrant are running (e.g. via Docker or local install), then:

**API (from repo root):**

```bash
PYTHONPATH=apps/api/src uv run --package api uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

**Streamlit UI:**

```bash
cd apps/chatbot_ui/src && uv run streamlit run chatbot_ui/app.py --server.address=0.0.0.0
```

**A2A Warehouse Manager Agent (standalone):**

```bash
cd apps/a2a_warehouse_manager_agent/warehouse_manager_agent
uv run python app.py   # listens on http://localhost:10001
```

**MCP servers:** run from their app directories using the entrypoints defined in each `pyproject.toml` (e.g. `fastmcp run` or the configured script).

## Notebooks

Jupyter notebooks are organized by week under `notebooks/`:

- **Prerequisites** – environment and tooling
- **Week 1–4** – RAG, embeddings, evaluation, MCP
- **Week 5** – LangGraph and agent workflows
- **Week 6** – LiteLLM router, Warehouse Agent (ADK), A2A agent, A2A + LangGraph, prompt caching

Use the project’s virtual environment as the Jupyter kernel:


## API Overview

The **api** app exposes:

- **Agents**: Product Q&A (RAG), Shopping Cart, Warehouse Manager, and a Coordinator that delegates between them
- **LangGraph** workflows with optional PostgreSQL checkpoints
- **LiteLLM** for multi-provider LLM routing

See `apps/api/src/api/` for routes and agent definitions.

## Prompt Registry

This repo supports **two** ways of managing prompts:

- **Local YAML prompt registry (checked into git)**:
  - Stored under `apps/api/src/api/agents/prompts/`
  - Loaded via `prompt_template_config(...)` in `apps/api/src/api/agents/utils/prompt_management.py`
  - Prompts are **Jinja2 templates** keyed by model name (example keys: `gpt-4.1`, `groq/llama-3.3-70b-versatile`)

- **LangSmith prompt registry (remote)**:
  - Pulled via `prompt_template_registry(prompt_name)` in `apps/api/src/api/agents/utils/prompt_management.py`
  - Useful when you want to iterate on prompts without changing the codebase

## Datasets

- **Raw Amazon Reviews’23 data (source)**:
  - The item metadata and reviews used here are derived from the **Amazon Reviews’23** dataset from McAuley Lab.
  - See the official dataset page for raw JSONL files and documentation: [Amazon Reviews’23 dataset](https://amazon-reviews-2023.github.io/main.html).

- **Amazon item metadata / product catalog (Qdrant)**:
  - **Collection**: `Amazon-items-collection-01-hybrid-search`
  - **Typical payload fields used by the system**:
    - `parent_asin` (item ID)
    - `description` (product metadata text used for RAG)
    - `average_rating`

- **Amazon reviews (Qdrant)**:
  - **Collection**: `Amazon-items-collection-01-reviews`
  - **Typical payload fields used by the system**:
    - `parent_asin` (item ID)
    - `text` (review text)


- **Evaluation dataset**:
  - Stored in **LangSmith** as `rag-evaluation-dataset` (referenced by `apps/api/evals/eval_retriever.py`)
  - The examples are expected to include `reference_context_ids` for ID-based context metrics

## Evaluation Pipeline

Retriever evaluation is implemented in `apps/api/evals/eval_retriever.py` using:

- **LangSmith**: `Client().evaluate(...)`
- **Ragas metrics**:
  - Faithfulness
  - Response Relevancy
  - ID-based Context Precision / Recall


```bash
make run-evals-retriever
```


## References

```bibtex
@article{hou2024bridging,
  title={Bridging Language and Items for Retrieval and Recommendation},
  author={Hou, Yupeng and Li, Jiacheng and He, Zhankui and Yan, An and Chen, Xiusi and McAuley, Julian},
  journal={arXiv preprint arXiv:2403.03952},
  year={2024}
}
```
