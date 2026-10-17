"""Accounts and one-use invitations; no accounts are seeded."""

from alembic import op

revision = "0002_identity_accounts"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    ddl = """
    CREATE TABLE users (
      id UUID PRIMARY KEY, email_normalized VARCHAR(254) NOT NULL UNIQUE,
      password_hash TEXT NOT NULL, role VARCHAR(16) NOT NULL, status VARCHAR(16) NOT NULL,
      preferred_language VARCHAR(2) NOT NULL, token_version INTEGER NOT NULL,
      privacy_notice_version VARCHAR(64) NOT NULL,
      privacy_notice_acknowledged_at TIMESTAMPTZ NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_user_role CHECK (role IN ('citizen','staff','admin')),
      CONSTRAINT ck_user_status CHECK (status IN ('active','disabled')),
      CONSTRAINT ck_user_language CHECK (preferred_language IN ('en','sw')),
      CONSTRAINT ck_user_version CHECK (token_version >= 0),
      CONSTRAINT ck_user_email CHECK (email_normalized=lower(btrim(email_normalized)))
    );
    CREATE TABLE invitations (
      id UUID PRIMARY KEY, email_normalized VARCHAR(254) NOT NULL,
      purpose VARCHAR(16) NOT NULL, target_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
      role VARCHAR(16) NOT NULL, preferred_language VARCHAR(2) NOT NULL,
      privacy_notice_version VARCHAR(64) NOT NULL, token_digest VARCHAR(64) NOT NULL UNIQUE,
      issuer VARCHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      expires_at TIMESTAMPTZ NOT NULL, consumed_at TIMESTAMPTZ, revoked_at TIMESTAMPTZ,
      accepted_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
      CONSTRAINT ck_invitation_purpose CHECK (purpose IN ('activation','password_reset')),
      CONSTRAINT ck_invitation_role CHECK (role IN ('citizen','staff','admin')),
      CONSTRAINT ck_invitation_language CHECK (preferred_language IN ('en','sw')),
      CONSTRAINT ck_invitation_expiry CHECK (expires_at>created_at),
      CONSTRAINT ck_invitation_target CHECK
        ((purpose='activation' AND target_user_id IS NULL) OR
         (purpose='password_reset' AND target_user_id IS NOT NULL))
    );
    CREATE UNIQUE INDEX uq_invitation_outstanding ON invitations(email_normalized,purpose)
      WHERE consumed_at IS NULL AND revoked_at IS NULL;
    CREATE INDEX ix_invitation_expiry ON invitations(expires_at);
    """
    for statement in ddl.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    # Explicit downgrade destroys accounts; restore/forward repair is preferred.
    for statement in ["DROP TABLE invitations", " DROP TABLE users"]:
        op.execute(statement)
