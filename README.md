# Agent Trader

An AI trading floor where LLM-driven "trader" agents manage simulated portfolios.
The project ships two independent front ends over the same data plus the engine that
drives it:

- **`backend/`** — a FastAPI read-only JSON API, the trading engine/scheduler, a set of
  MCP (Model Context Protocol) stdio servers (accounts, market, push), and SQLite
  persistence.
- **`demo/`** + **`app.py`** — a Gradio dashboard rendered in-process over `backend`.
- **`frontend/`** — a standalone Vite + TypeScript + uPlot single-page app that talks to
  the backend over HTTP.

All surfaces read the same `accounts.db`, so you can run any combination of them.

## Architecture

```
                         ┌──────────────────────────────┐
                         │        backend/ (Python)       │
   trading_floor.py ───▶ │  engine / scheduler            │
   (async loop)          │  traders.py  → LLM agents      │
                         │  market.py   → Massive or sim  │
   MCP stdio servers ──▶ │  accounts.py / database.py     │
   (accounts/market/push)│         │                       │
                         │         ▼                       │
                         │      accounts.db  (SQLite)      │
                         └──────────┬──────────┬───────────┘
                                    │          │
                     read-only JSON │          │ in-process reads
                                    ▼          ▼
                       ┌───────────────┐   ┌──────────────────────┐
                       │ FastAPI        │   │ demo/ + app.py        │
                       │ backend.api    │   │ Gradio dashboard      │
                       │ /api/*  :8000  │   │ :7860                 │
                       └───────┬────────┘   └──────────────────────┘
                               │ /api proxy
                               ▼
                       ┌────────────────────────┐
                       │ frontend/ (Vite SPA)    │
                       │ :5173  → proxies /api    │
                       └────────────────────────┘
```

Key point: **all Python commands run from the repository root**, because the packages
import each other by name (`app.py` → `demo.*` → `backend.*`).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python packaging/runner). Python **3.12** is pinned
  via `.python-version`; uv installs it automatically.
- Node.js **18+** and npm (for the Vite frontend).

## Setup

```bash
# 1. Python environment (from the repo root)
uv sync

# 2. Environment variables
cp .env.example .env      # then fill in the keys you need
```

`.env` is git-ignored. The app runs **fully offline** with only a placeholder
`OPENAI_API_KEY` set — market prices fall back to a built-in simulator when
`MASSIVE_API_KEY` is absent, so you can explore everything without paid API keys. See
`.env.example` for every supported variable and its default.

## Running

### Seed the database

```bash
uv run -m backend.reset      # creates accounts.db with 4 traders: Warren, George, Ray, Cathie
```

### Backend JSON API

```bash
uv run uvicorn backend.api:app --port 8000
```

Endpoints:

| Method & path | Description |
|---|---|
| `GET /api/traders` | List all traders |
| `GET /api/traders/{name}` | One trader: balance, holdings, P/L, transactions, time series |
| `GET /api/traders/{name}/logs?last_n=N` | Recent log entries for a trader |
| `GET /api/market` | Price source (`massive`/`simulator`) and market-open status |

### Frontend SPA (Vite)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 — proxies /api to http://127.0.0.1:8000
npm run build      # production build into frontend/dist/
```

The dev server proxies `/api` to the backend (configured in `frontend/vite.config.ts`),
so start the backend on port 8000 first.

### Gradio dashboard

```bash
uv run python app.py       # http://localhost:7860 (opens a browser automatically)
```

### Trading engine / scheduler

```bash
uv run -m backend.trading_floor
```

Runs the trading loop every `RUN_EVERY_N_MINUTES` (default 60). Set
`RUN_EVEN_WHEN_MARKET_IS_CLOSED=true` to run outside market hours and `USE_MANY_MODELS=true`
to use multiple LLM providers. Live trading decisions require valid model API keys.

## Troubleshooting

- **`OpenAIError: api_key must be set` on import** — the model clients are constructed at
  import time; set at least a placeholder `OPENAI_API_KEY` in `.env`.
- **Frontend shows no data** — start the backend on port 8000 before `npm run dev`; the
  SPA only reaches the API through the Vite `/api` proxy.
- **Gradio shows no data** — run `uv run -m backend.reset` first so `accounts.db` exists.
- **`ModuleNotFoundError: backend` / `demo`** — run Python commands from the repository
  root, not from inside a subfolder.

## Project layout

```
.
├── app.py                # Gradio launcher (demo.ui.create_ui)
├── backend/              # FastAPI API, engine, MCP servers, SQLite persistence
├── demo/                 # Gradio dashboard package (ui.py, util.py)
├── frontend/             # Vite + TypeScript + uPlot SPA
├── pyproject.toml        # uv-managed Python dependencies
├── uv.lock               # pinned dependency versions
├── .python-version       # pinned Python (3.12)
└── .env.example          # documented environment variables
```
