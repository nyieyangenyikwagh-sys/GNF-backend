import asyncio
import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse


app = FastAPI(title="Claims benchmark dependency stubs")
CONTROL_TOKEN = os.getenv("STUB_CONTROL_TOKEN", "benchmark-control")
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "benchmark-service-token")
modes = {"rules": "success", "fraud": "success"}


@app.get("/health")
def health():
    return {"status": "ok", "environment": "benchmark", "modes": modes}


@app.put("/__control/{dependency}/{mode}")
def control(dependency: str, mode: str, authorization: str = Header(default="")):
    if authorization != f"Bearer {CONTROL_TOKEN}":
        raise HTTPException(401, "Invalid control token")
    if dependency not in modes or mode not in {"success", "rule_fail", "high_risk", "error", "timeout", "invalid", "slow"}:
        raise HTTPException(400, "Unsupported mode")
    modes[dependency] = mode
    return {"dependency": dependency, "mode": mode}


async def _fault(mode: str):
    if mode == "error":
        raise HTTPException(500, "Injected dependency failure")
    if mode == "timeout":
        await asyncio.sleep(30)
    if mode == "slow":
        await asyncio.sleep(1)
    if mode == "invalid":
        return JSONResponse(200, {"unexpected": True})
    return None


def _authorize_service(authorization: str):
    if authorization != f"Bearer {SERVICE_TOKEN}":
        raise HTTPException(401, "Invalid service credential")


@app.post("/rules")
async def rules(_: dict, x_correlation_id: str = Header(...), idempotency_key: str = Header(...), authorization: str = Header(default="")):
    _authorize_service(authorization)
    fault = await _fault(modes["rules"])
    if fault:
        return fault
    if modes["rules"] == "rule_fail":
        return {"schema_version": "1.0", "outcome": "FAIL", "reason_codes": ["STUB_RULE_FAIL"], "rules_version": "stub-rules-1"}
    return {"schema_version": "1.0", "outcome": "PASS", "reason_codes": [], "rules_version": "stub-rules-1"}


@app.post("/fraud")
async def fraud(_: dict, x_correlation_id: str = Header(...), idempotency_key: str = Header(...), authorization: str = Header(default="")):
    _authorize_service(authorization)
    fault = await _fault(modes["fraud"])
    if fault:
        return fault
    if modes["fraud"] == "high_risk":
        return {"schema_version": "1.0", "risk": "HIGH", "score": 0.98, "model_version": "stub-fraud-1"}
    return {"schema_version": "1.0", "risk": "LOW", "score": 0.03, "model_version": "stub-fraud-1"}
