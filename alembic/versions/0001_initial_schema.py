"""Create the initial PostgreSQL schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(), nullable=False), sa.Column("hashed_password", sa.String(), nullable=False), sa.Column("role", sa.String(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("patients", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("first_name", sa.String(), nullable=False), sa.Column("last_name", sa.String(), nullable=False), sa.Column("dob", sa.Date(), nullable=False), sa.Column("gender", sa.String(), nullable=False), sa.Column("province", sa.String(), nullable=False), sa.Column("phone", sa.String()), sa.Column("email", sa.String()), sa.Column("address_line1", sa.String()), sa.Column("city", sa.String()), sa.Column("postal_code", sa.String()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_table("insurance_plans", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("payer_id", sa.String(), nullable=False), sa.Column("name", sa.String(), nullable=False), sa.Column("layer", sa.String(), nullable=False), sa.Column("plan_type", sa.String()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_insurance_plans_payer_id", "insurance_plans", ["payer_id"], unique=True)
    op.create_table("patient_insurances", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False), sa.Column("plan_id", sa.Integer(), sa.ForeignKey("insurance_plans.id"), nullable=False), sa.Column("member_id", sa.String(), nullable=False), sa.Column("health_card_number", sa.String()), sa.Column("group_number", sa.String()), sa.Column("effective_date", sa.Date(), nullable=False), sa.Column("termination_date", sa.Date()), sa.Column("priority", sa.String(), nullable=False), sa.Column("last_verified_at", sa.DateTime()), sa.Column("last_eligibility", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_table("claims", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False), sa.Column("plan_id", sa.Integer(), sa.ForeignKey("insurance_plans.id"), nullable=False), sa.Column("province", sa.String(), nullable=False), sa.Column("provider_billing_number", sa.String(), nullable=False), sa.Column("service_date", sa.Date(), nullable=False), sa.Column("status", sa.String(), nullable=False), sa.Column("billed_amount", sa.Numeric(10, 2), nullable=False), sa.Column("denial_reason_code", sa.String()), sa.Column("coverage_snapshot", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_table("claim_lines", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id"), nullable=False), sa.Column("service_code", sa.String(), nullable=False), sa.Column("diagnosis_code", sa.String(), nullable=False), sa.Column("units", sa.Integer(), nullable=False), sa.Column("amount", sa.Numeric(10, 2), nullable=False))
    op.create_table("claim_status_history", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id"), nullable=False), sa.Column("from_status", sa.String()), sa.Column("to_status", sa.String(), nullable=False), sa.Column("reason_code", sa.String()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("appeals", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id"), nullable=False), sa.Column("denial_reason_code", sa.String(), nullable=False), sa.Column("note", sa.String()), sa.Column("supporting_doc_url", sa.String()), sa.Column("outcome", sa.String(), nullable=False), sa.Column("resolved_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_table("payments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id"), nullable=False), sa.Column("era_number", sa.String(), nullable=False), sa.Column("eob_reference", sa.String()), sa.Column("paid_amount", sa.Numeric(10, 2), nullable=False), sa.Column("underpaid", sa.Boolean(), nullable=False), sa.Column("remittance", sa.String()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_table("provincial_rules", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("province", sa.String(), nullable=False), sa.Column("config", sa.JSON(), nullable=False))
    op.create_index("ix_provincial_rules_province", "provincial_rules", ["province"])
    op.create_table("audit_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer()), sa.Column("action", sa.String(), nullable=False), sa.Column("resource", sa.String(), nullable=False), sa.Column("ip_address", sa.String()), sa.Column("created_at", sa.DateTime(), nullable=False))


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_index("ix_provincial_rules_province", table_name="provincial_rules")
    op.drop_table("provincial_rules")
    op.drop_table("payments")
    op.drop_table("appeals")
    op.drop_table("claim_status_history")
    op.drop_table("claim_lines")
    op.drop_table("claims")
    op.drop_table("patient_insurances")
    op.drop_index("ix_insurance_plans_payer_id", table_name="insurance_plans")
    op.drop_table("insurance_plans")
    op.drop_table("patients")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
