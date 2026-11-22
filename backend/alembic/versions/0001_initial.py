"""Initial MediGuide schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("patient", "clinician", "admin", name="role"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("medical_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("stored_name", sa.String(255), nullable=False, unique=True),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("doc_type", sa.String(40), nullable=False),
        sa.Column("status", sa.Enum("uploaded", "processing", "ready", "needs_review", "failed", name="documentstatus"), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text()),
        sa.Column("extraction_confidence", sa.Float()),
        sa.Column("error_message", sa.Text()),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_medical_documents_user_id", "medical_documents", ["user_id"])
    op.create_table("extracted_items",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("document_id", sa.String(36), sa.ForeignKey("medical_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("data_type", sa.String(40), nullable=False), sa.Column("item_name", sa.String(120), nullable=False), sa.Column("item_value", sa.String(255), nullable=False),
        sa.Column("unit", sa.String(50)), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("source_text", sa.Text()), sa.Column("verified", sa.Boolean(), nullable=False))
    op.create_index("ix_extracted_items_document_id", "extracted_items", ["document_id"])
    op.create_table("medical_explanations",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("document_id", sa.String(36), sa.ForeignKey("medical_documents.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("simple_text", sa.Text(), nullable=False), sa.Column("important_points", sa.Text(), nullable=False), sa.Column("cautions", sa.Text(), nullable=False),
        sa.Column("citations", sa.Text(), nullable=False), sa.Column("model_name", sa.String(80), nullable=False), sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("follow_ups",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("document_id", sa.String(36), sa.ForeignKey("medical_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False), sa.Column("due_date", sa.Date()), sa.Column("status", sa.String(20), nullable=False), sa.Column("reminder_set", sa.Boolean(), nullable=False), sa.Column("source_text", sa.Text()))
    op.create_index("ix_follow_ups_document_id", "follow_ups", ["document_id"])
    op.create_table("medications",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("document_id", sa.String(36), sa.ForeignKey("medical_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False), sa.Column("dosage_text", sa.String(120)), sa.Column("timing_text", sa.String(160)), sa.Column("needs_confirmation", sa.Boolean(), nullable=False), sa.Column("source_text", sa.Text()))
    op.create_index("ix_medications_document_id", "medications", ["document_id"])
    op.create_table("timeline_events",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("document_id", sa.String(36), sa.ForeignKey("medical_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False), sa.Column("event_date", sa.Date()), sa.Column("summary", sa.Text(), nullable=False))
    op.create_index("ix_timeline_events_document_id", "timeline_events", ["document_id"])
    op.create_table("consultation_questions",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("medical_documents.id", ondelete="CASCADE")), sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("document_id", "question_text"))
    op.create_index("ix_consultation_questions_user_id", "consultation_questions", ["user_id"])
    op.create_index("ix_consultation_questions_document_id", "consultation_questions", ["document_id"])


def downgrade() -> None:
    for table in ("consultation_questions", "timeline_events", "medications", "follow_ups", "medical_explanations", "extracted_items", "medical_documents", "users"):
        op.drop_table(table)
