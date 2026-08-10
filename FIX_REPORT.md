# SOGO Style Sentinel - Railway startup fix

## Problem observed
Railway started the container and Alembic initialized PostgreSQL, but startup stopped before Uvicorn. The original startup command ran `alembic upgrade head` before the web server, with no lock/statement timeout. The application also ran `Base.metadata.create_all()` again inside FastAPI startup, creating two competing schema-initialization paths.

## Changes made
1. Added `app/prestart.py` as the single safe database pre-start path.
2. Removed `init_db()` / `create_all()` from FastAPI lifespan; Alembic is now authoritative in production.
3. Added PostgreSQL connection timeout, lock timeout (10s), and statement timeout (60s) so deployment cannot silently hang forever on a database lock/query.
4. Added legacy-schema detection: if all 8 expected tables and all expected columns already exist but `alembic_version` does not, the code stamps the schema at head without dropping tables or rows.
5. Added fail-safe behavior for partial/incompatible unversioned schemas. It stops with a detailed error instead of guessing, deleting, or recreating data.
6. Updated both `Procfile` and `Dockerfile` to run the safe pre-start check before Uvicorn.
7. Added the same lock/statement timeouts inside Alembic's own online migration connection.

## Files changed
- app/prestart.py (new)
- app/main.py
- migrations/env.py
- Procfile
- Dockerfile

## Safety decisions
- No migration file was deleted or rewritten.
- No table-drop or data-delete command was added.
- No credentials/tokens were added or logged.
- Existing complete legacy schemas are only stamped after table + required-column validation.
- Partial schemas fail closed for manual inspection.

## Validation performed
- Python bytecode compilation (`python -m compileall app migrations`) passed.
- Existing pytest suite could not be executed in this sandbox because several project-pinned dependencies are not installed here and package download is unavailable. The original test failure was an environment dependency error (`imagehash` missing), not a test assertion or syntax failure.

## Expected Railway log sequence after deploy
- `Checking PostgreSQL before application startup ...`
- `PostgreSQL connection is healthy.`
- `Schema state: ...`
- either `Alembic stamp completed.` or `Alembic upgrade completed.`
- `Starting SOGO Style Sentinel...`
- Uvicorn startup / application startup complete

If a DB lock is the actual blocker, deployment should now fail within roughly 10 seconds with a visible lock-timeout error instead of hanging indefinitely. That error can then be diagnosed without risking data.
