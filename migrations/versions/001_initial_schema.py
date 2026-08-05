"""Initial schema: conversations, messages, evidence, reflections, concepts."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ell.storage.models import (
    Concept,
    ConceptVersion,
    ConceptOperation,
    Conversation,
    Evidence,
    EvidenceType,
    Message,
    Reflection,
    ReflectionEvidence,
    TemporalScope,
)

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(255), unique=True, nullable=False),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("raw_data", postgresql.JSON, nullable=True),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("speaker", sa.Enum("user", "assistant", "system", "tool",
                                     name="speaker_enum"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column("branch_id", sa.String(64), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum(EvidenceType, name="evidencetype"), nullable=False),
        sa.Column("statement", sa.Text, nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("temporal_scope", sa.Enum(TemporalScope, name="temporalscope"), nullable=False),
        sa.Column("importance", sa.Float, nullable=False),
        sa.Column("extraction_confidence", sa.Float, nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "reflections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("statement", sa.Text, nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("evidence_ids", postgresql.JSON, nullable=False),
        sa.Column("contradiction_ids", postgresql.JSON, nullable=False, default=list),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("status", sa.Enum("candidate", "verified", "rejected", "superseded",
                                     name="reflectionstatus"), nullable=False, default="candidate"),
        sa.Column("generated_at", sa.DateTime, nullable=False),
        sa.Column("limitations", postgresql.JSON, nullable=True),
        sa.Column("alternative_interpretations", postgresql.JSON, nullable=True),
    )

    op.create_table(
        "reflections_evidence",
        sa.Column("reflection_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("reflections.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "concepts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_name", sa.String(255), unique=True, nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("status", sa.Enum("active", "weak", "archived", name="conceptstatus"),
                   nullable=False, default="active"),
    )

    op.create_table(
        "concept_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("definition", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("valid_from", sa.DateTime, nullable=False),
        sa.Column("valid_until", sa.DateTime, nullable=True),
        sa.Column("operation", sa.Enum(ConceptOperation, name="conceptoperation"), nullable=False),
        sa.Column("supporting_evidence_ids", postgresql.JSON, nullable=False),
        sa.Column("contradicting_evidence_ids", postgresql.JSON, nullable=False, default=list),
        sa.Column("source_reflection_ids", postgresql.JSON, nullable=False, default=list),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("concept_versions")
    op.drop_table("concepts")
    op.drop_table("reflections_evidence")
    op.drop_table("reflections")
    op.drop_table("evidence")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.execute("DROP TYPE IF EXISTS conceptoperation")
    op.execute("DROP TYPE IF EXISTS conceptstatus")
    op.execute("DROP TYPE IF EXISTS reflectionstatus")
    op.execute("DROP TYPE IF EXISTS evidencetype")
    op.execute("DROP TYPE IF EXISTS temporalscope")
    op.execute("DROP TYPE IF EXISTS speaker_enum")
