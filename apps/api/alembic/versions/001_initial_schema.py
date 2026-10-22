"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-19 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Enable pgvector extension (if on PostgreSQL)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_workspaces_owner_id_users'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_workspaces'))
    )
    op.create_index(op.f('ix_workspaces_owner_id'), 'workspaces', ['owner_id'], unique=False)

    # 3. workspace_memberships
    op.create_table(
        'workspace_memberships',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='OWNER', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_workspace_memberships_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name=op.f('fk_workspace_memberships_workspace_id_workspaces'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_workspace_memberships')),
        sa.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_membership')
    )

    # 4. documents
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('uploader_id', sa.UUID(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_key', sa.String(length=500), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], name=op.f('fk_documents_uploader_id_users'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name=op.f('fk_documents_workspace_id_workspaces'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_documents')),
        sa.UniqueConstraint('storage_key', name=op.f('uq_documents_storage_key'))
    )
    op.create_index('idx_documents_workspace_status', 'documents', ['workspace_id', 'status'])
    op.create_index('idx_documents_content_hash', 'documents', ['workspace_id', 'content_hash'])

    # 5. document_chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('start_char_offset', sa.Integer(), nullable=True),
        sa.Column('end_char_offset', sa.Integer(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('embedding', Vector(768), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('embedding_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_document_chunks_document_id_documents'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name=op.f('fk_document_chunks_workspace_id_workspaces'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_document_chunks'))
    )
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'])
    op.create_index(op.f('ix_document_chunks_workspace_id'), 'document_chunks', ['workspace_id'])

    # 6. collections & document_collections
    op.create_table(
        'collections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name=op.f('fk_collections_workspace_id_workspaces'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_collections')),
        sa.UniqueConstraint('workspace_id', 'name', name='uq_workspace_collection_name')
    )

    op.create_table(
        'document_collections',
        sa.Column('collection_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], name=op.f('fk_document_collections_collection_id_collections'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_document_collections_document_id_documents'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('collection_id', 'document_id', name=op.f('pk_document_collections'))
    )

    # 7. conversations, messages, citations
    op.create_table(
        'conversations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('scope', sa.String(length=50), server_default='WORKSPACE', nullable=False),
        sa.Column('scope_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_conversations_user_id_users'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name=op.f('fk_conversations_workspace_id_workspaces'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_conversations'))
    )

    op.create_table(
        'messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('completion_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('insufficient_evidence', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name=op.f('fk_messages_conversation_id_conversations'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_messages'))
    )

    op.create_table(
        'citations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.UUID(), nullable=True),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('document_title', sa.String(length=255), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], name=op.f('fk_citations_chunk_id_document_chunks'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_citations_document_id_documents'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], name=op.f('fk_citations_message_id_messages'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_citations'))
    )

    # 8. ingestion_jobs
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('stage', sa.String(length=50), server_default='QUEUED', nullable=False),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('safe_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_ingestion_jobs_document_id_documents'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_ingestion_jobs'))
    )


def downgrade() -> None:
    op.drop_table('ingestion_jobs')
    op.drop_table('citations')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('document_collections')
    op.drop_table('collections')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('workspace_memberships')
    op.drop_table('workspaces')
    op.drop_table('users')
