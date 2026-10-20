# Claims Engine inventory

Inspection date: 2026-10-19. This document records the repository as inspected and the benchmark controls added in the same change set.

## Runtime and entry point

The benchmark title says NestJS, but this repository is a Python service: FastAPI 0.111.0, Pydantic 2.8.2, SQLAlchemy 2.0.31, Alembic 1.13.2, and Uvicorn 0.30.1. There are no NestJS modules, controllers, or DTOs. The entry point is `app.main:app`; routers under `app/api/v1` are the controller equivalent and Pydantic classes under `app/schemas` are the DTO equivalent.

`Dockerfile` starts Alembic and Uvicorn. `docker-compose.yml` starts API, PostgreSQL 16, and Redis 7. `docker-compose.benchmark.yml` adds the `benchmark` marker, deterministic Rules/Fraud stubs, dependency URLs, short timeouts, and benchmark seed data. Startup order is PostgreSQL/Redis/stub health, migration, seed, API.

## HTTP inventory

All `/api/v1` endpoints except registration and login require a bearer JWT. JWTs are HS256 and now validate expiration, issuer `gnf-claims`, and audience `gnf-api`. Public registration can only create a `claimant`; elevated roles are seeded or provisioned out of band.

| Method/path | Request / response | Authorization |
| --- | --- | --- |
| `POST /api/v1/auth/register` | `UserCreate` / `UserOut` | Public; claimant only |
| `POST /api/v1/auth/login` | OAuth2 form / `Token` | Public |
| `POST /api/v1/patients` | `PatientCreate` / patient and eligibility object | Authenticated; owner assigned to caller |
| `GET /api/v1/patients/{id}` | none / `PatientOut` | Owner or staff read role |
| `POST /api/v1/insurance/verify` | `EligibilityRequest` / `EligibilityResponse` | Patient owner or operational staff |
| `POST /api/v1/insurance/reverify` | same | Patient owner or operational staff |
| `POST /api/v1/claims` | strict `ClaimCreate`; required `Idempotency-Key` / `ClaimOut` | claimant, biller, adjuster, supervisor, admin, service; claimant must own patient |
| `GET /api/v1/claims` | none / list of `ClaimOut` | owners see only their claims; adjuster, supervisor, auditor, admin, service see all |
| `GET /api/v1/claims/{id}` | none / `ClaimOut` | owner or staff; unauthorized IDs are concealed as 404 |
| `PATCH /api/v1/claims/{id}` | strict `ClaimUpdate`; required numeric `If-Match` / `ClaimOut` | owner or write role; final claims immutable; assessment is invalidated and rerun |
| `POST /api/v1/claims/{id}/retry-assessment` | none / `ClaimOut` | adjuster, supervisor, admin, service; failed assessments only |
| `POST /api/v1/claims/{id}/status` | strict `StatusChange` / `ClaimOut` | adjuster/supervisor/admin; approval is supervisor/admin only |
| `GET /api/v1/claims/{id}/audit` | none / ordered `AuditEventOut[]` | staff read roles only; claimant-facing responses do not expose assessment internals |
| `POST /api/v1/appeals` | `AppealCreate` / `AppealOut` | claim owner or operational staff; denied claims only |
| `POST /api/v1/appeals/{id}/resolve?approve=` | query boolean / `AppealOut` | supervisor/admin |
| `POST /api/v1/payments` | `PaymentCreate` / `PaymentOut` | adjuster, supervisor, admin, service |
| `GET /api/v1/analytics/summary` | none / `AnalyticsSummary` | admin/analyst |
| `GET /health` | none / status plus environment marker | Public |

Strict claim input rejects unknown fields. Amounts are positive decimals with at most two decimal places and 12 total digits; lines and text fields have explicit bounds. The global maximum declared request body is 1 MiB. Validation and HTTP errors use `{error: {code, message, details}, correlation_id}`. Claimant claim responses deliberately omit ownership IDs, coverage snapshots, rules results, fraud scores/results, and dependency internals.

## Persistence and transactions

PostgreSQL is mandatory; configuration rejects non-PostgreSQL URLs. Alembic owns the schema. Migration `0002_claims_benchmark_controls` adds ownership, idempotency uniqueness, request hashes, correlation IDs, optimistic versions, assessment snapshots, versioned history, and detailed audit events. A PostgreSQL trigger rejects update or deletion of `audit_logs`.

Claim validation, policy checks, claim/line insertion, initial history, and initial audit insertion are committed as one transaction. Dependency assessment happens only after that durable checkpoint. Every workflow checkpoint is committed, allowing restart recovery. A background recovery loop resumes `PENDING_RULES` and `PENDING_FRAUD` claims. Database write failures roll back the active unit of work.

## State machine

| Current state | Allowed next state(s) | Trigger/actor |
| --- | --- | --- |
| `PENDING_RULES` | `PENDING_FRAUD`, `REVIEW`, `FAILED_ASSESSMENT` | Rules orchestration |
| `PENDING_FRAUD` | `SUBMITTED`, `REVIEW`, `FAILED_ASSESSMENT` | Fraud orchestration |
| `FAILED_ASSESSMENT` | `PENDING_RULES` | service/adjuster/supervisor/admin retry |
| `REVIEW` | `HUMAN_REVIEW`, `SUBMITTED`, `DENIED` | adjuster/supervisor/admin |
| `HUMAN_REVIEW` | `SUBMITTED`, `APPROVED`, `DENIED` | adjuster; approval supervisor/admin only |
| `SUBMITTED` | `APPROVED`, `DENIED`, `PAID` | manual adjudication/payment |
| `APPROVED` | `PAID` | payment |
| `DENIED` | `HUMAN_REVIEW`, `CLOSED` | appeal/manual action |
| `PAID` | `CLOSED` | manual close |
| `CLOSED` | none | terminal |

An edit to a non-final claim is a special domain event: it increments the optimistic version, clears both assessments, records `claim.edited_assessment_stale`, returns to `PENDING_RULES`, and reruns both assessments.

Near-duplicate claims without a shared idempotency key are accepted as distinct records because repeated health services can legitimately share patient, date, code, and amount. Clients must reuse the same key for transport retries; duplicate-domain detection is left to review/rules and is never silently merged.

## Rules and Fraud integration

`app/services/assessment_clients.py` defines version `1.0` request/response contracts. HTTP dependency calls use an environment service token, correlation ID, claim-version idempotency key, explicit timeout, and bounded exponential-backoff retry. Invalid JSON/schema, HTTP failures, and timeouts become `FAILED_ASSESSMENT`; they never default to pass/low risk. A rules failure routes to `REVIEW` with reason codes. High fraud risk routes to `REVIEW`, never rejection. Returned Rules/Fraud model versions are persisted.

If dependency URLs are unset, deterministic in-process adapters support local development. The benchmark Compose override always uses controllable HTTP stubs with success, rule-fail, high-risk, 500, timeout, invalid-body, and slow modes.

## Tests and commands

The repository originally contained an empty `tests/test_health.py`; there was no executable baseline. The new harness is under `claims-benchmark/`, with validation, workflow, authorization, idempotency/concurrency, audit, resilience, integrity, reporting, performance, and external-dataset components.

- Isolated stack/run: `make claims-isolated`, or Compose with both YAML files followed by `python claims-benchmark/run_claims_benchmark.py`.
- Focused fault suite: `make claims-failure`.
- Integrated run: create `claims-benchmark/config.integrated.json` from the example using real service API endpoints, then `make claims-integrated`.

At initial inspection this workstation had neither a Python executable nor Docker on PATH. A workspace-local Python 3.11 runtime was subsequently installed and the implementation/unit suite passed 12 tests. Docker/PostgreSQL remained unavailable, so no isolated or integrated benchmark case is represented as passed. Execution status is recorded in `docs/integration-gaps.md` and generated run reports.
