# UI Implementation Plan

## Guiding Constraints

- **Trello is kept** for approvals and publish scheduling — the UI surfaces their current state (card counts per list) but does not replicate those flows
- **The UI's job** is: monitoring, triggering, history, log visibility, and client management
- **Backend = FastAPI** wrapping the existing `MultiClientRunner` / `ClientManager` / `ContentOrchestrator` — almost no new business logic
- **Real-time = WebSockets** for log streaming directly from `loguru`
- **History = SQLite** — lightweight, no server needed, fits the existing zero-database setup

---

## Stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend API | FastAPI | Python-native, async, WebSocket built-in, fits codebase perfectly |
| Frontend | React + Tailwind CSS | Component model suits the pipeline/card UI; Tailwind keeps it fast to build |
| Real-time | FastAPI WebSockets | Stream loguru output to browser per-client |
| Persistence | SQLite via SQLAlchemy | Run history, post records, webhook registry later — no infra needed |
| Process management | Uvicorn | Single command to run the whole app |

---

## New File Structure

```
Auto_LinkedIn/
├── api/
│   ├── __init__.py
│   ├── app.py               # FastAPI app + CORS + lifespan
│   ├── routes/
│   │   ├── clients.py       # GET/POST /clients, DELETE /clients/{name}
│   │   ├── workflows.py     # POST /clients/{name}/run/{workflow}
│   │   ├── scheduler.py     # GET/POST /scheduler, per-client jobs
│   │   ├── history.py       # GET /clients/{name}/history
│   │   └── logs.py          # WS /ws/logs/{client_name}
│   ├── models.py            # SQLAlchemy models (RunRecord, PostRecord)
│   └── log_broadcaster.py   # Loguru → WebSocket bridge
│
├── ui/                      # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ClientDetail.tsx
│   │   │   ├── History.tsx
│   │   │   └── Scheduler.tsx
│   │   ├── components/
│   │   │   ├── PipelineBar.tsx      # Research→Trello→Generate→Trello→Publish
│   │   │   ├── LiveLogPanel.tsx     # WebSocket log viewer
│   │   │   ├── ClientCard.tsx       # Dashboard status card per client
│   │   │   ├── RunButton.tsx        # Trigger workflow manually
│   │   │   └── SchedulerTable.tsx
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── db.py                    # SQLite setup, session factory
│
# (all existing files unchanged)
├── main.py
├── client_manager.py
├── multi_client_runner.py
├── orchestrator.py
└── ...
```

---

## Phase 1 — FastAPI Backend
**Effort: ~4–5 days**

Foundation everything else sits on. Pure Python, no frontend yet.

### `api/app.py`
- FastAPI app with lifespan (start/stop MultiClientRunner schedulers)
- CORS configured for local React dev server
- Mount all route modules
- Serve built React app as static files in production

### `api/routes/clients.py`
```
GET    /api/clients                   → list all clients with per-client status summary
POST   /api/clients                   → register new client (creates clients/<name>.env)
GET    /api/clients/{name}            → single client detail + Trello list card counts
DELETE /api/clients/{name}            → remove client env file
POST   /api/clients/{name}/validate   → run validate_setup()
```

### `api/routes/workflows.py`
```
POST /api/clients/{name}/run/{workflow}   → trigger research / process / publish / full
POST /api/run/{workflow}?all=true         → trigger for all clients in parallel
GET  /api/clients/{name}/status           → current run state (idle / running / error)
```

### `api/routes/scheduler.py`
```
GET   /api/scheduler               → all scheduled jobs across clients + next run times
POST  /api/scheduler/{name}/start
POST  /api/scheduler/{name}/stop
PATCH /api/scheduler/{name}        → update timing (research hour, check intervals)
```

### `api/routes/history.py`
```
GET /api/clients/{name}/history   → paginated run + post records from SQLite
GET /api/history                  → cross-client history
```

### `api/routes/logs.py`
```
WS /ws/logs/{client_name}   → stream live log lines to browser for one client
WS /ws/logs/all             → stream all clients' logs with [client] prefix
```

### `api/log_broadcaster.py`
Loguru sink that puts records into an `asyncio.Queue`. WebSocket handler consumes
the queue and pushes to all connected clients. Filtered by `client_name` so each
connection only receives its own client's output.

### `db.py` — SQLite schema
```
RunRecord:  id, client_name, workflow, started_at, finished_at, status, error
PostRecord: id, client_name, topic, linkedin_post_id, published_at, char_count
```
A small hook in `orchestrator.publish_approved_content` writes a `PostRecord`
after each successful LinkedIn post.

### Run the app
```bash
uvicorn api.app:app --reload --port 8000
```

---

## Phase 2 — Core UI: Dashboard + Client Detail
**Effort: ~5–6 days**

### Dashboard (`/`)

One status card per registered client showing current run state, next scheduled run,
and Trello card counts (how many topics/posts are pending approval). Polls
`GET /api/clients` every 30 seconds.

```
┌─ Client status cards ───────────────────────────────────────────┐
│  [Acme Corp]        [TechStart]        [Globex]                 │
│  ● Running          ◌ Idle             ⚠ Error                  │
│  Research: done     Next run: 2h       Config invalid            │
│  Trello: 2 pending  Trello: 0 pending  [Fix →]                  │
│  [Open →]           [Open →]                                    │
│  [+ Add Client]                                                  │
└──────────────────────────────────────────────────────────────────┘

┌─ Next scheduled runs ──────────────────────────────────────────┐
│  09:00 AM  Daily Research     Acme Corp, TechStart              │
│  11:00 AM  Process Approvals  All clients                       │
└──────────────────────────────────────────────────────────────────┘
```

### Client Detail (`/client/:name`)

Visual pipeline bar showing each workflow stage and how many Trello cards are
currently sitting in each list. "Approval pending" stages link directly to the
Trello board — clicking opens Trello in a new tab.

```
┌─ Pipeline ──────────────────────────────────────────────────────┐
│  [Research] ──→ [Trello: Topics] ──→ [Generate] ──→            │
│     done            2 cards               idle                  │
│                 (approval pending)                               │
│  [Trello: Content] ──→ [Publish]                                │
│       1 card               idle                                 │
│                                                                  │
│  [▶ Research]  [▶ Process]  [▶ Publish]  [▶ Full]              │
└──────────────────────────────────────────────────────────────────┘

┌─ Live Logs ──────────────────────────────────── [▼ Auto-scroll] ┐
│  WebSocket feed — real-time loguru output for this client       │
└──────────────────────────────────────────────────────────────────┘
```

The live log panel opens a WebSocket to `/ws/logs/{client_name}` and appends
lines as they arrive. The UI shows state; Trello handles approval action.

---

## Phase 3 — History + Scheduler Views
**Effort: ~3 days**

### History (`/history`)
- Table of all runs and posts from SQLite
- Filter by client, date range, workflow type
- Each published post shows a "View on LinkedIn →" link via the stored post ID

### Scheduler (`/scheduler`)
- Table of all APScheduler jobs across all clients with next run times
- Start / stop per client
- Edit research hour and check intervals inline
- Polls every 60 seconds to keep next-run times current

---

## Phase 4 — Client Management
**Effort: ~2–3 days**

### Add Client (`/clients/new`)

Form that generates `clients/<name>.env`:

```
Client name:     [acme_corp          ]
Target URL:      [https://acmecorp.com]
Industry:        [SaaS               ]
Trello Board ID: [                   ]
... (all required fields)

[Validate & Save]
```

On save: calls `POST /api/clients` then `POST /api/clients/{name}/validate`.
On success: redirects to the new client's detail page.

### Remove Client
Confirmation modal → calls `DELETE /api/clients/{name}` → removes env file.

---

## Phase 5 — Production Packaging
**Effort: ~1–2 days**

- `npm run build` in `ui/` outputs to `ui/dist/`
- FastAPI serves `ui/dist/` as static files at `/`
- Single command runs everything: `uvicorn api.app:app --port 8000`
- Add `start` command to `main.py`: `python main.py start` → launches uvicorn

---

## Timeline Summary

| Phase | Scope | Effort |
|---|---|---|
| 1 | FastAPI backend + SQLite + WebSocket logs | 4–5 days |
| 2 | Dashboard + Client detail + Live logs | 5–6 days |
| 3 | History + Scheduler views | 3 days |
| 4 | Client management (add/remove) | 2–3 days |
| 5 | Production packaging | 1–2 days |
| **Total** | | **15–19 days** |

A working Phase 1 + 2 is usable in roughly a week and covers the
highest-value parts: seeing what's happening and triggering runs manually.

---

## What This UI Does NOT Do (by design)

- Approve topics or content — stays in Trello
- Set publish times — stays in Trello card due dates
- Replace any existing CLI functionality — `main.py` commands remain fully functional

The UI is purely **observe + trigger**.
