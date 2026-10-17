import { afterEach, describe, expect, it, vi } from 'vitest';
import { AuthClient } from './client';
import { safeReturn } from './contracts';
import { installServer, testUser, testSession } from './testServer';
let cleanup = () => {};
afterEach(() => {
  cleanup();
});
function setup(session = false) {
  const server = installServer(session);
  cleanup = server.restore;
  return server;
}
describe('authentication HTTP boundary', () => {
  it('restores with CSRF, validates current user, and never persists secrets', async () => {
    const s = setup(true);
    const client = new AuthClient();
    await client.restore();
    expect(client.getSnapshot().user).toEqual(testUser);
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
    const calls = s.fetcher.mock.calls;
    expect(calls.map(([url]) => url)).toEqual([
      '/api/v1/auth/csrf',
      '/api/v1/auth/refresh',
      '/api/v1/auth/me',
    ]);
    for (const [, init] of calls) {
      expect(init?.credentials).toBe('same-origin');
      expect(init?.cache).toBe('no-store');
      expect(init?.redirect).toBe('error');
    }
  });
  it('serializes shared-cookie refresh and CSRF across two tabs and clears both on logout', async () => {
    const s = setup(true);
    const a = new AuthClient();
    const b = new AuthClient();
    const stopA = a.start();
    const stopB = b.start();
    try {
      await Promise.all([a.restore(), b.restore()]);
      expect(s.maxActive()).toBe(1);
      expect(a.getSnapshot().status).toBe('authenticated');
      expect(b.getSnapshot().status).toBe('authenticated');
      await a.logout();
      expect(a.getSnapshot().user).toBeNull();
      expect(b.getSnapshot().user).toBeNull();
      expect(s.channelMessages).toEqual(['invalidate']);
    } finally {
      stopA();
      stopB();
    }
  });
  it('coalesces restoration and refreshes an expired access token once per serialized caller', async () => {
    const s = setup(true);
    const client = new AuthClient();
    await Promise.all([client.restore(), client.restore()]);
    expect(s.fetcher.mock.calls.filter(([u]) => u.endsWith('/refresh'))).toHaveLength(1);
    const clock = Date.now();
    vi.spyOn(Date, 'now').mockReturnValue(clock + 900000);
    await Promise.all([client.currentUser(), client.currentUser()]);
    expect(s.fetcher.mock.calls.filter(([u]) => u.endsWith('/refresh'))).toHaveLength(2);
  });
  it('does not automatically retry an ambiguous refresh response', async () => {
    const s = setup(true);
    const original = s.fetcher.getMockImplementation();
    s.fetcher.mockImplementation(async (url, init) => {
      if (url.endsWith('/refresh')) throw new Error('secret must not escape');
      return original!(url, init);
    });
    const client = new AuthClient();
    await expect(client.restore()).rejects.toMatchObject({ issue: 'unavailable' });
    await expect(client.restore()).rejects.toMatchObject({ issue: 'expired' });
    expect(s.fetcher.mock.calls.filter(([u]) => u.endsWith('/refresh'))).toHaveLength(1);
    expect(client.getSnapshot().user).toBeNull();
  });
  it.each([
    [403, 'csrf'],
    [429, 'rateLimited'],
    [503, 'unavailable'],
  ] as const)('safely handles HTTP %s without reflecting payload', async (status, issue) => {
    const s = setup();
    s.fetcher.mockResolvedValue(s.response(status, { password: 'private-reflected-data' }));
    const client = new AuthClient();
    await expect(
      client.login('sample@example.invalid', 'not-a-real-password'),
    ).rejects.toMatchObject({ issue });
    expect(JSON.stringify(client.getSnapshot())).not.toContain('private-reflected-data');
  });
  it('activates without auto-login, sends exact notice and no public role', async () => {
    const s = setup();
    const client = new AuthClient();
    await client.activate('a'.repeat(43), 'Synthetic-example-2026', 'sw');
    expect(client.getSnapshot().status).toBe('guest');
    const call = s.fetcher.mock.calls.find(([u]) => u.endsWith('/activate'))!;
    expect(JSON.parse(call[1]!.body as string)).toEqual({
      token: 'a'.repeat(43),
      password: 'Synthetic-example-2026',
      preferred_language: 'sw',
      privacy_notice_version: 'synthetic-v1',
      privacy_notice_acknowledged: true,
    });
    expect(s.fetcher.mock.calls.some(([u]) => u.endsWith('/login'))).toBe(false);
  });
  it('lists sessions and clears identity after current-session revocation', async () => {
    setup(true);
    const client = new AuthClient();
    await client.restore();
    expect((await client.sessions()).items).toHaveLength(1);
    await client.revoke(testSession.id, true);
    expect(client.getSnapshot().user).toBeNull();
  });
  it('does not claim server revocation when logout is unavailable', async () => {
    const s = setup(true);
    const client = new AuthClient();
    await client.restore();
    s.fetcher.mockRejectedValue(new Error('outage'));
    await expect(client.logout(true)).rejects.toMatchObject({ issue: 'logoutFailed' });
    expect(client.getSnapshot()).toMatchObject({ user: null, issue: 'logoutFailed' });
  });
  it('fails closed without browser-wide locks', async () => {
    setup();
    Reflect.deleteProperty(navigator, 'locks');
    const client = new AuthClient();
    await expect(
      client.login('sample@example.invalid', 'not-a-real-password'),
    ).rejects.toMatchObject({ issue: 'unsupported' });
  });
  it.each([
    '//evil.invalid',
    'https://evil.invalid',
    '/%2f%2fevil.invalid',
    '/login?next=evil',
    null,
  ])('allows no external/encoded return path: %s', (value) => {
    expect(safeReturn(value)).toBe('/account');
  });
});

it('can retry an outage before refresh begins, without replaying a rotation', async () => {
  const s = setup(true);
  const client = new AuthClient();
  const original = s.fetcher.getMockImplementation();
  s.fetcher.mockImplementationOnce(() => Promise.resolve(s.response(503)));
  await expect(client.restore()).rejects.toMatchObject({ issue: 'unavailable' });
  s.fetcher.mockImplementation(original!);
  await client.restore();
  expect(client.getSnapshot().user).toEqual(testUser);
});
it('rejects used or expired invitations with the same safe response', async () => {
  const s = setup();
  const original = s.fetcher.getMockImplementation();
  s.fetcher.mockImplementation((url, init) =>
    url.endsWith('/activate') ? Promise.resolve(s.response(400)) : original!(url, init),
  );
  const client = new AuthClient();
  await expect(
    client.activate('a'.repeat(43), 'Synthetic-example-2026', 'en'),
  ).rejects.toMatchObject({ issue: 'invitation' });
  expect(client.getSnapshot().user).toBeNull();
});

it('automatically refreshes a visible session at the pre-expiry timer', async () => {
  vi.useFakeTimers();
  const s = setup(true);
  vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('visible');
  const client = new AuthClient();
  const stop = client.start();
  try {
    await client.restore();
    expect(s.fetcher.mock.calls.filter(([url]) => url.endsWith('/refresh'))).toHaveLength(1);
    await vi.advanceTimersByTimeAsync(870001);
    expect(s.fetcher.mock.calls.filter(([url]) => url.endsWith('/refresh'))).toHaveLength(2);
    expect(client.getSnapshot().status).toBe('authenticated');
  } finally {
    stop();
    vi.useRealTimers();
  }
});
