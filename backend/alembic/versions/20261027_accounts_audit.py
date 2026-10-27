"""Local accounts, revocable sessions, and persistent action history."""
from alembic import op
import sqlalchemy as sa

revision = '20261027_accounts_audit'
down_revision = '20261008_data_halls'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('username', sa.String(64), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('failed_logins', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True)),
        sa.CheckConstraint("role IN ('viewer', 'operator', 'admin')", name='ck_user_role'))
    op.create_table('login_sessions',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('csrf_hash', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_login_sessions_user_id', 'login_sessions', ['user_id'])
    op.create_table('audit_events',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('actor_id', sa.UUID()), sa.Column('actor_name', sa.String(64), nullable=False),
        sa.Column('action', sa.String(180), nullable=False), sa.Column('target_name', sa.String(180), nullable=False),
        sa.Column('target_id', sa.UUID()), sa.Column('rack_id', sa.UUID()), sa.Column('system_id', sa.UUID()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('outcome', sa.String(16), nullable=False), sa.Column('expected_state', sa.String(32)),
        sa.Column('status_code', sa.Integer()), sa.Column('message', sa.Text(), nullable=False), sa.Column('changed_fields', sa.JSON(), nullable=False))
    for field in ['target_id', 'rack_id', 'system_id']:
        op.create_index('ix_audit_events_' + field, 'audit_events', [field])


def downgrade():
    op.drop_table('audit_events')
    op.drop_table('login_sessions')
    op.drop_table('users')
