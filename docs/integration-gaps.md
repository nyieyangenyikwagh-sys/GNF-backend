# Claims Engine integration gaps

Status as of 2026-10-19. “Implemented” means present in code and migrations; it does not mean runtime-verified.

| Section 8 expectation | Status | Evidence / remaining work |
| --- | --- | --- |
| Versioned validated dependency schemas | Implemented | strict Pydantic `RulesDecision` and `FraudDecision`, schema version `1.0` |
| Explicit pending/failure/review states | Implemented | state machine includes `PENDING_RULES`, `PENDING_FRAUD`, `FAILED_ASSESSMENT`, `REVIEW`, `HUMAN_REVIEW` |
| Timeouts and bounded retry | Implemented | configurable timeout and retry count; assessment requests have deterministic idempotency keys |
| Creation idempotency | Implemented | required header, canonical request hash, per-owner unique constraint, race recovery |
| Concurrent-update protection | Implemented | required `If-Match`, row lock, monotonically increasing claim version |
| Correlation and structured errors/log context | Implemented | ingress middleware, dependency propagation, response header, history and audit fields; error envelope is structured |
| Append-only audit | Implemented | audit on creation, assessment, edit and transition; PostgreSQL mutation-blocking trigger |
| Environment service credentials | Implemented/configuration pending | `SERVICE_TOKEN` is environment-only. Real service token has not been supplied |
| No cross-service DB writes | Implemented | Claims accesses only its own SQLAlchemy database. The supplied Fraud PostgreSQL DSN is intentionally not used by Claims |

## Execution gaps

- **Passed — implementation/unit suite:** 12/12 tests passed using the workspace-local Python 3.11 environment. These cover strict claim schemas, dependency contracts, state-machine safety, ownership, idempotent replay, auditor write denial, external mapping determinism, and hand-computed evaluator cases.
- **Could not run — isolated benchmark suites:** Docker/PostgreSQL was unavailable. A runner dry run exited 5 and generated a report classifying the target as unavailable; it did not record a pass.
- **Could not run — integrated suite:** real Rules and Fraud HTTP assessment endpoints/contracts and a service credential are not yet supplied. A Fraud database DSN alone is not an API contract and must remain owned by the Fraud service.
- **Could not run — performance:** requires the benchmark stack. The runner is ready to measure two repetitions at concurrency 1, 5, 10, and 25 with warm-up excluded.
- **Could not run — external dataset ingestion:** the exact upstream generator and Apache-2.0 licence were inspected at commit `2551a1c77275464906f65daabcd6d208b7d33c32`; the adapter and schema mapping are implemented. The generated CSV and a running benchmark stack are still required for the 1,000/10,000-row executions.
- **Not yet validated — deliberately broken Claims build:** dependency fault modes are covered, but the additional mutation test against a deliberately broken Claims service has not run.

These items remain “could not run,” never “passed,” until a dated report under `claims-benchmark/results/` proves otherwise.
