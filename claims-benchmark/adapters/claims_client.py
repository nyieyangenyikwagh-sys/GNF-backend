from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ClaimsClient:
    base_url: str
    token: str | None = None
    timeout: float = 5.0

    def _headers(self) -> dict[str, str]:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = self._headers()
        headers.update(kwargs.pop("headers", {}))
        return httpx.request(method, f"{self.base_url}{path}", headers=headers, timeout=self.timeout, **kwargs)

    def login(self, email: str, password: str) -> str:
        response = self.request("POST", "/api/v1/auth/login", data={"username": email, "password": password})
        response.raise_for_status()
        self.token = response.json()["access_token"]
        return self.token

    def create_claim(self, payload: dict, key: str) -> httpx.Response:
        return self.request("POST", "/api/v1/claims", json=payload, headers={"Idempotency-Key": key})

    def get_claim(self, claim_id: int) -> httpx.Response:
        return self.request("GET", f"/api/v1/claims/{claim_id}")

    def list_claims(self) -> httpx.Response:
        return self.request("GET", "/api/v1/claims")

    def transition(self, claim_id: int, to_status: str) -> httpx.Response:
        return self.request("POST", f"/api/v1/claims/{claim_id}/status", json={"to_status": to_status})
