"""Minimal audit and shared counters; column-specific runtime grants."""

from alembic import op

revision = "0004_auth_controls"
down_revision = "0003_identity_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    ddl = """
    CREATE TABLE auth_audit_events (
      id UUID PRIMARY KEY, occurred_at TIMESTAMPTZ NOT NULL,
      actor VARCHAR(64), subject VARCHAR(64), action VARCHAR(32) NOT NULL,
      outcome VARCHAR(16) NOT NULL, request_id UUID NOT NULL
    );
    CREATE INDEX ix_audit_time ON auth_audit_events(occurred_at);
    CREATE INDEX ix_audit_subject ON auth_audit_events(subject,occurred_at);
    CREATE TABLE auth_rate_limits (
      dimension VARCHAR(32) NOT NULL, identifier VARCHAR(64) NOT NULL,
      "window" INTEGER NOT NULL, count INTEGER NOT NULL, expires_at TIMESTAMPTZ NOT NULL,
      PRIMARY KEY(dimension,identifier,"window"), CONSTRAINT ck_rate_count CHECK(count>=0)
    );
    CREATE INDEX ix_rate_expiry ON auth_rate_limits(expires_at);
    """
    for statement in ddl.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("""
    DO $grants$ BEGIN
      IF EXISTS (SELECT FROM pg_roles WHERE rolname='county_runtime') THEN
        GRANT SELECT, INSERT ON users TO county_runtime;
        GRANT UPDATE(password_hash,preferred_language,privacy_notice_version,
          privacy_notice_acknowledged_at,token_version,updated_at) ON users TO county_runtime;
        GRANT SELECT ON invitations TO county_runtime;
        GRANT UPDATE(consumed_at,accepted_user_id) ON invitations TO county_runtime;
        GRANT SELECT, INSERT, UPDATE ON
          auth_sessions,refresh_tokens,auth_rate_limits TO county_runtime;
        GRANT INSERT ON auth_audit_events TO county_runtime;
      END IF;
    END $grants$;
    """)


def downgrade() -> None:
    for statement in ["DROP TABLE auth_rate_limits", " DROP TABLE auth_audit_events"]:
        op.execute(statement)
