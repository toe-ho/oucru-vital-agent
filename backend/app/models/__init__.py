"""Import all models so Alembic's autogenerate can discover them via Base.metadata."""

from app.models.log_models import AgentLog, AuditEvent
from app.models.recording_models import AssessmentJob, Recording
from app.models.report_models import ChatMessage, Conversation, Report
from app.models.segment_models import Segment, SegmentOverrideEvent, SqiResult
from app.models.settings_models import Setting
from app.models.user_models import Role, User, UserRole

__all__ = [
    "User",
    "Role",
    "UserRole",
    "Recording",
    "AssessmentJob",
    "Segment",
    "SqiResult",
    "SegmentOverrideEvent",
    "Report",
    "Conversation",
    "ChatMessage",
    "AgentLog",
    "AuditEvent",
    "Setting",
]
