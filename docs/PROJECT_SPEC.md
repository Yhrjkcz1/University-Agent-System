# SaiZhiTong Project Specification

Version: 2.0

Updated: 2026-08-05

Scope: development, deployment, testing, and acceptance of the current `main` branch

## 1. Product Scope

SaiZhiTong is a multi-agent assistant for university competition discovery and preparation. It collects a user profile through conversation, retrieves structured competition records, recommends suitable opportunities, explains details, and generates editable Word drafts.

The service is decision support only. Official competition pages and human review remain authoritative.

## 2. Production Architecture

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React, TypeScript, Vite, Ant Design | Chat, library, favorites, authentication, admin UI |
| Backend | FastAPI, Pydantic, Uvicorn | Agent API, auth, data access, downloads, refresh dispatch |
| Agents | MainAgent plus four domain agents | Orchestration, collection, extraction, recommendation, materials |
| Data | Supabase / PostgreSQL | Competitions, users, conversations, portraits, favorites, jobs |
| Jobs | GitHub Actions | Scheduled and manual competition refresh |
| Hosting | GitHub Pages and Render | Static frontend and Python API |

Streamlit and Gradio are compatibility-only local debugging entry points.

## 3. Agent Responsibilities

- **MainAgent**: intent recognition, conversation state, routing, result integration, safe fallback messages.
- **InfoCollectAgent**: source collection, file parsing, URL normalization, change detection, source-level error reporting.
- **InfoExtractAgent**: structured extraction of organizers, dates, categories, levels, URLs, and attachments.
- **RecommendationAgent**: hard filtering, ranking, diversity, reasons, risks, and actionable next steps.
- **MaterialAgent**: target and material selection, editable `.docx` generation, safe error handling, human-review notice.

## 4. Core Flows

```text
Recommendation:
profile completion → Supabase candidates → filter/rank → explanation

Detail follow-up:
conversation reference → selected recommendation → structured details

Material generation:
competition selection → material selection → required inputs → Word download

Database refresh:
GitHub Actions → source crawl → change detection → extraction → Supabase
```

Interactive recommendation requests must not start a synchronous web crawl.

## 5. API Contract

Production entry point: `api.py`.

Key endpoints:

- `GET /`: health check
- `POST /api/agent/run`: one conversation turn
- `GET /api/competitions`: competition library
- `POST /api/competitions/refresh`: dispatch refresh
- `GET /api/competitions/refresh/status`: refresh status
- `/api/auth/*`: registration, login, refresh, logout, profile
- `/api/conversations/*`: conversation persistence
- `/api/saved-competitions/*`: favorites
- `/api/admin/*`: protected administration

Agent request:

```json
{
  "user_input": "I am a third-year computer science student interested in AI competitions.",
  "state_snapshot": {}
}
```

Agent responses must contain `success`, `response`, `state_snapshot`, and `metadata`.

## 6. State and Data Rules

Conversation state must remain JSON serializable and retain the current intent, profile, last recommendations, selected competition, material type, and missing fields.

Competition records should include:

- title and authoritative URL;
- source and source text;
- description and structured summary;
- organizer;
- registration and contest dates;
- category and level;
- extraction and refresh metadata.

Missing values must remain empty or null. Agents must not invent official facts. Date timezone conversion must follow an explicit business rule and must not silently change the official calendar date.

## 7. Database and Deployment

Run the idempotent migrations in this order:

1. `migration.sql`
2. `migration_auth.sql`

The API currently requires `competitions.summary`. A deployment whose database lacks this column is invalid and will return 503 from the competition endpoint.

Frontend deployment uses `.github/workflows/deploy.yml`. Backend deployment uses `render.yaml`. `VITE_API_BASE_URL` must point to the production API, and `ALLOWED_ORIGINS` must contain the actual GitHub Pages or custom-domain origin.

## 8. Security Requirements

- Set a strong production `JWT_SECRET_KEY`.
- Keep service-role keys, database passwords, LLM keys, and GitHub tokens server-side.
- Enforce authentication and role checks for protected routes.
- Do not expose tracebacks, SQL messages, internal paths, or secrets to users.
- Do not log passwords or complete tokens.
- Treat generated documents as potentially sensitive user data.

## 9. Quality Gate

Required commands:

```powershell
python -m pytest tests -q -p no:cacheprovider
Set-Location frontend
npm run build
```

Formal acceptance requires:

- all tests under `tests/` passing;
- a successful frontend production build;
- healthy API and OpenAPI endpoints;
- a 200 response from the real competition library;
- end-to-end checks for auth, recommendation, follow-up, document generation, favorites, and refresh;
- the latest Supabase migrations;
- correct production CORS and API configuration.

## 10. Current Status

Local review on 2026-08-05 found:

- frontend production build: passed;
- backend suite: 158 passed, 9 failed, 3 collection errors;
- Supabase schema: missing `competitions.summary` in the connected environment;
- regressions in date parsing, refresh statistics, and several dialogue flows;
- a placeholder CORS origin in `render.yaml`;
- a large frontend main bundle.

The project is suitable for internal pre-acceptance, but the blocking issues must be resolved before formal acceptance. See `docs/PROJECT_REVIEW_2026-08-05.md` and `docs/ACCEPTANCE_GUIDE_CN.md`.
