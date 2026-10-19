import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthClient } from '../auth/client';
import { ConversationClient } from './client';
import { firstId, installHistoryServer } from './testServer';
let cleanup = () => {};
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
async function setup(count = 2) {
  const server = installHistoryServer(count);
  const auth = new AuthClient();
  const stop = auth.start();
  await auth.restore();
  const client = new ConversationClient(auth, auth.getSessionScope());
  const close = client.start();
  cleanup = () => {
    close();
    stop();
    server.restore();
  };
  return { server, auth, client };
}
describe('authenticated persistence transport', () => {
  it('uses bearer only, no-store and no redirects without exposing tokens', async () => {
    const { server, client } = await setup();
    expect((await client.list()).items).toHaveLength(2);
    const init = server.calls[0]!.init;
    expect(new Headers(init.headers).get('Authorization')).toMatch(/^Bearer /);
    expect(init.credentials).toBe('omit');
    expect(init.cache).toBe('no-store');
    expect(init.redirect).toBe('error');
    expect(new Headers(init.headers).has('X-CSRF-Token')).toBe(false);
    expect(localStorage.length).toBe(0);
  });
  it('persists once after a lost acknowledgement by reusing the exact key', async () => {
    const { server, client } = await setup();
    const original = server.fetcher.getMockImplementation()!;
    let lost = true;
    server.fetcher.mockImplementation(async (url, init) => {
      const result = await original(url, init);
      if (url.includes('/messages') && init?.method === 'POST' && lost) {
        lost = false;
        throw new TypeError('Synthetic connection lost');
      }
      return result;
    });
    await expect(client.send(firstId, 'Synthetic retry')).rejects.toThrow();
    expect(client.pending(firstId)?.status).toBe('uncertain');
    expect(() => client.send(firstId, 'Changed')).toThrow();
    const result = await client.send(firstId, 'Synthetic retry');
    expect(result.value.sequence).toBe(3);
    const calls = server.calls.filter((c) => c.init.method === 'POST');
    expect(calls).toHaveLength(2);
    expect(new Headers(calls[0]!.init.headers).get('Idempotency-Key')).toBe(
      new Headers(calls[1]!.init.headers).get('Idempotency-Key'),
    );
    expect(server.messages.get(firstId)).toHaveLength(3);
    expect(client.pending(firstId)).toBeUndefined();
  });
  it('coalesces concurrent duplicate submissions', async () => {
    const { server, client } = await setup();
    const one = client.send(firstId, 'One synthetic question');
    const two = client.send(firstId, 'One synthetic question');
    expect(one).toBe(two);
    await one;
    expect(server.calls.filter((c) => c.init.method === 'POST')).toHaveLength(1);
  });
  it('does not clear a valid session after history is unavailable', async () => {
    const { server, auth, client } = await setup();
    server.fetcher.mockResolvedValueOnce(server.response(503));
    await expect(client.list()).rejects.toThrow();
    expect(auth.getSnapshot().status).toBe('authenticated');
  });
  it('invalidates session and uncertain state on 401', async () => {
    const { server, auth, client } = await setup();
    server.fetcher.mockResolvedValueOnce(server.response(401));
    await expect(client.list()).rejects.toThrow();
    expect(auth.getSnapshot().status).toBe('guest');
    expect(client.pending(firstId)).toBeUndefined();
  });
  it('rejects late old-account responses after sign-out', async () => {
    const { server, auth, client } = await setup();
    const original = server.fetcher.getMockImplementation()!;
    let release!: (value: Response) => void;
    server.fetcher.mockImplementation((url, init) =>
      url.startsWith('/api/v1/conversations')
        ? new Promise((resolve) => {
            release = resolve;
          })
        : original(url, init),
    );
    const waiting = client.list();
    const caught = expect(waiting).rejects.toThrow();
    await vi.waitFor(() => expect(release).toBeDefined());
    // The cookie lock serializes network work, so simulate a cross-tab invalidation.
    const other = new BroadcastChannel('county.auth.invalidate.v1');
    other.postMessage('invalidate');
    other.close();
    release(server.response(200, { items: [...server.records.values()], next_cursor: null }));
    await caught;
    expect(auth.getSnapshot().status).toBe('guest');
  });
  it('keeps metadata ETags, paginates and maps stale writes without replay', async () => {
    const { client } = await setup(21);
    const a = await client.list();
    expect(a.items).toHaveLength(20);
    expect((await client.list(a.next_cursor!)).items).toHaveLength(1);
    const row = await client.get(firstId);
    await client.rename(firstId, 'Renamed', row.etag);
    await expect(client.rename(firstId, 'Stale', row.etag)).rejects.toMatchObject({
      issue: 'conflict',
    });
    await client.remove(firstId);
    await expect(client.get(firstId)).rejects.toMatchObject({ issue: 'missing' });
  });
  it('refreshes expired access through the existing serialized auth manager', async () => {
    const { server, auth, client } = await setup();
    const scope = auth.getSessionScope();
    const future = Date.now() + 880000;
    vi.spyOn(Date, 'now').mockReturnValue(future);
    await client.list();
    expect(auth.getSessionScope()).toBe(scope);
    expect(server.fetcher.mock.calls.filter(([url]) => url.endsWith('/refresh'))).toHaveLength(2);
  });
  it('discards a delayed old-account response body without clearing the new account', async () => {
    const { server, auth, client } = await setup();
    const original = server.fetcher.getMockImplementation()!;
    let body!: ReadableStreamDefaultController<Uint8Array>;
    server.fetcher.mockImplementation(async (url, init) => {
      if (url.startsWith('/api/v1/conversations'))
        return new Response(
          new ReadableStream<Uint8Array>({
            start(controller) {
              body = controller;
            },
          }),
          { headers: { 'Content-Type': 'application/json' } },
        );
      if (url.endsWith('/login')) {
        const response = await original(url, init);
        const value = (await response.json()) as { user: { id: string; email: string } };
        return server.response(200, {
          ...value,
          user: {
            ...value.user,
            id: '00000000-0000-4000-8000-000000000099',
            email: 'other@example.invalid',
          },
        });
      }
      return original(url, init);
    });
    const result = client.list();
    const rejected = expect(result).rejects.toThrow();
    await vi.waitFor(() => expect(body).toBeDefined());
    await auth.login('other@example.invalid', 'Synthetic unrelated password');
    body.enqueue(
      new TextEncoder().encode(
        JSON.stringify({ items: [...server.records.values()], next_cursor: null }),
      ),
    );
    body.close();
    await rejected;
    expect(auth.getSnapshot().user?.id).toBe('00000000-0000-4000-8000-000000000099');
    expect(client.pending(firstId)).toBeUndefined();
  });
  it('keeps a held conversation and maps safe deletion restriction', async () => {
    const { client, server } = await setup();
    server.fetcher.mockResolvedValueOnce(
      server.response(409, { error: { code: 'deletion_restricted' } }),
    );
    await expect(client.remove(firstId)).rejects.toMatchObject({ issue: 'restricted' });
    expect(server.records.has(firstId)).toBe(true);
  });
  it('does not allow bearer requests outside the conversation family', async () => {
    const { auth } = await setup();
    await expect(
      auth.conversationRequest(auth.getSessionScope(), 'https://example.invalid/collect'),
    ).rejects.toThrow();
  });
});
