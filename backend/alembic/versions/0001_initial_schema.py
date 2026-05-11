"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("google_sub", sa.String(255), nullable=True, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # roles
    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
    )

    # user_roles
    op.create_table(
        "user_roles",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # recordings
    op.create_table(
        "recordings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_uri", sa.Text, nullable=False),
        sa.Column("signal_type", sa.String(10), nullable=False),
        sa.Column("sampling_rate", sa.Integer, nullable=False),
        sa.Column("file_format", sa.String(20), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("subject_id", sa.String(255), nullable=True),
        sa.Column("device_id", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="uploaded"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )

    # assessment_jobs
    op.create_table(
        "assessment_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("recording_id", UUID(as_uuid=True), sa.ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="queued"),
        sa.Column("parameters", JSONB, nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_segments", sa.Integer, nullable=True),
        sa.Column("processed_segments", sa.Integer, nullable=True),
        sa.Column("progress_pct", sa.Float, nullable=True),
        sa.Column("current_stage", sa.Text, nullable=True),
        sa.Column("overall_verdict", sa.Text, nullable=True),
        sa.Column("acceptance_rate", sa.Float, nullable=True),
        sa.Column("escalated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("escalation_reason", sa.Text, nullable=True),
        sa.Column("agent_interpretation", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )

    # segments
    op.create_table(
        "segments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("assessment_job_id", UUID(as_uuid=True), sa.ForeignKey("assessment_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recording_id", UUID(as_uuid=True), sa.ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("segment_number", sa.Integer, nullable=False),
        sa.Column("start_time", sa.Float, nullable=False),
        sa.Column("end_time", sa.Float, nullable=False),
        sa.Column("classification", sa.Text, nullable=False, server_default="pending"),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("sqi_summary", JSONB, nullable=False, server_default="{}"),
        sa.Column("failed_rules", JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_segments_job_id", "segments", ["assessment_job_id"])

    # sqi_results
    op.create_table(
        "sqi_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("segment_id", UUID(as_uuid=True), sa.ForeignKey("segments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Float, nullable=True),
        sa.Column("threshold_min", sa.Float, nullable=True),
        sa.Column("threshold_max", sa.Float, nullable=True),
        sa.Column("passed", sa.Boolean, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sqi_results_segment_id", "sqi_results", ["segment_id"])

    # reports
    op.create_table(
        "reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("assessment_job_id", UUID(as_uuid=True), sa.ForeignKey("assessment_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recording_id", UUID(as_uuid=True), sa.ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="generating"),
        sa.Column("format", sa.Text, nullable=False),
        sa.Column("content_json", JSONB, nullable=True),
        sa.Column("content_html", sa.Text, nullable=True),
        sa.Column("pdf_file_path", sa.Text, nullable=True),
        sa.Column("include_waveform_plots", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )

    # conversations
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("recording_id", UUID(as_uuid=True), sa.ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_job_id", UUID(as_uuid=True), sa.ForeignKey("assessment_jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("report_id", UUID(as_uuid=True), sa.ForeignKey("reports.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )

    # chat_messages
    op.create_table(
        "chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("sources", JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )

    # agent_logs
    op.create_table(
        "agent_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("assessment_job_id", UUID(as_uuid=True), sa.ForeignKey("assessment_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stage", sa.Text, nullable=False),
        sa.Column("tool_called", sa.Text, nullable=True),
        sa.Column("input_params", JSONB, nullable=True),
        sa.Column("output_summary", sa.Text, nullable=True),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("error_detail", sa.Text, nullable=True),
    )
    op.create_index("ix_agent_logs_job_id", "agent_logs", ["assessment_job_id"])

    # audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("resource_type", sa.Text, nullable=True),
        sa.Column("resource_id", sa.Text, nullable=True),
        sa.Column("details", JSONB, nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.Text, nullable=True),
        sa.Column("request_id", sa.Text, nullable=True),
    )

    # settings
    op.create_table(
        "settings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(255), nullable=False, unique=True),
        sa.Column("value", JSONB, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_by", UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    for table in [
        "settings", "audit_events", "agent_logs", "chat_messages",
        "conversations", "reports", "sqi_results", "segments",
        "assessment_jobs", "recordings", "user_roles", "roles", "users",
    ]:
        op.drop_table(table)
