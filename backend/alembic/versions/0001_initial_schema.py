"""Initial schema — all tables.

Revision ID: 0001
Revises:
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255)),
        sa.Column("google_sub", sa.String(255), unique=True),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("deleted_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.CheckConstraint("status IN ('active','disabled')", name="ck_user_status"),
    )

    # roles
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(32), nullable=False, unique=True),
        sa.Column("description", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("deleted_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "name IN ('admin','researcher','reviewer','readonly')", name="ck_role_name"
        ),
    )

    # user_roles
    op.create_table(
        "user_roles",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role_id", sa.UUID(), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("deleted_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role_active"),
    )

    # recordings
    op.create_table(
        "recordings",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_format", sa.String(16), nullable=False),
        sa.Column("signal_type", sa.String(8), nullable=False),
        sa.Column("sampling_rate", sa.Float()),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("channel_count", sa.Integer(), server_default="1"),
        sa.Column("file_size_bytes", sa.BigInteger()),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("storage_uri", sa.String(500)),
        sa.Column("subject_id", sa.String(128)),
        sa.Column("device_id", sa.String(128)),
        sa.Column("notes", sa.Text()),
        sa.Column("agent_summary", JSONB()),
        sa.Column("status", sa.String(16), nullable=False, server_default="uploaded"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("deleted_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "file_format IN ('edf','csv','parquet','wfdb')", name="ck_recording_format"
        ),
        sa.CheckConstraint("signal_type IN ('ecg','ppg')", name="ck_recording_signal_type"),
        sa.CheckConstraint(
            "status IN ('uploaded','processing','completed','failed')",
            name="ck_recording_status",
        ),
    )

    # assessment_jobs
    op.create_table(
        "assessment_jobs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "recording_id",
            sa.UUID(),
            sa.ForeignKey("recordings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("current_step", sa.String(64)),
        sa.Column("progress_pct", sa.Numeric(5, 2)),
        sa.Column("total_segments", sa.Integer()),
        sa.Column("processed_segments", sa.Integer(), server_default="0"),
        sa.Column("parameters", JSONB()),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("deleted_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "status IN ('queued','processing','completed','failed','cancelled')",
            name="ck_job_status",
        ),
    )

    # segments
    op.create_table(
        "segments",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "assessment_job_id",
            sa.UUID(),
            sa.ForeignKey("assessment_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recording_id",
            sa.UUID(),
            sa.ForeignKey("recordings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("segment_number", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Float()),
        sa.Column("end_time", sa.Float()),
        sa.Column("duration", sa.Float()),
        sa.Column("classification", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("quality_score", sa.Float()),
        sa.Column("sqi_summary", JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "classification IN ('accept','reject','pending','uncomputable')",
            name="ck_segment_classification",
        ),
        sa.UniqueConstraint("assessment_job_id", "segment_number", name="uq_segment_job_number"),
    )

    # sqi_results
    op.create_table(
        "sqi_results",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "segment_id",
            sa.UUID(),
            sa.ForeignKey("segments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric_name", sa.String(64), nullable=False),
        sa.Column("metric_category", sa.String(32), nullable=False),
        sa.Column("metric_value", sa.Float()),
        sa.Column("threshold_min", sa.Float()),
        sa.Column("threshold_max", sa.Float()),
        sa.Column("passed", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "metric_category IN ('statistical','signal_processing','cardiac',"
            "'hrv_time','hrv_frequency','waveform','nonlinear','clinical')",
            name="ck_sqi_metric_category",
        ),
        sa.UniqueConstraint("segment_id", "metric_name", name="uq_sqi_segment_metric"),
    )

    # segment_override_events
    op.create_table(
        "segment_override_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "segment_id",
            sa.UUID(),
            sa.ForeignKey("segments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recording_id",
            sa.UUID(),
            sa.ForeignKey("recordings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_job_id",
            sa.UUID(),
            sa.ForeignKey("assessment_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(8), nullable=False),
        sa.Column("reason_category", sa.String(64)),
        sa.Column("note", sa.Text()),
        sa.Column(
            "supersedes_override_event_id",
            sa.UUID(),
            sa.ForeignKey("segment_override_events.id"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.CheckConstraint("label IN ('accept','reject')", name="ck_override_label"),
    )

    # reports
    op.create_table(
        "reports",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("recording_id", sa.UUID(), sa.ForeignKey("recordings.id"), nullable=False),
        sa.Column("assessment_job_id", sa.UUID(), sa.ForeignKey("assessment_jobs.id")),
        sa.Column("title", sa.String(255)),
        sa.Column("content_json", JSONB()),
        sa.Column("content_html", sa.Text()),
        sa.Column("pdf_file_path", sa.String(500)),
        sa.Column("json_schema_version", sa.String(16), nullable=False, server_default="1.0"),
        sa.Column("generated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("deleted_by", sa.UUID(), sa.ForeignKey("users.id")),
    )

    # conversations
    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("recording_id", sa.UUID(), sa.ForeignKey("recordings.id"), nullable=False),
        sa.Column("assessment_job_id", sa.UUID(), sa.ForeignKey("assessment_jobs.id")),
        sa.Column("report_id", sa.UUID(), sa.ForeignKey("reports.id")),
        sa.Column("title", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("deleted_by", sa.UUID(), sa.ForeignKey("users.id")),
    )

    # chat_messages
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.UUID(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", JSONB()),
        sa.Column("token_count", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("deleted_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.CheckConstraint("role IN ('user','assistant','system')", name="ck_message_role"),
    )

    # agent_logs
    op.create_table(
        "agent_logs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "assessment_job_id",
            sa.UUID(),
            sa.ForeignKey("assessment_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recording_id",
            sa.UUID(),
            sa.ForeignKey("recordings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("tool_called", sa.String(128)),
        sa.Column("input_params", JSONB()),
        sa.Column("output_summary", sa.Text()),
        sa.Column("reasoning", sa.Text()),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("status", sa.String(16), nullable=False, server_default="success"),
        sa.Column("error_detail", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "stage IN ('initialized','loading','preprocessing','assessing',"
            "'interpreting','reporting','completed','error')",
            name="ck_agent_log_stage",
        ),
        sa.CheckConstraint(
            "status IN ('success','error','timeout','skipped')",
            name="ck_agent_log_status",
        ),
        sa.UniqueConstraint("assessment_job_id", "step_number", name="uq_agent_log_job_step"),
    )

    # audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("actor_user_id", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(64)),
        sa.Column("entity_id", sa.UUID()),
        sa.Column("details", JSONB()),
        sa.Column("request_id", sa.String(64)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # settings
    op.create_table(
        "settings",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", JSONB()),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("description", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("updated_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("deleted_by", sa.UUID(), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "category IN ('sqi','segmentation','agent','clinical','ui')",
            name="ck_setting_category",
        ),
        sa.UniqueConstraint("key", name="uq_setting_key_active"),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("audit_events")
    op.drop_table("agent_logs")
    op.drop_table("chat_messages")
    op.drop_table("conversations")
    op.drop_table("reports")
    op.drop_table("segment_override_events")
    op.drop_table("sqi_results")
    op.drop_table("segments")
    op.drop_table("assessment_jobs")
    op.drop_table("recordings")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")
