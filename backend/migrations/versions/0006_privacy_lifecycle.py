"""Synthetic privacy controls; no default authorized operators or content copies."""

from alembic import op

revision = "0006_privacy_lifecycle"
down_revision = "0005_conversation_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    statements = [
        """CREATE TABLE privacy_operators (
          role_name VARCHAR(63) PRIMARY KEY, enabled BOOLEAN NOT NULL,
          can_hold BOOLEAN NOT NULL, can_request BOOLEAN NOT NULL, can_maintain BOOLEAN NOT NULL
        )""",
        """CREATE TABLE privacy_holds (
          id UUID PRIMARY KEY, user_id UUID NOT NULL, conversation_id UUID,
          scope VARCHAR(16) NOT NULL, reason VARCHAR(16) NOT NULL, case_ref UUID NOT NULL,
          audit_subject VARCHAR(64) NOT NULL, issuer VARCHAR(64) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL, reviewed_at TIMESTAMPTZ NOT NULL,
          review_due_at TIMESTAMPTZ NOT NULL, reviewed_by VARCHAR(64) NOT NULL,
          review_ref UUID NOT NULL, released_at TIMESTAMPTZ, released_by VARCHAR(64),
          release_ref UUID,
          CONSTRAINT ck_privacy_hold_scope CHECK(scope IN ('account','conversation')),
          CONSTRAINT ck_privacy_hold_reason CHECK(reason IN ('incident','records','review')),
          CONSTRAINT ck_hold_target CHECK((scope='account') = (conversation_id IS NULL)),
          CONSTRAINT ck_hold_review CHECK(review_due_at=reviewed_at+interval '30 days'),
          CONSTRAINT ck_hold_clock CHECK(created_at<=reviewed_at),
          CONSTRAINT ck_hold_release CHECK(released_at IS NULL OR released_at>=reviewed_at),
          CONSTRAINT ck_hold_digest CHECK(audit_subject ~ '^[a-f0-9]{64}$'),
          CONSTRAINT ck_hold_release_fields CHECK((released_at IS NULL AND released_by IS NULL
            AND release_ref IS NULL) OR (released_at IS NOT NULL AND released_by IS NOT NULL
            AND release_ref IS NOT NULL))
        )""",
        "CREATE INDEX ix_hold_account_active ON privacy_holds(user_id) WHERE released_at IS NULL",
        "CREATE INDEX ix_hold_review_active ON privacy_holds(review_due_at) "
        "WHERE released_at IS NULL",
        """CREATE TABLE privacy_deletion_requests (
          id UUID PRIMARY KEY, user_id UUID REFERENCES users(id) ON DELETE SET NULL,
          target_digest VARCHAR(64) NOT NULL, verification_ref UUID NOT NULL,
          accepted_by VARCHAR(64) NOT NULL, received_at TIMESTAMPTZ NOT NULL,
          accepted_at TIMESTAMPTZ NOT NULL,
          acknowledgement_due_at TIMESTAMPTZ NOT NULL, completion_due_at TIMESTAMPTZ NOT NULL,
          status VARCHAR(16) NOT NULL, completed_at TIMESTAMPTZ,
          CONSTRAINT ck_deletion_receipt CHECK(received_at<=accepted_at),
          CONSTRAINT ck_deletion_status CHECK(status IN ('accepted','held','completed')),
          CONSTRAINT ck_deletion_completion CHECK((status='completed')=(completed_at IS NOT NULL)),
          CONSTRAINT ck_deletion_live_user CHECK(status<>'completed' OR user_id IS NULL),
          CONSTRAINT ck_deletion_digest CHECK(target_digest ~ '^[a-f0-9]{64}$')
        )""",
        "CREATE UNIQUE INDEX uq_deletion_user ON privacy_deletion_requests(user_id)",
        "CREATE INDEX ix_deletion_due ON privacy_deletion_requests(completion_due_at)",
        """CREATE TABLE privacy_deletion_ledger (
          kind VARCHAR(16) NOT NULL, target_id UUID NOT NULL, deleted_at TIMESTAMPTZ NOT NULL,
          expires_at TIMESTAMPTZ NOT NULL, PRIMARY KEY(kind,target_id),
          CONSTRAINT ck_ledger_kind CHECK(kind IN ('account','conversation'))
        )""",
        "CREATE INDEX ix_privacy_ledger_expiry ON privacy_deletion_ledger(expires_at)",
        """CREATE TABLE privacy_maintenance_state (
          id INTEGER PRIMARY KEY CONSTRAINT ck_privacy_state_singleton CHECK(id=1),
          audit_key_sha256 VARCHAR(64), last_daily_at TIMESTAMPTZ,
          last_success_at TIMESTAMPTZ, last_hold_alert_at TIMESTAMPTZ
        )""",
        "INSERT INTO privacy_maintenance_state(id) VALUES(1)",
        """CREATE FUNCTION public.privacy_is_held(owner_id UUID, item_id UUID)
        RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER
          SET search_path=pg_catalog,public AS $$
          SELECT EXISTS(SELECT FROM public.privacy_holds h WHERE h.user_id=owner_id
            AND h.released_at IS NULL AND (h.scope='account' OR h.conversation_id=item_id))
        $$""",
        "REVOKE ALL ON FUNCTION public.privacy_is_held(UUID,UUID) FROM PUBLIC",
        """CREATE FUNCTION public.privacy_audit_key_matches(fingerprint TEXT)
          RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER
          SET search_path=pg_catalog,public AS $$
          SELECT audit_key_sha256 IS NULL OR audit_key_sha256=fingerprint
            FROM public.privacy_maintenance_state WHERE id=1
          $$""",
        "REVOKE ALL ON FUNCTION public.privacy_audit_key_matches(TEXT) FROM PUBLIC",
        """CREATE FUNCTION public.privacy_hold_change() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        DECLARE actor TEXT; subject_id UUID; operation TEXT;
        BEGIN
          PERFORM pg_advisory_xact_lock(724051902);
          actor := encode(sha256(convert_to(session_user::text,'UTF8')),'hex');
          IF TG_OP='DELETE' THEN
            IF OLD.released_at IS NULL OR OLD.released_at > clock_timestamp()-interval '90 days'
              OR NOT EXISTS(SELECT FROM public.privacy_operators WHERE role_name=session_user
                AND enabled AND can_maintain) THEN
              RAISE EXCEPTION 'Privacy operation denied' USING ERRCODE='42501';
            END IF;
            RETURN OLD;
          END IF;
          IF NOT EXISTS(SELECT FROM public.privacy_operators WHERE role_name=session_user
            AND enabled AND can_hold) THEN
            RAISE EXCEPTION 'Privacy operation denied' USING ERRCODE='42501';
          END IF;
          PERFORM id FROM public.users WHERE id=NEW.user_id FOR UPDATE;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'Privacy target unavailable' USING ERRCODE='23503';
          END IF;
          IF TG_OP='INSERT' THEN
            IF NEW.issuer<>actor OR NEW.reviewed_by<>actor OR NEW.released_at IS NOT NULL
              OR (NEW.scope='conversation' AND NOT EXISTS(SELECT FROM public.conversations
                WHERE id=NEW.conversation_id AND user_id=NEW.user_id)) THEN
              RAISE EXCEPTION 'Privacy operation denied' USING ERRCODE='42501';
            END IF;
            operation := 'privacy_hold_created';
          ELSE
            IF OLD.released_at IS NOT NULL OR
              ROW(NEW.id,NEW.user_id,NEW.conversation_id,NEW.scope,NEW.reason,NEW.case_ref,
                  NEW.audit_subject,NEW.issuer,NEW.created_at)
              IS DISTINCT FROM ROW(OLD.id,OLD.user_id,OLD.conversation_id,OLD.scope,OLD.reason,
                  OLD.case_ref,OLD.audit_subject,OLD.issuer,OLD.created_at) THEN
              RAISE EXCEPTION 'Privacy operation denied' USING ERRCODE='42501';
            END IF;
            IF NEW.released_at IS NOT NULL THEN
              IF NEW.released_by<>actor THEN
                RAISE EXCEPTION 'Privacy operation denied' USING ERRCODE='42501';
              END IF;
              operation := 'privacy_hold_released';
            ELSE
              IF NEW.reviewed_at<OLD.reviewed_at OR NEW.reviewed_by<>actor THEN
                RAISE EXCEPTION 'Privacy operation denied' USING ERRCODE='42501';
              END IF;
              operation := 'privacy_hold_reviewed';
            END IF;
          END IF;
          INSERT INTO public.auth_audit_events
            (id,occurred_at,actor,subject,action,outcome,request_id)
            VALUES(gen_random_uuid(),clock_timestamp(),actor,NEW.audit_subject,operation,'success',NEW.id);
          RETURN NEW;
        END $$""",
        "REVOKE ALL ON FUNCTION public.privacy_hold_change() FROM PUBLIC",
        """CREATE FUNCTION public.privacy_request_insert() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        DECLARE actor TEXT;
        BEGIN
          actor := encode(sha256(convert_to(session_user::text,'UTF8')),'hex');
          IF NOT EXISTS(SELECT FROM public.privacy_operators WHERE role_name=session_user
            AND enabled AND can_request) OR NEW.accepted_by<>actor OR NEW.user_id IS NULL
            OR NEW.status NOT IN ('accepted','held') OR NEW.completed_at IS NOT NULL THEN
            RAISE EXCEPTION 'Privacy operation denied' USING ERRCODE='42501';
          END IF;
          PERFORM id FROM public.users WHERE id=NEW.user_id AND status='disabled' FOR UPDATE;
          IF NOT FOUND OR EXISTS(SELECT FROM public.auth_sessions
            WHERE user_id=NEW.user_id AND revoked_at IS NULL) THEN
            RAISE EXCEPTION 'Privacy revocation required' USING ERRCODE='23514';
          END IF;
          INSERT INTO public.auth_audit_events
            (id,occurred_at,actor,subject,action,outcome,request_id)
            VALUES(gen_random_uuid(),clock_timestamp(),actor,NEW.target_digest,
                   'privacy_delete_accepted','success',NEW.id);
          RETURN NEW;
        END $$""",
        "REVOKE ALL ON FUNCTION public.privacy_request_insert() FROM PUBLIC",
        """CREATE TRIGGER privacy_request_insert BEFORE INSERT ON privacy_deletion_requests
          FOR EACH ROW EXECUTE FUNCTION public.privacy_request_insert()""",
        """CREATE TRIGGER privacy_hold_change BEFORE INSERT OR UPDATE OR DELETE
          ON privacy_holds FOR EACH ROW EXECUTE FUNCTION public.privacy_hold_change()""",
        """CREATE FUNCTION public.privacy_guard_delete() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
        DECLARE owner_id UUID; item_id UUID; blocked BOOLEAN := false; kind_name TEXT;
        BEGIN
          IF TG_TABLE_NAME='users' THEN
            owner_id := OLD.id; kind_name := 'account';
            SELECT EXISTS(SELECT FROM public.privacy_holds WHERE user_id=owner_id
              AND released_at IS NULL) INTO blocked;
          ELSIF TG_TABLE_NAME='conversations' THEN
            owner_id := OLD.user_id; item_id := OLD.id; kind_name := 'conversation';
          ELSIF TG_TABLE_NAME='auth_sessions' THEN owner_id := OLD.user_id;
          ELSIF TG_TABLE_NAME='invitations' THEN
            SELECT EXISTS(SELECT FROM public.privacy_holds h JOIN public.users u ON u.id=h.user_id
              WHERE h.scope='account' AND h.released_at IS NULL AND
              (u.id=OLD.target_user_id OR u.id=OLD.accepted_user_id
                OR u.email_normalized=OLD.email_normalized)) INTO blocked;
          ELSIF TG_TABLE_NAME='auth_audit_events' THEN
            PERFORM pg_advisory_xact_lock(724051902);
            SELECT EXISTS(SELECT FROM public.privacy_holds WHERE audit_subject=OLD.subject
              AND released_at IS NULL) INTO blocked;
          END IF;
          IF owner_id IS NOT NULL THEN
            PERFORM id FROM public.users WHERE id=owner_id FOR UPDATE;
            IF TG_TABLE_NAME='conversations' THEN
              blocked := public.privacy_is_held(owner_id,item_id);
            ELSIF TG_TABLE_NAME='auth_sessions' THEN
              SELECT EXISTS(SELECT FROM public.privacy_holds WHERE user_id=owner_id
                AND scope='account' AND released_at IS NULL) INTO blocked;
            END IF;
          END IF;
          IF blocked THEN
            RAISE EXCEPTION 'Deletion restricted' USING ERRCODE='23514';
          END IF;
          -- OLD has the triggering table's row type. Keep user-only fields in
          -- a separate statement so PostgreSQL never resolves them for other tables.
          IF kind_name='account' THEN
            IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname=session_user AND rolsuper)
              AND NOT EXISTS(SELECT FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner
                WHERE c.oid='public.users'::regclass AND r.rolname=session_user)
              AND (OLD.status<>'disabled' OR NOT EXISTS(SELECT FROM public.privacy_deletion_requests
                WHERE user_id=OLD.id AND status IN ('accepted','held'))) THEN
              RAISE EXCEPTION 'Verified deletion request required' USING ERRCODE='42501';
            END IF;
          END IF;
          IF kind_name IS NOT NULL THEN
            INSERT INTO public.privacy_deletion_ledger(kind,target_id,deleted_at,expires_at)
              VALUES(kind_name,OLD.id,clock_timestamp(),clock_timestamp()+interval '37 days')
              ON CONFLICT DO NOTHING;
            INSERT INTO public.auth_audit_events
            (id,occurred_at,actor,subject,action,outcome,request_id)
              VALUES(gen_random_uuid(),clock_timestamp(),
                encode(sha256(convert_to(session_user::text,'UTF8')),'hex'),
                encode(sha256(convert_to(OLD.id::text,'UTF8')),'hex'),
                'privacy_'||kind_name||'_deleted','success',gen_random_uuid());
          END IF;
          RETURN OLD;
        END $$""",
        "REVOKE ALL ON FUNCTION public.privacy_guard_delete() FROM PUBLIC",
    ]
    for statement in statements:
        op.execute(statement)
    for table in ("users", "conversations", "auth_sessions", "invitations", "auth_audit_events"):
        op.execute(
            f"CREATE TRIGGER privacy_guard_delete BEFORE DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION public.privacy_guard_delete()"
        )
    op.execute("""
    DO $$ BEGIN
      IF EXISTS(SELECT FROM pg_roles WHERE rolname='county_runtime') THEN
        GRANT EXECUTE ON FUNCTION public.privacy_is_held(UUID,UUID) TO county_runtime;
        GRANT EXECUTE ON FUNCTION public.privacy_audit_key_matches(TEXT) TO county_runtime;
      END IF;
    END $$;
    """)


def downgrade() -> None:
    # Removing safeguards is forbidden while relevant live evidence/requests remain.
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT FROM privacy_holds WHERE released_at IS NULL
                  OR released_at>clock_timestamp()-interval '90 days')
        OR EXISTS(SELECT FROM privacy_deletion_requests WHERE status<>'completed'
                  OR completed_at>clock_timestamp()-interval '90 days')
        OR EXISTS(SELECT FROM privacy_deletion_ledger WHERE expires_at>clock_timestamp()) THEN
        RAISE EXCEPTION 'Privacy controls still required; downgrade refused';
      END IF;
    END $$""")
    for table in ("users", "conversations", "auth_sessions", "invitations", "auth_audit_events"):
        op.execute(f"DROP TRIGGER privacy_guard_delete ON {table}")
    op.execute("DROP FUNCTION public.privacy_guard_delete()")
    op.execute("DROP FUNCTION public.privacy_audit_key_matches(TEXT)")
    op.execute("""DO $$ DECLARE principal RECORD; BEGIN
      FOR principal IN SELECT role_name FROM privacy_operators p JOIN pg_roles r
        ON r.rolname=p.role_name WHERE p.can_maintain LOOP
        EXECUTE format('REVOKE DELETE ON public.users,public.conversations FROM %I',
                       principal.role_name);
        EXECUTE format('REVOKE UPDATE(updated_at) ON public.users,public.conversations FROM %I',
                       principal.role_name);
        EXECUTE format('REVOKE SELECT(id,status,email_normalized) ON public.users FROM %I',
                       principal.role_name);
        EXECUTE format('REVOKE SELECT(id,user_id,expires_at) ON public.conversations FROM %I',
                       principal.role_name);
      END LOOP;
      FOR principal IN SELECT role_name FROM privacy_operators p JOIN pg_roles r
        ON r.rolname=p.role_name WHERE p.can_hold OR p.can_request LOOP
        EXECUTE format('REVOKE SELECT(id,user_id) ON public.conversations FROM %I',
                       principal.role_name);
      END LOOP;
    END $$""")
    op.execute("DROP TABLE privacy_maintenance_state")
    op.execute("DROP TABLE privacy_deletion_ledger")
    op.execute("DROP TABLE privacy_deletion_requests")
    op.execute("DROP FUNCTION public.privacy_request_insert()")
    op.execute("DROP FUNCTION public.privacy_is_held(UUID,UUID)")
    op.execute("DROP TABLE privacy_holds")
    op.execute("DROP FUNCTION public.privacy_hold_change()")
    op.execute("DROP TABLE privacy_operators")
