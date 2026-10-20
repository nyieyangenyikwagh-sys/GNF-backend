import time
from typing import Callable, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.request_context import correlation_id
from app.schemas.claim import FraudDecision, RulesDecision
from app.services.rule_engine import ClaimContext, run_rules


class AssessmentUnavailable(RuntimeError):
    pass


T = TypeVar("T", bound=BaseModel)


def _headers(claim_id: int, claim_version: int) -> dict[str, str]:
    headers = {
        "X-Correlation-ID": correlation_id(),
        "Idempotency-Key": f"claim-{claim_id}-v{claim_version}",
    }
    if settings.SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {settings.SERVICE_TOKEN}"
    return headers


def _post(url: str, payload: dict, schema: type[T], claim_id: int, claim_version: int) -> T:
    if not settings.SERVICE_TOKEN:
        raise AssessmentUnavailable("service credential is not configured")
    last_error: Exception | None = None
    for attempt in range(settings.DEPENDENCY_MAX_RETRIES + 1):
        try:
            response = httpx.post(
                url,
                json=payload,
                headers=_headers(claim_id, claim_version),
                timeout=settings.DEPENDENCY_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return schema.model_validate(response.json())
        except (httpx.HTTPError, ValueError, ValidationError) as exc:
            last_error = exc
            if attempt < settings.DEPENDENCY_MAX_RETRIES:
                time.sleep(min(0.1 * (2 ** attempt), 1.0))
    raise AssessmentUnavailable(type(last_error).__name__) from last_error


def assess_rules(claim, patient, insurance) -> RulesDecision:
    payload = {
        "schema_version": "1.0",
        "claim_id": claim.id,
        "claim_version": claim.version,
        "province": claim.province,
        "provider_billing_number": claim.provider_billing_number,
        "service_date": claim.service_date.isoformat(),
        "health_card_number": insurance.health_card_number if insurance else None,
        "patient_province": patient.province,
        "lines": [
            {
                "service_code": line.service_code,
                "diagnosis_code": line.diagnosis_code,
                "units": line.units,
                "amount": str(line.amount),
            }
            for line in claim.lines
        ],
    }
    if settings.RULES_ENGINE_URL:
        return _post(settings.RULES_ENGINE_URL, payload, RulesDecision, claim.id, claim.version)

    errors = run_rules(
        ClaimContext(
            claim.province,
            claim.provider_billing_number,
            claim.service_date,
            insurance.health_card_number if insurance else None,
            patient.province,
            payload["lines"],
        )
    )
    return RulesDecision(
        schema_version="1.0",
        outcome="FAIL" if errors else "PASS",
        reason_codes=[error.code for error in errors],
        rules_version="local-1.0",
    )


def assess_fraud(claim) -> FraudDecision:
    payload = {
        "schema_version": "1.0",
        "claim_id": claim.id,
        "claim_version": claim.version,
        "amount": str(claim.billed_amount),
    }
    if settings.FRAUD_ENGINE_URL:
        return _post(settings.FRAUD_ENGINE_URL, payload, FraudDecision, claim.id, claim.version)

    # The local adapter is deliberately deterministic and only provides an isolated-mode contract.
    return FraudDecision(
        schema_version="1.0",
        risk="LOW",
        score=0.05,
        model_version="local-stub-1.0",
    )
