"""Private Phase 2 user-message storage; no AI attempt tables or seeded content."""

from alembic import op

revision = "0005_conversation_persistence"
down_revision = "0004_auth_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    ddl = """
    CREATE TABLE conversations (
      id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      title VARCHAR(120) NOT NULL, language VARCHAR(2) NOT NULL,
      next_sequence BIGINT NOT NULL, version BIGINT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
      last_activity_at TIMESTAMPTZ NOT NULL, expires_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT ck_conversation_title CHECK(char_length(btrim(title)) BETWEEN 1 AND 120),
      CONSTRAINT ck_conversation_language CHECK(language IN ('en','sw')),
      CONSTRAINT ck_conversation_counters CHECK(next_sequence >= 1 AND version >= 1),
      CONSTRAINT ck_conversation_times CHECK(created_at <= last_activity_at
        AND last_activity_at <= updated_at AND expires_at > last_activity_at
        AND expires_at <= created_at + interval '90 days')
    );
    CREATE INDEX ix_conversation_owner ON conversations(user_id,updated_at,id);
    CREATE INDEX ix_conversation_expiry ON conversations(expires_at);
    CREATE TABLE messages (
      id UUID PRIMARY KEY,
      conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
      sequence BIGINT NOT NULL, role VARCHAR(16) NOT NULL, content TEXT NOT NULL,
      language VARCHAR(2) NOT NULL, client_request_id UUID NOT NULL,
      request_hash VARCHAR(64) NOT NULL, created_at TIMESTAMPTZ NOT NULL,
      CONSTRAINT uq_message_sequence UNIQUE(conversation_id,sequence),
      CONSTRAINT uq_message_request UNIQUE(conversation_id,client_request_id),
      CONSTRAINT ck_message_sequence CHECK(sequence >= 1),
      CONSTRAINT ck_message_role CHECK(role='user'),
      CONSTRAINT ck_message_language CHECK(language IN ('en','sw')),
      CONSTRAINT ck_message_content CHECK(char_length(btrim(content)) BETWEEN 1 AND 4000),
      CONSTRAINT ck_message_hash CHECK(request_hash ~ '^[0-9a-f]{64}$')
    );
    """
    for statement in ddl.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("""
    DO $grants$ BEGIN
      IF EXISTS (SELECT FROM pg_roles WHERE rolname='county_runtime') THEN
        GRANT SELECT,INSERT,DELETE ON conversations TO county_runtime;
        GRANT UPDATE(title,language,next_sequence,version,last_activity_at,updated_at,expires_at)
          ON conversations TO county_runtime;
        GRANT SELECT,INSERT ON messages TO county_runtime;
      END IF;
    END $grants$;
    """)


def downgrade() -> None:
    # Explicitly destructive: removes all conversations/messages, preserves identity.
    op.execute("DROP TABLE messages")
    op.execute("DROP TABLE conversations")
