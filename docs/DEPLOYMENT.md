# Deployment Guide — Waraq AI

Waraq AI is a two-part app: a FastAPI backend (Render) and a React frontend (Netlify).
Documents live in **Qdrant Cloud**; auth is **Clerk**. All keys are BYOK.

## Architecture

```
Browser (Netlify frontend, React + Clerk)
   │  Bearer <Clerk JWT> on REST, ?token= on SSE
   ▼
Render backend (FastAPI, uvicorn)
   │  user_id filter on every query
   ▼
Qdrant Cloud (vector store, chunks tagged with user_id)
```

## 1. Qdrant Cloud

1. Create a free cluster at https://cloud.qdrant.io
2. Copy the cluster **URL** (e.g. `https://xyz.us-east-1-0.aws.cloud.qdrant.io:6333`)
   and the **API key** from the cluster's Access tab.
3. These become `WARAQAI_QDRANT_URL` + `WARAQAI_QDRANT_API_KEY` on Render.

## 2. Clerk (auth)

1. Create an app at https://dashboard.clerk.com
2. **Secret key** (`sk_test_...`) → backend env `WARAQAI_CLERK_SECRET_KEY`.
3. **Publishable key** (`pk_test_...`) → frontend env `VITE_CLERK_PUBLISHABLE_KEY`.
4. In Clerk dashboard → JWT Templates → session token, ensure the `sub` claim
   is the user id (default) — Waraq uses it for tenant isolation.

## 3. Render (backend)

Easiest path: the included `render.yaml` Blueprint.

1. Push this repo to GitHub.
2. Render → New → Blueprint → pick the repo. Render reads `render.yaml`.
3. In the service → Environment, set the `sync: false` vars:
   - `WARAQAI_QDRANT_URL`, `WARAQAI_QDRANT_API_KEY`
   - `WARAQAI_CLERK_SECRET_KEY`
   - `WARAQAI_LLM_API_KEY` (BYOK)
   - `WARAQAI_CORS_ORIGINS` → your Netlify URL (e.g. `https://waraqai.netlify.app`)
   - `WARAQAI_CLERK_AUTHORIZED_PARTIES` → same Netlify URL
4. Note the backend URL, e.g. `https://waraq-ai-backend.onrender.com`.

## 4. Netlify (frontend)

1. Netlify → Add new site → Import from Git → pick the repo.
2. Build settings (from `frontend/netlify.toml`):
   - Base directory: `frontend`
   - Build command: `npm ci && npm run build`
   - Publish directory: `dist`
3. Environment variables:
   - `VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxx`
   - `VITE_API_BASE_URL=https://waraq-ai-backend.onrender.com`
4. After the first deploy, copy the site URL back into Render's
   `WARAQAI_CORS_ORIGINS` + `WARAQAI_CLERK_AUTHORIZED_PARTIES`, then redeploy.

## Env var reference

| Var | Where | Purpose |
|---|---|---|
| `WARAQAI_QDRANT_URL` | Render | Qdrant Cloud cluster URL |
| `WARAQAI_QDRANT_API_KEY` | Render | Qdrant Cloud API key |
| `WARAQAI_CLERK_SECRET_KEY` | Render | Clerk backend secret (JWT verify) |
| `WARAQAI_CORS_ORIGINS` | Render | Allowed frontend origins |
| `WARAQAI_CLERK_AUTHORIZED_PARTIES` | Render | Clerk JWT `azp` allowlist |
| `WARAQAI_LLM_PROVIDER` | Render | deepseek / gemini / openai / anthropic / openrouter |
| `WARAQAI_LLM_API_KEY` | Render | BYOK LLM key |
| `WARAQAI_LLM_MODEL` | Render | Optional LiteLLM model override |
| `VITE_CLERK_PUBLISHABLE_KEY` | Netlify | Clerk frontend key |
| `VITE_API_BASE_URL` | Netlify | Backend URL for fetch/SSE |

## Local dev (unchanged)

```bash
docker compose up -d          # Qdrant
copy .env.example .env        # add WARAQAI_CLERK_SECRET_KEY for auth
uvicorn app.main:app --reload
cd frontend && npm run dev    # Vite proxy → localhost:8000
```
