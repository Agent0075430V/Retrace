This project exposes REST APIs for Product, AI (lost/found matching), and Users.

Quick developer guide

1) Mock embeddings (fast, no ML deps)

- To enable deterministic mock embeddings (useful for front-end testing and CI), set:

  DEV_USE_MOCK_EMBEDDINGS=True

  The default in this repo is True in settings (for local dev). Mock embeddings derive a small deterministic vector from the uploaded image pixels.

2) Run Celery for async matching

- To enable async matching, set CELERY_ENABLED=True and ensure a broker is available (Redis is recommended).
- Example (PowerShell):

  # Install requirements (in an activated venv)
  python -m pip install -r requirements.txt

  # Start Redis (if you have it installed locally)
  redis-server

  # Start Celery worker
  celery -A Retrace.celery.app worker --loglevel=info

- When Celery is enabled, new lost/found items enqueue a matching task instead of running matching inline.

3) Image-based matching

- If you want real CLIP/Torch embeddings, install torch + clip (requirements.txt lists these). Keep in mind these are large packages and may take time to install.

4) Endpoints overview

- Products: /api/products/
- AI lost/found: /api/ai/lost/ and /api/ai/found/
- Matches: /api/ai/matches/
- Notifications: /api/ai/notifications/
- Users register/token: /users/register/ and /users/token/

If you want, I can now:
- Install CPU torch and run a live image match demo locally.
- Configure Celery and run a demonstration showing async matching with Redis.
- Add API docs and tests.

Tell me which to run next and I will implement it and run the verification steps.
