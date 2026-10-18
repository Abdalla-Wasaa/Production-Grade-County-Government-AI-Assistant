// Synthetic persistence fixture; never used by production routing or a live API.
import { installServer } from '../auth/testServer';
import type { Conversation, Message } from './contracts';
export const firstId = '10000000-0000-4000-8000-000000000001';
export const secondId = '10000000-0000-4000-8000-000000000002';
const when = '2026-10-18T12:00:00Z';
export function installHistoryServer(count = 2, messageCount = 2) {
  const auth = installServer(true);
  const fallback = auth.fetcher.getMockImplementation()!;
  const records = new Map<string, Conversation>();
  const messages = new Map<string, Message[]>();
  const keys = new Map<string, Message>();
  let counter = 100;
  const calls: { path: string; init: RequestInit }[] = [];
  const response = (status: number, body: unknown = null, version?: number) =>
    new Response(status === 204 ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json', ...(version ? { ETag: `"${version}"` } : {}) },
    });
  for (let i = 1; i <= count; i++) {
    const id = `10000000-0000-4000-8000-${String(i).padStart(12, '0')}`;
    records.set(id, {
      id,
      title: 'Synthetic conversation ' + i,
      language: 'en',
      version: 1,
      created_at: when,
      updated_at: when,
      expires_at: '2026-11-17T12:00:00Z',
    });
    messages.set(
      id,
      Array.from({ length: messageCount }, (_, n) => ({
        id: `20000000-0000-4000-8000-${String(i * 100 + n + 1).padStart(12, '0')}`,
        conversation_id: id,
        sequence: n + 1,
        role: 'user',
        content: `Synthetic message ${n + 1}`,
        language: 'en',
        created_at: when,
      })),
    );
  }
  auth.fetcher.mockImplementation(async (url, init = {}) => {
    if (!url.startsWith('/api/v1/conversations')) return fallback(url, init);
    calls.push({ path: url, init });
    if (!new Headers(init.headers).get('Authorization')) return response(401);
    const parsed = new URL(url, 'http://127.0.0.1');
    const pieces = parsed.pathname.split('/').filter(Boolean);
    const id = pieces[3];
    const method = init.method ?? 'GET';
    if (!id) {
      if (method === 'POST') {
        const body = JSON.parse(init.body as string) as { title?: string; language: 'en' | 'sw' };
        const id = `10000000-0000-4000-8000-${String(++counter).padStart(12, '0')}`;
        const row: Conversation = {
          id,
          title: body.title ?? 'New conversation',
          language: body.language,
          version: 1,
          created_at: when,
          updated_at: when,
          expires_at: '2026-11-17T12:00:00Z',
        };
        records.set(id, row);
        messages.set(id, []);
        return response(201, row, 1);
      }
      const rows = [...records.values()];
      const offset = Number(parsed.searchParams.get('cursor') ?? 0);
      return response(200, {
        items: rows.slice(offset, offset + 20),
        next_cursor: offset + 20 < rows.length ? String(offset + 20) : null,
      });
    }
    const row = records.get(id);
    if (!row) return response(404);
    if (pieces[4] === 'messages') {
      const rows = messages.get(id)!;
      if (method === 'POST') {
        const body = JSON.parse(init.body as string) as { content: string };
        const key = id + ':' + new Headers(init.headers).get('Idempotency-Key');
        const replay = keys.get(key);
        if (replay)
          return replay.content === body.content
            ? response(200, replay, row.version)
            : response(409);
        const item: Message = {
          id: crypto.randomUUID(),
          conversation_id: id,
          sequence: rows.length + 1,
          role: 'user',
          content: body.content,
          language: row.language,
          created_at: when,
        };
        rows.push(item);
        keys.set(key, item);
        row.version++;
        return response(201, item, row.version);
      }
      const offset = Number(parsed.searchParams.get('cursor') ?? 0);
      return response(
        200,
        {
          items: rows.slice(offset, offset + 20),
          next_cursor: offset + 20 < rows.length ? String(offset + 20) : null,
        },
        row.version,
      );
    }
    if (method === 'PATCH') {
      if (new Headers(init.headers).get('If-Match') !== `"${row.version}"`) return response(412);
      const body = JSON.parse(init.body as string) as { title: string };
      row.title = body.title;
      row.version++;
    }
    if (method === 'DELETE') {
      records.delete(id);
      messages.delete(id);
      return response(204);
    }
    return response(200, row, row.version);
  });
  return { ...auth, records, messages, calls, response };
}
