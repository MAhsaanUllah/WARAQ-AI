# Deployment Guide — Waraq AI

Waraq AI is a two-part app: a FastAPI backend (Hugging Face Spaces) and a React frontend (Netlify).
Documents live in **Qdrant Cloud**; auth is **Clerk**. All keys are BYOK.

## Architecture

``
Browser (Netlify frontend, React + Clerk)
   │  Bearer <Clerk JWT> on REST, ?token= on SSE
   ▼
Hugging Face Space (FastAPI, Gradio)
   │  user_id filter on every query
   ▼
Qdrant Cloud (vector store, chunks tagged with user_id)
``

## 1. Qdrant Cloud

1. Create a free cluster at https://cloud.qdrant.io
2. Copy the cluster **URL** (e.g. https://xyz.us-east-1-0.aws.cloud.qdrant.io:6333)
   and the **API key** from the cluster's Access tab.
3. These become WARAQAI_QDRANT_URL + WARAQAI_QDRANT_API_KEY on your backend.

## 2. Clerk (auth)

1. Create an app at https://dashboard.clerk.com
2. **Secret key** (sk_test_...) → backend env WARAQAI_CLERK_SECRET_KEY.
3. **Publishable key** (pk_test_...) → frontend env VITE_CLERK_PUBLISHABLE_KEY.
4. In Clerk dashboard → JWT Templates → session token, ensure the sub claim
   is the user id (default) — Waraq uses it for tenant isolation.

## 3. Hugging Face Spaces (backend)

Hugging Face Spaces provides 100% free hosting for Gradio apps with no credit card required. You can even set the Space to "Private" for free.

1. Create an account at https://huggingface.co
2. Go to **Spaces** → **Create new Space**.
3. Set a name (e.g. waraq-ai-backend).
4. Select **License**: MIT.
5. Select **Space SDK**: **Gradio** (Blank).
6. Select **Space Hardware**: Free.
7. Under **Visibility**, you can select **Private** (recommended) so your code is hidden.
8. Click **Create Space**.
9. Once created, go to **Settings** → **Variables and secrets** and add these as **Secrets**:
   - WARAQAI_QDRANT_URL (Qdrant URL)
   - WARAQAI_QDRANT_API_KEY (Qdrant API Key)
   - WARAQAI_CLERK_SECRET_KEY (Clerk secret key)
   - WARAQAI_LLM_API_KEY (Your LLM key, e.g. DeepSeek/OpenAI)
   - WARAQAI_CORS_ORIGINS (Your Netlify URL, e.g. https://waraqai.netlify.app)
   - WARAQAI_CLERK_AUTHORIZED_PARTIES (Your Netlify URL)
10. Finally, upload the backend code. You can either push via Git or upload files directly in the "Files" tab.
11. Note the backend URL (e.g. https://yourusername-waraq-ai-backend.hf.space).

## 4. Netlify (frontend)

1. Netlify → Add new site → Import from Git → pick the repo.
2. Build settings (from rontend/netlify.toml):
   - Base directory: rontend
   - Build command: 
pm ci && npm run build
   - Publish directory: dist
3. Environment variables:
   - VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxx
   - VITE_API_BASE_URL=https://yourusername-waraq-ai-backend.hf.space
4. Deploy!

## Env var reference

| Var | Where | Purpose |
|---|---|---|
| WARAQAI_QDRANT_URL | HF Spaces | Qdrant Cloud cluster URL |
| WARAQAI_QDRANT_API_KEY | HF Spaces | Qdrant Cloud API key |
| WARAQAI_CLERK_SECRET_KEY | HF Spaces | Clerk backend secret (JWT verify) |
| WARAQAI_CORS_ORIGINS | HF Spaces | Allowed frontend origins |
| WARAQAI_CLERK_AUTHORIZED_PARTIES | HF Spaces | Clerk JWT zp allowlist |
| WARAQAI_LLM_PROVIDER | HF Spaces | deepseek / gemini / openai / anthropic / openrouter |
| WARAQAI_LLM_API_KEY | HF Spaces | BYOK LLM key |
| WARAQAI_LLM_MODEL | HF Spaces | Optional LiteLLM model override |
| VITE_CLERK_PUBLISHABLE_KEY | Netlify | Clerk frontend key |
| VITE_API_BASE_URL | Netlify | Backend URL for fetch/SSE |
