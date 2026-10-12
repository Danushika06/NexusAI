# NexusAI — Student Wellbeing and Career Co-Pilot

**A multi-agent web platform that scores a student's distress risk from behaviour, chat sentiment and mood surveys, routes each chat message to a wellbeing, career or crisis agent, and alerts a human counselor when the risk is high.**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white) ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white) ![FAISS](https://img.shields.io/badge/FAISS-0467DF?style=flat&logo=meta&logoColor=white) ![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black) ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white) ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

## Overview

College counsellors cannot watch every student, and most students who struggle never walk into the counselling office. NexusAI is a prototype of a safety net around that gap. A student does a short mood check-in and chats with an assistant; the system combines three signals into one risk score, adapts the assistant's reply to that score, and creates an alert on a counselor dashboard when the score or the wording of a message looks serious. The same app also gives career help: resume parsing, a 12-week roadmap, job-market lookups and mock interviews.

Status: a working prototype built as a team project, not a deployed or clinically validated product. Be aware of these limits, which I checked against the code:

- The anomaly model is an IsolationForest trained on synthetic "healthy" data generated in code, not on real student data.
- The job-market server returns mock postings unless LinkedIn credentials are configured, and flags every mock response with `is_mock`.
- The mic button in the chat panel has no handler yet; the `/wellbeing/voice-chat` endpoint exists on the backend.
- The skill radar chart on the career page scores each skill with a deterministic hash of its name, so it illustrates the layout and does not measure skill level.
- This repo has a sibling, `flinders_nexus_ai`, which is the same project with a different model and LLM setup. The differences are listed in the section below.

## Key Features

- **Three-signal risk score** — `ml/risk/scorer.py` computes `0.50 x anomaly + 0.35 x sentiment + 0.15 x survey decline` and maps it to the tiers low (below 0.4), moderate (0.4), high (0.6) and crisis (0.8).
- **Behavioural anomaly detection** — `ml/anomaly/detector.py` runs an IsolationForest (100 trees) on seven normalised features (session gap, survey skip streak, session length, assignment delay, chat initiation frequency, mood trend, login-hour variance). If no saved model exists it trains one on synthetic data and pickles it.
- **Sentiment scoring** — `ml/sentiment/analyzer.py` asks a Groq-hosted `llama-3.3-70b-versatile` to return a distress number between 0 and 1, and returns a neutral 0.5 if the call fails.
- **Message router with a safety bias** — `agents/orchestrator/router_logic.py` matches crisis phrases with word-boundary regexes, drops matches that sit in a fiction context or follow a negation word, and otherwise routes on career or wellbeing keywords and risk level.
- **Crisis path with counselor alert** — `agents/crisis/agent.py` decides with a multi-tier `is_crisis()` gate, posts an alert to the counselor-alerts server with up to three retries, and answers with a helpline-aware prompt. If the alert cannot be created, the prompt tells the student to contact support directly.
- **Escalation detection** — the orchestrator forces the crisis agent if the risk tier jumps two or more tiers between turns.
- **LLM router with fallback** — `agents/llm/__init__.py` tries Groq first, then a remote Ollama server, with a five-minute circuit breaker per provider and a canned message if both fail.
- **Career tools** — resume upload (PyPDF2 plus spaCy, with a keyword fallback), roadmap generation, job-opening lookup, and a five-question multi-turn mock interview kept in memory.
- **RAG over curated resources** — `rag/` embeds 38 seed resources (courses, government schemes, career guides, wellbeing and helpline entries) with fastembed `BAAI/bge-small-en-v1.5` and searches them in a FAISS inner-product index.
- **Counselor workflow** — alert feed (auto-refresh every 30 seconds), case notes, case resolution, and anonymous notifications to students.
- **Auth and hardening** — JWT access and refresh tokens with rotation and a revoked-token table, role checks for student, counselor and admin, slowapi rate limits, a CORS allow-list, an Origin check on state-changing requests, and a startup check that refuses a default or short `SECRET_KEY`.

## How It Works

```
Frontend (:3000, nginx) --/api--> Backend FastAPI (:8000) --HTTP--> MCP-style servers (:9001-9004)
                                       |                                   |
                                  PostgreSQL <-------------------------- PostgreSQL
                                       |
                       Orchestrator -> Wellbeing | Pathway | Crisis agent
                                       |
                              LLM router: Groq -> Ollama
```

**Chat turn** (`POST /wellbeing/chat` in `backend/src/wellbeing/router.py`):

1. The router restores the last 10 stored turns into the in-memory `ContextStore` if the process has none.
2. `OrchestratorAgent.process` fetches the last 7 days of behaviour from the student-db server, scores anomaly and sentiment, and computes the risk.
3. `route()` picks `crisis`, `pathway` or `wellbeing`. Escalation and the `is_crisis()` gate can override it to `crisis`.
4. The chosen agent calls the LLM router with a system prompt tuned to the risk tier. The turn is saved to `chat_messages`.
5. If the risk score is 0.6 or higher and there is no unresolved alert for that student in the last 15 minutes, the router inserts a `counselor_alerts` row.

**Mood survey** (`POST /wellbeing/survey`): three 1-10 sliders plus optional free text. The backend stores the survey, scores anomaly from the latest behaviour log, sentiment from the free text, and survey decline against up to three previous surveys, then stores a `wellbeing_alerts` row at 0.4 or above and a counselor alert at 0.6 or above.

**Career roadmap** (`POST /pathway/generate-roadmap`): the Pathway agent asks the job-market and RAG servers for context and prompts the LLM. If the LLM router returns its canned fallback message, `_build_template_roadmap` builds a fixed 12-week template based on the role. Template weeks are then filled with RAG resources.

**The "MCP servers"** in `mcp-servers/` are four small FastAPI services exposing `POST /tools/<name>` endpoints (student-db, job-market, resource-rag, counselor-alerts). They are called over plain HTTP by the backend; they do not implement the Model Context Protocol itself.

**Database**: tables are created at startup with `Base.metadata.create_all`, and an Alembic migration (`001_initial_schema.py`) also exists. Models cover users, revoked tokens, students, behaviour logs, mood surveys, wellbeing alerts, chat messages, skill profiles, career roadmaps, counselor alerts, case notes and notifications.

### How this repo differs from flinders_nexus_ai

Both repos hold the same project. I compared them file by file: the frontend, the agent logic, the routers, the models, the migrations and the tests are byte-identical, and 13 code and config files plus the README and `.env.example` differ. This copy is the lightweight variant:

| Area | NexusAI (this repo) | flinders_nexus_ai |
| ---- | ------------------- | ----------------- |
| Sentiment | Groq API call | local DistilBERT SST-2 model |
| Speech to text | Groq `whisper-large-v3-turbo` API | local Whisper `small` |
| Embeddings | fastembed `bge-small-en-v1.5` | sentence-transformers `all-MiniLM-L6-v2` |
| LLM order | Groq, then Ollama | Ollama (3 s timeout), then Groq |
| Heavy dependencies | none (no PyTorch) | torch, transformers, sentence-transformers, openai-whisper |
| Docker | memory limits per service, Postgres tuned small | no limits; `uv.lock` is copied into the build |
| Extras | none | `.codesandbox/` bootstrap for a CodeSandbox DevBox |

The docstrings in this repo say the Groq sentiment analyzer "replaces local DistilBERT" and fastembed "replaces sentence-transformers", so I read this copy as the later, lighter version of the same codebase.

## Results / Highlights

The repo contains no model evaluation, so I am not reporting accuracy figures. What it does contain as tests:

- **Backend** (`backend/tests/`, 47 test functions): password hashing and JWT claims, the risk scorer's tiers and clamping, crisis-keyword matching including the fiction and negation filters, and the router's routing decisions.
- **Frontend** (`frontend/src/tests/`): the auth store and the radar-chart hash helper, using Vitest.
- **CI** (`.github/workflows/ci.yml`): backend tests, the scorer and router tests, a frontend type-check and unit tests, and a Docker build check on push.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2 (async) with asyncpg, Alembic, Pydantic v2, python-jose and passlib for auth, slowapi, httpx
- **ML / NLP:** scikit-learn (IsolationForest), spaCy, PyPDF2, fastembed, FAISS (`faiss-cpu`), aiosqlite for the resource store
- **LLMs:** Groq (`llama-3.3-70b-versatile`, Whisper), Ollama (`gpt-oss` model name by default)
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, React Query, Zustand, Axios, Recharts, lucide-react, Vitest
- **Infra:** Docker Compose (PostgreSQL 15, backend, four tool servers, nginx frontend), GitHub Actions, uv

## Getting Started

### Prerequisites
- Docker and Docker Compose for the full stack, or Python 3.11+, uv, Node.js 20 and PostgreSQL 15 to run pieces locally
- A Groq API key. The backend settings read `GROQ_API_KEY`, but `.env.example` in this copy lists `ANTHROPIC_API_KEY` instead, so add `GROQ_API_KEY` to your `.env` by hand. Without it, sentiment stays at the neutral 0.5 and the LLM falls through to Ollama.
- An Ollama server reachable at `OLLAMA_BASE_URL` (the default in `backend/src/config.py` is a private network address that will not exist on your machine)

### Installation
```bash
git clone https://github.com/Danushika06/NexusAI.git
cd NexusAI
cp .env.example .env
# set SECRET_KEY (32+ characters), GROQ_API_KEY and OLLAMA_BASE_URL in .env
python -c "import secrets; print(secrets.token_hex(32))"
```

### Running with Docker
```bash
docker compose up --build
docker compose exec backend uv run python scripts/seed_demo.py   # optional demo accounts
```
The frontend is on http://localhost:3000, the API on http://localhost:8000 (docs at `/docs`). The backend image only copies `src/`, so `docker-compose.yml` mounts `agents/`, `ml/`, `rag/` and `shared/` as volumes: run compose from the repo root.

### Running locally
```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

cd ../frontend
npm install
npm run dev     # http://localhost:3000, proxies /api to localhost:8000
```
The four tool servers also need to be running (ports 9001-9004) for behaviour data, alerts, job data and resource search. On first start the backend builds the FAISS index from the seed list in `rag/scripts/build_index.py`.

### Tests
```bash
cd backend && uv run pytest tests/ -v
cd frontend && npm run test:unit:run
```

## Usage

Register as a student or a counselor, then:

| Role | Page | What it does |
| ---- | ---- | ------------ |
| Student | `/dashboard` | mood history chart, risk gauge, behaviour signals |
| Student | `/mindbridge` | mood check-in sliders and the wellbeing chat |
| Student | `/pathway` | resume upload, roadmap, job openings, career chat |
| Counselor | `/counselor` | alert feed, case notes, resolve cases |

The dashboard falls back to hard-coded demo mood and behaviour data when the API returns none, and it reads `behavior` and `streak_days` while the backend returns `latest_behavior` and `login_streak`, so the behaviour panel currently shows the demo values.

### Backend API

| Method | Route | Role | Purpose |
| ------ | ----- | ---- | ------- |
| POST | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout` | public / user | account and token management |
| GET | `/auth/me` | user | current user |
| POST / GET | `/students/profile`, `/students/me` | student | profile |
| GET | `/students/dashboard`, `/students/mood-history` | student | dashboard data, 30-day mood history |
| POST | `/students/behavior-log` | student | store the seven behaviour signals |
| POST | `/wellbeing/survey` | student | submit mood check-in, returns risk result |
| POST | `/wellbeing/chat` | student | orchestrated chat turn |
| POST | `/wellbeing/voice-chat` | student | audio upload, transcribe, then chat |
| GET | `/wellbeing/risk/{student_id}` | counselor | latest stored risk alert |
| POST | `/pathway/resume` | student | parse a resume into skills |
| POST | `/pathway/generate-roadmap` | student | 12-week roadmap |
| POST | `/pathway/job-openings` | student | job lookup via the job-market server |
| GET | `/pathway/mock-interview/{role}` | student | one interview question |
| POST | `/pathway/mock-interview/start`, `/pathway/mock-interview/answer` | student | multi-turn mock interview |
| GET | `/pathway/profile` | student | skill profile |
| GET | `/counselor/alerts` | counselor | alert feed (`threshold` query parameter) |
| POST | `/counselor/notes`, `/counselor/resolve` | counselor | case notes, resolve an alert |
| GET / POST | `/counselor/notifications`, `/counselor/notifications/read` | student | anonymous resolution notices |
| GET | `/health` | public | health check |

## Project Structure

```
NexusAI/
├── backend/                  # FastAPI app
│   ├── src/                  # auth, students, wellbeing, pathway, counselor modules (router, service, models, schemas)
│   ├── alembic/              # initial schema migration
│   ├── scripts/seed_demo.py  # demo students and counselor via the HTTP API
│   └── tests/                # auth, risk scorer, router logic tests
├── agents/                   # orchestrator, wellbeing, pathway, crisis agents, LLM router, interview store
├── ml/                       # anomaly (IsolationForest), sentiment, risk scorer, speech transcriber
├── rag/                      # embedder, FAISS indexer, retriever, SQLite resource store, build_index.py
├── mcp-servers/              # student-db, job-market (with mock data), resource-rag, counselor-alerts
├── frontend/                 # React + TypeScript app (pages, charts, chat panel, API clients, tests)
├── docs/NexusAI-Overview.md  # project write-up
├── docker-compose.yml        # postgres, backend, 4 tool servers, frontend
└── .github/workflows/ci.yml  # tests and Docker build check
```

---

## Contact

<table>
  <tr><td><b>GitHub:</b> <a href="https://github.com/Danushika06">Danushika06</a></td><td><b>LinkedIn:</b> <a href="https://www.linkedin.com/in/danushika-n-323b4628b/">danushika-n</a></td></tr>
  <tr><td colspan="2" align="center"><b>Email:</b> <a href="mailto:danushikanagarajan@gmail.com">danushikanagarajan@gmail.com</a></td></tr>
</table>

Built by **Danushika N**
