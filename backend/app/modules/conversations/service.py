"""Short database-only transactions; account -> family -> conversation lock order."""

import hashlib
import json
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, or_, select

from app.modules.conversations.models import Conversation, Message
from app.modules.conversations.schemas import (
    AddMessage,
    ConversationItem,
    ConversationList,
    CreateConversation,
    MessageItem,
    MessageList,
    UpdateConversation,
)
from app.modules.identity.models import User
from app.modules.identity.security import AuthFailure
from app.modules.identity.service import Identity
from app.modules.privacy.service import conversation_held


class Conversations:
    def __init__(self, identity: Identity, user: User):
        self.identity, self.user = identity, user
        self.db, self.tokens = identity.db, identity.tokens

    async def owned(self, key: UUID) -> Conversation:
        row = await self.db.scalar(
            select(Conversation)
            .where(
                Conversation.id == key,
                Conversation.user_id == self.user.id,
                Conversation.expires_at > self.tokens.clock(),
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        # Recheck time after acquiring the lock, not just before any lock wait.
        if row is None or row.expires_at <= self.tokens.clock():
            raise AuthFailure(404, "not_found")
        return row

    async def event(self, action: str) -> None:
        await self.identity.event(action, "success", str(self.user.id))

    async def create(self, body: CreateConversation) -> Conversation:
        now = self.tokens.clock()
        count = await self.db.scalar(
            select(func.count())
            .select_from(Conversation)
            .where(
                Conversation.user_id == self.user.id,
                Conversation.expires_at > now,
            )
        )
        # authenticate() holds this user's row lock across count + insert.
        if count is not None and count >= 100:
            raise AuthFailure(429, "storage_limit")
        language = body.language or self.user.preferred_language
        row = Conversation(
            user_id=self.user.id,
            title=body.title or ("Mazungumzo mapya" if language == "sw" else "New conversation"),
            language=language,
            created_at=now,
            updated_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(days=30),
        )
        self.db.add(row)
        await self.db.flush()
        await self.event("conversation_created")
        return row

    async def listing(self, limit: int, cursor: str | None) -> ConversationList:
        query = select(Conversation).where(
            Conversation.user_id == self.user.id,
            Conversation.expires_at > self.tokens.clock(),
        )
        if cursor:
            try:
                data = self.tokens.context(cursor, "conversation_cursor", str(self.user.id))
                updated, key = datetime.fromisoformat(data["updated_at"]), UUID(data["id"])
                if updated.tzinfo is None:
                    raise ValueError
            except (AuthFailure, ValueError, KeyError, TypeError):
                raise AuthFailure(422, "validation_error") from None
            query = query.where(
                or_(
                    Conversation.updated_at < updated,
                    and_(
                        Conversation.updated_at == updated,
                        Conversation.id < key,
                    ),
                )
            )
        rows = list(
            (
                await self.db.scalars(
                    query.order_by(
                        Conversation.updated_at.desc(),
                        Conversation.id.desc(),
                    ).limit(limit + 1)
                )
            ).all()
        )
        more = len(rows) > limit
        rows = rows[:limit]
        next_cursor = None
        if more:
            last = rows[-1]
            next_cursor = self.tokens.sign_context(
                "conversation_cursor",
                str(self.user.id),
                300,
                updated_at=last.updated_at.isoformat(),
                id=str(last.id),
            )
        return ConversationList(
            items=[ConversationItem.model_validate(row) for row in rows],
            next_cursor=next_cursor,
        )

    async def update(self, row: Conversation, body: UpdateConversation, match: str | None) -> None:
        if match is None:
            raise AuthFailure(428, "version_required")
        if match != f'"{row.version}"':
            raise AuthFailure(412, "version_conflict")
        if body.title is not None:
            row.title = body.title
        if body.language is not None:
            row.language = body.language
        row.version += 1
        row.updated_at = max(row.updated_at, self.tokens.clock())
        await self.event("conversation_updated")
        await self.db.flush()

    async def delete(self, row: Conversation) -> None:
        if await conversation_held(self.db, self.user.id, row.id):
            await self.identity.event("privacy_delete_denied", "denied", str(self.user.id))
            raise AuthFailure(409, "deletion_restricted")
        await self.db.delete(row)
        await self.event("conversation_deleted")
        await self.db.flush()

    async def add(self, row: Conversation, body: AddMessage, key: UUID) -> tuple[Message, bool]:
        # The path scopes keys; hash only canonical normalized content, never language
        # or mutable metadata, so a retry after rename/language change remains stable.
        digest = hashlib.sha256(
            json.dumps(
                {"content": body.content},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode()
        ).hexdigest()
        existing = await self.db.scalar(
            select(Message).where(
                Message.conversation_id == row.id,
                Message.client_request_id == key,
            )
        )
        if existing:
            if existing.request_hash != digest:
                raise AuthFailure(409, "idempotency_conflict")
            return existing, True
        if row.next_sequence > 1000:
            raise AuthFailure(429, "storage_limit")
        now = self.tokens.clock()
        message = Message(
            conversation_id=row.id,
            sequence=row.next_sequence,
            role="user",
            content=body.content,
            language=row.language,
            client_request_id=key,
            request_hash=digest,
            created_at=now,
        )
        self.db.add(message)
        row.next_sequence += 1
        row.version += 1
        row.last_activity_at = max(row.last_activity_at, now)
        row.updated_at = max(row.updated_at, now)
        row.expires_at = min(
            row.created_at + timedelta(days=90), row.last_activity_at + timedelta(days=30)
        )
        await self.event("message_created")
        await self.db.flush()
        return message, False

    async def history(self, row: Conversation, limit: int, cursor: str | None) -> MessageList:
        query = select(Message).where(Message.conversation_id == row.id)
        if cursor:
            try:
                data = self.tokens.context(cursor, "message_cursor", f"{self.user.id}:{row.id}")
                sequence = data["sequence"]
                if type(sequence) is not int or sequence < 1:
                    raise ValueError
            except (AuthFailure, ValueError, KeyError, TypeError):
                raise AuthFailure(422, "validation_error") from None
            query = query.where(Message.sequence > sequence)
        rows = list(
            (await self.db.scalars(query.order_by(Message.sequence).limit(limit + 1))).all()
        )
        more = len(rows) > limit
        rows = rows[:limit]
        next_cursor = None
        if more:
            next_cursor = self.tokens.sign_context(
                "message_cursor",
                f"{self.user.id}:{row.id}",
                300,
                sequence=rows[-1].sequence,
            )
        return MessageList(
            items=[MessageItem.model_validate(row) for row in rows], next_cursor=next_cursor
        )
