# ADR 0003: Separate user-message persistence from AI generation

Status: owner approved the contract amendment on 18 October 2026; implementation
prepared under issue #19, runtime verification pending separate authorization.

## Context

The Phase 0 send contract coupled POST /conversations/{id}/messages to reserving a
user/assistant pair and invoking a provider. P2-03 must persist messages without AI;
issue #19 required resolving this conflict before implementation. Auth contracts
and the seven required CI checks remain unchanged.

## Decision

Use that POST path for user-only persistence with a required UUID Idempotency-Key
header and strict content-only body. Return the persisted Message (201 first write,
200 identical replay); reject different content with the same key (409). Never
accept role/ownership/counter fields from clients. An unanswered message is valid;
multiple unanswered messages are permitted without placeholder assistant rows.

Use explicit conversations/messages schema revision 0005. Enforce ownership and
expiry on every operation. Lock account -> session -> conversation, retain unique
sequence/key constraints, and commit content-free audit together with writes. Keep
bounded signed-cursor history and existing optimistic PATCH ETags. The shared
identity dependency commits before the response is sent; database/audit failures
roll back rather than returning false successful writes.

Document generation as a separate future operation. Its exact path and send/retry,
backlog, assistant state, quota and recovery semantics require Phase 3 design
approval; no generation/retry route is implemented here.

## Consequences and alternatives

This changes the previous unimplemented Phase 0 send contract with explicit owner
approval. It avoids fake answers and premature provider abstractions. Reusing the
historical paired schema would create misleading pending assistant resources;
leaving writes out would not satisfy the authorized milestone. The user-only CHECK
will need a reviewed expansion for real assistant messages in Phase 3.

Per-account serialization trades throughput for straightforward cap, ownership,
revocation and ordering correctness. Keyed canonical hashes support retries without
logging content, but are not encryption; database access remains restricted.
No dependency changes, production approval or automatic exposure acceptance follow
from this ADR. P2-05 still owns physical retention purge and account lifecycle.
