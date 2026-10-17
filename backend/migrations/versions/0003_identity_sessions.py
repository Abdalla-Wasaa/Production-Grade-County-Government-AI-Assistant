"""Absolute session families and retained refresh lineage."""

from alembic import op

revision = "0003_identity_sessions"
down_revision = "0002_identity_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    ddl = """
    CREATE TABLE auth_sessions (
      id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      created_at TIMESTAMPTZ NOT NULL, expires_at TIMESTAMPTZ NOT NULL,
      last_used_at TIMESTAMPTZ NOT NULL, revoked_at TIMESTAMPTZ, reason VARCHAR(32),
      CONSTRAINT ck_session_lifetime CHECK (expires_at=created_at+interval '7 days')
    );
    CREATE INDEX ix_session_owner ON auth_sessions(user_id,created_at,id);
    CREATE INDEX ix_session_expiry ON auth_sessions(expires_at);
    CREATE TABLE refresh_tokens (
      id UUID PRIMARY KEY, session_id UUID NOT NULL REFERENCES auth_sessions(id) ON DELETE CASCADE,
      token_digest VARCHAR(64) NOT NULL UNIQUE, created_at TIMESTAMPTZ NOT NULL,
      expires_at TIMESTAMPTZ NOT NULL, consumed_at TIMESTAMPTZ, replaced_by_id UUID,
      CONSTRAINT uq_refresh_family_id UNIQUE(session_id,id),
      CONSTRAINT uq_refresh_successor UNIQUE(replaced_by_id),
      CONSTRAINT fk_refresh_successor FOREIGN KEY(session_id,replaced_by_id)
        REFERENCES refresh_tokens(session_id,id) DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT ck_refresh_expiry CHECK (expires_at>created_at),
      CONSTRAINT ck_refresh_consumed CHECK (replaced_by_id IS NULL OR consumed_at IS NOT NULL)
    );
    CREATE UNIQUE INDEX uq_refresh_live ON refresh_tokens(session_id) WHERE consumed_at IS NULL;
    CREATE INDEX ix_refresh_expiry ON refresh_tokens(expires_at);
    """
    for statement in ddl.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    for statement in ["DROP TABLE refresh_tokens", " DROP TABLE auth_sessions"]:
        op.execute(statement)
