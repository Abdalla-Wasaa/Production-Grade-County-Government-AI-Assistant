// Synthetic in-memory HTTP fixture for client/component tests only.
import { vi } from 'vitest';
export const testUser = {
  id: '00000000-0000-4000-8000-000000000001',
  email: 'sample@example.invalid',
  role: 'citizen',
  preferred_language: 'en',
};
export const testSession = {
  id: '00000000-0000-4000-8000-000000000002',
  created_at: '2026-10-17T12:00:00Z',
  expires_at: '2026-10-24T12:00:00Z',
  last_used_at: '2026-10-17T12:00:00Z',
  is_current: true,
};
export function installServer(initialSession = false) {
  let loggedIn = initialSession;
  let nonce = 0;
  let active = 0;
  let maxActive = 0;
  let tail = Promise.resolve();
  const channelMessages: unknown[] = [];
  class Channel {
    static all = new Set<Channel>();
    onmessage: ((event: MessageEvent<unknown>) => void) | null = null;
    constructor() {
      Channel.all.add(this);
    }
    postMessage(value: unknown) {
      channelMessages.push(value);
      for (const c of Channel.all)
        if (c !== this) c.onmessage?.({ data: value } as MessageEvent<unknown>);
    }
    close() {
      Channel.all.delete(this);
    }
  }
  vi.stubGlobal('BroadcastChannel', Channel);
  const original = Object.getOwnPropertyDescriptor(navigator, 'locks');
  Object.defineProperty(navigator, 'locks', {
    configurable: true,
    value: {
      request: (_name: string, _options: unknown, work: () => Promise<unknown>) => {
        const next = tail.then(async () => {
          active++;
          maxActive = Math.max(maxActive, active);
          try {
            return await work();
          } finally {
            active--;
          }
        });
        tail = next.then(
          () => {},
          () => {},
        );
        return next;
      },
    },
  });
  const response = (status: number, body: unknown = null) =>
    new Response(status === 204 ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  const fetcher = vi.fn(async (url: string, init: RequestInit = {}): Promise<Response> => {
    await Promise.resolve();
    const path = url.replace('/api/v1/auth', '');
    const headers = new Headers(init.headers);
    if (path === '/csrf') return response(200, { csrf_token: 'synthetic-csrf-' + ++nonce });
    if (init.method !== 'GET' && headers.get('X-CSRF-Token') !== 'synthetic-csrf-' + nonce)
      return response(403);
    if (path === '/activate') return response(204);
    if (path === '/login') loggedIn = true;
    if (path === '/login' || path === '/refresh')
      return loggedIn
        ? response(200, {
            access_token: 'synthetic-access-' + nonce,
            token_type: 'bearer',
            expires_in: 900,
            user: testUser,
          })
        : response(401);
    if (path === '/logout' || path === '/logout-all' || path.startsWith('/sessions/')) {
      loggedIn = false;
      return response(204);
    }
    if (!loggedIn || !headers.get('Authorization')) return response(401);
    if (path === '/me') return response(200, testUser);
    if (path.startsWith('/sessions'))
      return response(200, { items: [testSession], next_cursor: null });
    return response(404);
  });
  vi.stubGlobal('fetch', fetcher);
  return {
    fetcher,
    response,
    channelMessages,
    maxActive: () => maxActive,
    restore: () => {
      if (original) Object.defineProperty(navigator, 'locks', original);
      else Reflect.deleteProperty(navigator, 'locks');
    },
  };
}
