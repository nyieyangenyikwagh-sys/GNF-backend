"""Deterministic adapter for the Apache-2.0 synthetic motor-claims dataset.

The source fraud label is intentionally ignored: it is not ground truth for this
health-claims workflow. Mapping metadata is returned separately from the API body.
"""

import csv
import hashlib
import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


SERVICE_CODES = ("03.03A", "03.04A", "03.05A", "03.08A", "13.99A")
DIAGNOSIS_CODES = ("J06.9", "E11.9", "I10", "M54.5", "R51", "Z00.0", "F41.1")
REQUIRED_SOURCE_FIELDS = {"claim_id", "policy_id", "incident_date", "incident_type", "claim_amount"}


def inspect_csv(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = REQUIRED_SOURCE_FIELDS - set(fields)
        if missing:
            raise ValueError(f"dataset is missing required fields: {sorted(missing)}")
        rows = 0
        nulls = {field: 0 for field in fields}
        categories: dict[str, set[str]] = {"incident_type": set(), "policy_type": set()}
        for row in reader:
            rows += 1
            for field in fields:
                if row.get(field, "") == "":
                    nulls[field] += 1
            for field in categories:
                categories[field].add(row.get(field, ""))
    return {"rows": rows, "columns": len(fields), "fields": fields, "nulls": nulls, "categories": {key: sorted(value) for key, value in categories.items()}}


def _stable_index(value: str, size: int) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16) % size


def map_row(row: dict[str, str], *, patient_id: int, plan_id: int, anchor_date: date | None = None) -> tuple[dict, dict]:
    missing = REQUIRED_SOURCE_FIELDS - row.keys()
    if missing:
        raise ValueError(f"row is missing required fields: {sorted(missing)}")
    anchor = anchor_date or date.today()
    source_date = date.fromisoformat(row["incident_date"])
    # The external motor policies do not exist in this service. Keep relative variation
    # while deterministically placing service dates in the seeded health-policy window.
    service_date = anchor - timedelta(days=source_date.toordinal() % 60)
    amount = Decimal(row["claim_amount"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    amount = max(Decimal("0.01"), min(amount, Decimal("9999999999.99")))
    incident = row["incident_type"]
    payload = {
        "patient_id": patient_id,
        "plan_id": plan_id,
        "province": "AB",
        "provider_billing_number": f"{_stable_index(row['policy_id'], 1_000_000):06d}",
        "service_date": service_date.isoformat(),
        "lines": [{
            "service_code": SERVICE_CODES[_stable_index(incident, len(SERVICE_CODES))],
            "diagnosis_code": DIAGNOSIS_CODES[_stable_index(row["claim_id"], len(DIAGNOSIS_CODES))],
            "units": 1,
            "amount": str(amount),
        }],
    }
    metadata = {
        "source_claim_id": row["claim_id"],
        "idempotency_key": f"external-{row['claim_id']}",
        "synthetic_fill_fields": ["patient_id", "plan_id", "province", "provider_billing_number", "service_code", "diagnosis_code", "units"],
        "transformed_fields": ["incident_date->service_date", "claim_amount->lines[0].amount"],
        "dropped_fields": sorted(set(row) - {"claim_id", "policy_id", "incident_date", "incident_type", "claim_amount"}),
    }
    return payload, metadata


def seeded_stratified_sample(path: Path, size: int, seed: int = 42) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if size >= len(rows):
        return rows
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row["incident_type"], []).append(row)
    rng = random.Random(seed)
    selected = []
    for group in groups.values():
        count = max(1, round(size * len(group) / len(rows)))
        selected.extend(rng.sample(group, min(count, len(group))))
    rng.shuffle(selected)
    return selected[:size]
