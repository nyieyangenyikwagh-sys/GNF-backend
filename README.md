# Canadian Health Claims Platform

FastAPI MVP for Alberta public AHCIP and Green Shield private claims. It includes JWT role access, mock eligibility verification, Alberta PHN/SOMB claim rules, claim status history, appeals, reconciliation, and denial analytics. Health information handling should comply with Alberta's Health Information Act (HIA).

## Local development

The application uses standard PostgreSQL through SQLAlchemy and `psycopg2`; it does not use Supabase.

1. Copy `.env.example` to `.env` and replace `SECRET_KEY`. If you run the API outside Docker, keep the local `DATABASE_URL` from the example.
2. Start the local services and API: `docker compose up --build`.
3. Visit `http://localhost:8000/docs` and run the frontend with `cd rcm-platform-frontend; npm run dev`.

The Compose API service applies `alembic upgrade head` before it starts. To run the API directly after starting PostgreSQL, use `python -m alembic upgrade head` and `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`.

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` in `rcm-platform-frontend/.env.local` only if the frontend is not using that default.

For Railway, supply `DATABASE_URL` using Railway PostgreSQL's connection string, `SECRET_KEY`, `REDIS_URL` (if caching is enabled), and `PORT` (provided by Railway). Run `alembic upgrade head` as a release/pre-deploy step. `pgvector` can later be enabled in this PostgreSQL database for RAG embeddings; no RAG or vector dependency is installed yet.

### Migrating existing Supabase data

Do not delete the Supabase project. Export its PostgreSQL data, review the exported schema against `alembic/versions/0001_initial_schema.py`, load it into the target PostgreSQL database, then mark or apply the Alembic revision as appropriate. Password hashes managed by Supabase Auth require an explicit user-auth migration or password-reset flow; they should not be copied blindly.
