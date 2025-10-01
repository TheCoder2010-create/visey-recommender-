# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project type: Python FastAPI microservice for recommending WordPress resources.

Common commands (Windows PowerShell)
- Create venv and install deps
  ```powershell path=null start=null
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

- Configure environment (examples)
  ```powershell path=null start=null
  # WordPress
  $env:WP_BASE_URL = "https://example.com"            # REQUIRED: your WP site
  $env:WP_AUTH_TYPE = "none"                          # none|basic|jwt
  $env:WP_USERNAME = "apiuser"                        # if basic
  $env:WP_PASSWORD = "{{WP_APP_PASSWORD}}"           # if basic; do not echo
  $env:WP_JWT_TOKEN = "{{WP_JWT_TOKEN}}"             # if jwt; do not echo

  # Caching (auto prefers Redis if available; otherwise SQLite)
  $env:CACHE_BACKEND = "auto"                          # auto|redis|sqlite
  $env:REDIS_URL = "redis://localhost:6379"          # if using redis

  # Service behavior
  $env:TOP_N = "10"
  $env:CONTENT_WEIGHT = "0.6"
  $env:COLLAB_WEIGHT = "0.3"
  $env:POP_WEIGHT = "0.1"
  $env:EMB_WEIGHT = "0.0"                             # >0 to enable embeddings
  ```

- Run the API (reload for dev)
  ```powershell path=null start=null
  uvicorn visey_recommender.api.main:app --host 0.0.0.0 --port 8000 --reload
  ```

- Quick smoke tests
  ```powershell path=null start=null
  # Recommend for a user
  Invoke-RestMethod -Uri "http://localhost:8000/recommend?user_id=123" -Method GET | ConvertTo-Json -Depth 5

  # Record feedback (rating optional 1-5)
  Invoke-RestMethod -Uri "http://localhost:8000/feedback?user_id=123&resource_id=456&rating=5" -Method POST
  ```

- Optional: enable semantic embeddings
  ```powershell path=null start=null
  pip install sentence-transformers
  $env:EMB_WEIGHT = "0.2"  # any >0 enables embeddings if package is installed
  ```

Testing, linting, build
- No test suite or lint configuration is present in this repository. There is no packaging/pyproject setup. If these are added later, update this file with the exact commands.

High-level architecture and flow
- API layer (visey_recommender/api/main.py)
  - FastAPI app exposes:
    - GET /recommend: fetches WordPress user profile and resources, returns ranked items.
    - POST /feedback: upserts (user_id, resource_id, rating) into SQLite for collaborative signals.
- Configuration (visey_recommender/config.py)
  - Reads env vars for WordPress auth, cache backend selection, scoring weights, and paths. Ensures a data/ directory exists for SQLite files.
- WordPress client (visey_recommender/clients/wp_client.py)
  - Async httpx client; supports none/basic/jwt auth via headers or BasicAuth.
  - Normalizes user meta to profile fields (industry, stage, team_size, funding, location).
  - Fetches posts as resources with id, title, link, categories, tags, meta, excerpt.
- Data models (visey_recommender/data/models.py)
  - Pydantic models: UserProfile, Resource, Interaction, Recommendation.
- Feature engineering (visey_recommender/features/engineer.py)
  - Hashing-trick vectorization (numpy) for profiles/resources; cosine similarity utility.
- Recommender (visey_recommender/recommender/baseline.py)
  - Combines:
    - Content-based score: cosine(user_vector, resource_vector) including implicit tokens from past interactions.
    - Simple collaborative score: Jaccard similarity on item-user co-occurrence vs user’s interacted items.
    - Popularity boost: from observed feedback counts/ratings.
    - Optional embedding score: SentenceTransformers profile vs resource title/excerpt if EMB_WEIGHT > 0 and package installed.
  - Final score = weighted sum via CONTENT_WEIGHT, COLLAB_WEIGHT, POP_WEIGHT, EMB_WEIGHT.
  - Explainability: simple heuristics (industry/stage/location matches) or fallback to “similar to your past activity”.
- Popularity service (visey_recommender/services/popularity.py)
  - Aggregates feedback to compute top resources with small rating-based boost.
- Storage
  - FeedbackStore (visey_recommender/storage/feedback_store.py): SQLite DB at data/feedback.db, primary store for interactions that drive collaborative and popularity signals.
  - Cache (visey_recommender/storage/cache.py): Redis or SQLite JSON cache implementation is available; not currently wired into the API calls in this version. If integrated later, prefer Redis when REDIS_URL is set; otherwise fallback to SQLite at data/cache.db.
- Embeddings (visey_recommender/embeddings/semantic.py)
  - Optional helper around SentenceTransformers; raises at init if dependencies missing.

Operational notes
- The WordPress REST API must expose the required user meta; depending on your site, that may require plugins (e.g., ACF to REST API, JWT auth) or Application Passwords. Choose WP_AUTH_TYPE accordingly.
- SQLite files are created automatically under data/; this directory is ensured on startup.
- Cold-start: if a user has no interactions, collaborative scores are zero; ranking is primarily content-based with a popularity boost.

CI/CD and rules
- No CI workflows, CLAUDE/Copilot/Cursor rules were found. This file should be updated if such rules are added.
