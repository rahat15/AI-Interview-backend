"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create artifacts table
    op.create_table('artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=False),
        sa.Column('industry', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('plan_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('cv_file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('jd_file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('current_question_index', sa.Integer(), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cv_file_id'], ['artifacts.id'], ),
        sa.ForeignKeyConstraint(['jd_file_id'], ['artifacts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create questions table
    op.create_table('questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('competency', sa.String(length=100), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('is_follow_up', sa.Boolean(), nullable=True),
        sa.Column('parent_question_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['parent_question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create answers table
    op.create_table('answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.String(length=500), nullable=True),
        sa.Column('asr_text', sa.Text(), nullable=True),
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create scores table
    op.create_table('scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('answer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rubric_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('clarity', sa.Float(), nullable=False),
        sa.Column('structure', sa.Float(), nullable=False),
        sa.Column('depth_specificity', sa.Float(), nullable=False),
        sa.Column('role_fit', sa.Float(), nullable=False),
        sa.Column('technical', sa.Float(), nullable=False),
        sa.Column('communication', sa.Float(), nullable=False),
        sa.Column('ownership', sa.Float(), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=False),
        sa.Column('meta', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create reports table
    op.create_table('reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('pdf_url', sa.String(length=500), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('strengths', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('areas_for_improvement', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    
    # Create embeddings table
    op.create_table('embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('artifact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_idx', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', postgresql.VECTOR(384), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.execute('CREATE INDEX embeddings_embedding_ivfflat_idx ON embeddings USING ivfflat (embedding vector_l2_ops);')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('embeddings')
    op.drop_table('reports')
    op.drop_table('scores')
    op.drop_table('answers')
    op.drop_table('questions')
    op.drop_table('sessions')
    op.drop_table('artifacts')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
