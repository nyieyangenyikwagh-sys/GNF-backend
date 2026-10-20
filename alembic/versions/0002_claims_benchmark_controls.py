"""Add claim ownership, idempotency, workflow, and append-only audit controls.

Revision ID: 0002_claims_benchmark_controls
Revises: 0001_initial_schema
Create Date: 2026-10-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_claims_benchmark_controls"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("owner_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_patients_owner_user", "patients", "users", ["owner_user_id"], ["id"])
    op.create_index("ix_patients_owner_user_id", "patients", ["owner_user_id"])

    op.add_column("claims", sa.Column("owner_user_id", sa.Integer(), nullable=True))
    op.add_column("claims", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.add_column("claims", sa.Column("request_hash", sa.String(64), nullable=True))
    op.add_column("claims", sa.Column("correlation_id", sa.String(128), nullable=True))
    op.add_column("claims", sa.Column("version", sa.Integer(), server_default="1", nullable=False))
    op.add_column("claims", sa.Column("rules_result", sa.JSON(), nullable=True))
    op.add_column("claims", sa.Column("fraud_result", sa.JSON(), nullable=True))
    op.add_column("claims", sa.Column("assessment_claim_version", sa.Integer(), nullable=True))
    op.add_column("claims", sa.Column("assessment_attempts", sa.Integer(), server_default="0", nullable=False))
    op.add_column("claims", sa.Column("next_retry_at", sa.DateTime(), nullable=True))

    # Preserve pre-benchmark data under a disabled system owner rather than dropping it.
    op.execute("""
        INSERT INTO users (email, hashed_password, role, is_active)
        SELECT 'legacy-owner@invalid.local', '!', 'service', false
        WHERE NOT EXISTS (SELECT 1 FROM users)
    """)
    op.execute("UPDATE patients SET owner_user_id = (SELECT MIN(id) FROM users) WHERE owner_user_id IS NULL")
    op.execute("UPDATE claims SET owner_user_id = (SELECT MIN(id) FROM users) WHERE owner_user_id IS NULL")
    op.execute("UPDATE claims SET idempotency_key = 'legacy-' || id::text WHERE idempotency_key IS NULL")
    op.execute("UPDATE claims SET request_hash = repeat('0', 64) WHERE request_hash IS NULL")
    op.execute("UPDATE claims SET correlation_id = 'legacy-migration' WHERE correlation_id IS NULL")
    op.execute("""
        UPDATE claims SET status = CASE lower(status)
          WHEN 'draft' THEN 'PENDING_RULES'
          WHEN 'submitted' THEN 'SUBMITTED'
          WHEN 'rejected' THEN 'REVIEW'
          WHEN 'denied' THEN 'DENIED'
          WHEN 'appeal_pending' THEN 'HUMAN_REVIEW'
          WHEN 'paid' THEN 'PAID'
          WHEN 'closed' THEN 'CLOSED'
          ELSE status END
    """)
    op.alter_column("claims", "owner_user_id", nullable=False)
    op.alter_column("claims", "idempotency_key", nullable=False)
    op.alter_column("claims", "request_hash", nullable=False)
    op.alter_column("claims", "correlation_id", nullable=False)
    op.create_foreign_key("fk_claims_owner_user", "claims", "users", ["owner_user_id"], ["id"])
    op.create_index("ix_claims_owner_user_id", "claims", ["owner_user_id"])
    op.create_unique_constraint("uq_claim_owner_idempotency", "claims", ["owner_user_id", "idempotency_key"])

    op.add_column("claim_status_history", sa.Column("actor_user_id", sa.Integer(), nullable=True))
    op.add_column("claim_status_history", sa.Column("correlation_id", sa.String(128), server_default="legacy-migration", nullable=False))
    op.add_column("claim_status_history", sa.Column("claim_version", sa.Integer(), server_default="1", nullable=False))
    op.create_foreign_key("fk_claim_history_actor", "claim_status_history", "users", ["actor_user_id"], ["id"])

    op.add_column("audit_logs", sa.Column("claim_id", sa.Integer(), nullable=True))
    op.add_column("audit_logs", sa.Column("correlation_id", sa.String(128), server_default="legacy-migration", nullable=False))
    op.add_column("audit_logs", sa.Column("claim_version", sa.Integer(), nullable=True))
    op.add_column("audit_logs", sa.Column("details", sa.JSON(), nullable=True))
    op.create_foreign_key("fk_audit_claim", "audit_logs", "claims", ["claim_id"], ["id"])
    op.create_index("ix_audit_logs_claim_id", "audit_logs", ["claim_id"])

    # API code has no mutation route; this database guard makes the guarantee durable.
    op.execute("""
        CREATE FUNCTION prevent_audit_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'audit_logs is append-only';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_mutation()")
    op.drop_index("ix_audit_logs_claim_id", table_name="audit_logs")
    op.drop_constraint("fk_audit_claim", "audit_logs", type_="foreignkey")
    for column in ("details", "claim_version", "correlation_id", "claim_id"):
        op.drop_column("audit_logs", column)
    op.drop_constraint("fk_claim_history_actor", "claim_status_history", type_="foreignkey")
    for column in ("claim_version", "correlation_id", "actor_user_id"):
        op.drop_column("claim_status_history", column)
    op.drop_constraint("uq_claim_owner_idempotency", "claims", type_="unique")
    op.drop_index("ix_claims_owner_user_id", table_name="claims")
    op.drop_constraint("fk_claims_owner_user", "claims", type_="foreignkey")
    for column in ("next_retry_at", "assessment_attempts", "assessment_claim_version", "fraud_result", "rules_result", "version", "correlation_id", "request_hash", "idempotency_key", "owner_user_id"):
        op.drop_column("claims", column)
    op.drop_index("ix_patients_owner_user_id", table_name="patients")
    op.drop_constraint("fk_patients_owner_user", "patients", type_="foreignkey")
    op.drop_column("patients", "owner_user_id")
