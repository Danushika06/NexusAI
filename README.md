# 🧠 NexusAI — Academic Wellbeing & Career Co-Pilot

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Project Description](#-project-description)
- [Get Started](#-get-started)
  - [Prerequisites](#prerequisites)
  - [Frontend Setup](#frontend-setup)
  - [Backend Setup](#backend-setup)
  - [Full Stack (Docker)](#full-stack-docker)
- [Contribution](#-contribution)
- [Contact](#-contact)

---

## 🔭 Project Overview

**NexusAI** is an AI-powered academic wellbeing and career co-pilot designed for college students. It combines machine learning–based risk detection with an intelligent agent system to provide holistic student support — from mental wellbeing monitoring and crisis intervention to personalized career guidance.

Counselors get a real-time dashboard with automated alerts, while students interact with empathetic AI agents tailored to their needs.

---

## 📖 Project Description

NexusAI is built around four core pillars:

### 🧩 Wellbeing Monitoring
- **Behavioral Anomaly Detection** — IsolationForest model trained on 7 behavioral features (attendance, sleep, social activity, etc.) to flag unusual patterns.
- **Sentiment Analysis** — DistilBERT-based distress scoring on student messages in real time.
- **Risk Scoring** — Weighted formula (`0.50 × anomaly + 0.35 × sentiment + 0.15 × survey_decline`) producing tiered risk levels: low, moderate, high, and crisis.

### 💬 AI Agent System
- **Orchestrator Agent** — Routes student queries to specialist agents based on risk score and intent.
- **Wellbeing Agent** — Empathetic conversational support calibrated to the student's risk tier.
- **Career Pathway Agent** — Resume parsing, 12-week career roadmap generation, and mock interviews using job market data + RAG-powered resources.
- **Crisis Agent** — Three-signal gate system that auto-creates counselor alerts when thresholds are met.

### 📊 Counselor Dashboard
- Real-time alert feed with risk-tier badges.
- Case notes and resolution workflow.
- Visual analytics: mood history charts, risk gauges, and skill radar charts.

### 🔍 RAG-Powered Resources
- Semantic search over curated academic and career resources using SentenceTransformers + FAISS.
- Domain-filtered retrieval for contextually relevant recommendations.

### Architecture

```
Frontend (:3000) → /api proxy → Backend (:8000) → MCP Servers (:9001-9004)
                                       ↓                    ↓
                                   PostgreSQL (:5432)   PostgreSQL (shared)
                                       ↓
                                 Agents + ML Pipeline
                                       ↓
                              LLM Router (Ollama → Claude Haiku fallback)
```

| Service | Port | Stack |
|---------|------|-------|
| Frontend | 3000 | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | 8000 | FastAPI, SQLAlchemy 2.0, asyncpg |
| Student DB MCP | 9001 | FastAPI microservice |
| Job Market MCP | 9002 | FastAPI microservice |
| Resource RAG MCP | 9003 | FastAPI + FAISS + SentenceTransformers |
| Counselor Alerts MCP | 9004 | FastAPI microservice |
| PostgreSQL | 5432 | PostgreSQL 15 Alpine |

---

## 🚀 Get Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm**
- **uv** (Python package manager) — [Install uv](https://docs.astral.sh/uv/)
- **Docker & Docker Compose** (for full-stack setup)
- **PostgreSQL 15** (if running locally without Docker)

### Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server (runs on http://localhost:3000)
npm run dev

# Production build
npm run build
```

> The Vite dev server proxies all `/api` requests to the backend at `localhost:8000`.

### Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Install dependencies with uv
uv sync

# Copy environment variables
cp ../.env.example ../.env
# Edit .env with your database URL, API keys, etc.

# Run database migrations
uv run alembic upgrade head

# Seed demo data (optional)
uv run python scripts/seed_demo.py

# Start the development server
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Environment variables** (`.env`):
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `SECRET_KEY` | JWT signing key |
| `OLLAMA_BASE_URL` | Remote Ollama server URL |
| `OLLAMA_MODEL` | Ollama model name |
| `ANTHROPIC_API_KEY` | Claude Haiku fallback API key |

### Full Stack (Docker)

The easiest way to run everything together:

```bash
# Start all services (PostgreSQL, backend, 4 MCP servers, frontend)
docker compose up --build

# Stop all services
docker compose down
```

---

## 🤝 Contribution

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit** your changes with clear, descriptive messages
   ```bash
   git commit -m "Add: brief description of your change"
   ```
4. **Push** to your fork
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** against the `main` branch

### Guidelines

- Follow the existing code style and conventions.
- Python: use `uv` as the package manager, async-first patterns, Pydantic v2 schemas.
- Frontend: use the teal-based design system (`#005A70` primary), `lucide-react` for icons.
- Write meaningful commit messages.
- Test your changes before submitting a PR.

---

## 📬 Contact

For any queries or suggestions, feel free to reach out:

📧 **Email:** [danushikanagarajan@gmail.com](mailto:danushikanagarajan@gmail.com)
