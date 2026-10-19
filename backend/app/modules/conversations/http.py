"""Bearer-only persistence boundary; scoped auth cookies are never authority here."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response

from app.core.errors import ErrorResponse
from app.modules.conversations.schemas import (
    AddMessage,
    ConversationItem,
    ConversationList,
    CreateConversation,
    MessageItem,
    MessageList,
    UpdateConversation,
)
from app.modules.conversations.service import Conversations
from app.modules.identity.http import Service, bearer

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


async def conversations(request: Request, identity: Service) -> Conversations:
    user, _family = await bearer(request, identity)
    return Conversations(identity, user)


Store = Annotated[Conversations, Depends(conversations)]
Limit = Annotated[int, Query(ge=1, le=100)]
Cursor = Annotated[str | None, Query(max_length=2048)]


@router.post("", status_code=201, response_model=ConversationItem)
async def create(body: CreateConversation, response: Response, store: Store) -> ConversationItem:
    row = await store.create(body)
    response.headers["Location"] = f"/api/v1/conversations/{row.id}"
    response.headers["ETag"] = f'"{row.version}"'
    return ConversationItem.model_validate(row)


@router.get("", response_model=ConversationList)
async def listing(store: Store, limit: Limit = 20, cursor: Cursor = None) -> ConversationList:
    return await store.listing(limit, cursor)


@router.get("/{id}", response_model=ConversationItem)
async def retrieve(id: UUID, response: Response, store: Store) -> ConversationItem:
    row = await store.owned(id)
    response.headers["ETag"] = f'"{row.version}"'
    return ConversationItem.model_validate(row)


@router.patch("/{id}", response_model=ConversationItem)
async def update(
    id: UUID,
    body: UpdateConversation,
    response: Response,
    store: Store,
    if_match: Annotated[str | None, Header(max_length=64)] = None,
) -> ConversationItem:
    row = await store.owned(id)
    await store.update(row, body, if_match)
    response.headers["ETag"] = f'"{row.version}"'
    return ConversationItem.model_validate(row)


@router.delete("/{id}", status_code=204, responses={409: {"model": ErrorResponse}})
async def delete(id: UUID, store: Store) -> Response:
    await store.delete(await store.owned(id))
    return Response(status_code=204)


@router.post("/{id}/messages", status_code=201, response_model=MessageItem)
async def add(
    id: UUID,
    body: AddMessage,
    response: Response,
    store: Store,
    idempotency_key: Annotated[UUID, Header()],
) -> MessageItem:
    row = await store.owned(id)
    message, replayed = await store.add(row, body, idempotency_key)
    response.headers["ETag"] = f'"{row.version}"'
    if replayed:
        response.status_code = 200
        response.headers["Idempotency-Replayed"] = "true"
    return MessageItem.model_validate(message)


@router.get("/{id}/messages", response_model=MessageList)
async def history(
    id: UUID,
    response: Response,
    store: Store,
    limit: Limit = 20,
    cursor: Cursor = None,
) -> MessageList:
    row = await store.owned(id)
    response.headers["ETag"] = f'"{row.version}"'
    return await store.history(row, limit, cursor)
