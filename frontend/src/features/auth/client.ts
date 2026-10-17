import { readPublicConfig } from '../../config';
import { AuthError, userContract } from './contracts';
import type { AuthIssue, AuthState, SessionPage } from './contracts';

const LOCK = 'county.auth.cookies.v1';
const CHANNEL = 'county.auth.invalidate.v1';
const TIMEOUT = 12000;

// All credentials are private object fields. No storage, URL or telemetry adapter.
export class AuthClient {
  private access: string | null = null;
  private expires = 0;
  private generation = 0;
  private state: AuthState = { status: 'loading', user: null, issue: null };
  private listeners = new Set<() => void>();
  private channel: BroadcastChannel | null = null;
  private timer: ReturnType<typeof setTimeout> | undefined;
  private running = false;
  private refreshUncertain = false;
  private signOutUnconfirmed = false;
  private restoration: Promise<void> | null = null;
  private readonly base = readPublicConfig(import.meta.env).apiBaseUrl + '/auth';

  getSnapshot = (): AuthState => this.state;
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  private publish(state: AuthState) {
    this.state = state;
    this.listeners.forEach((notify) => notify());
  }
  private clear(issue: AuthIssue | null, broadcast = false) {
    this.generation++;
    this.access = null;
    this.expires = 0;
    clearTimeout(this.timer);
    this.publish({ status: issue === 'unavailable' ? 'unavailable' : 'guest', user: null, issue });
    if (broadcast) this.channel?.postMessage('invalidate');
  }
  start = () => {
    this.running = true;
    if (typeof BroadcastChannel !== 'undefined') {
      this.channel = new BroadcastChannel(CHANNEL);
      this.channel.onmessage = (event: MessageEvent<unknown>) => {
        if (event.data === 'invalidate') this.clear('expired');
        if (event.data === 'logout-unconfirmed') {
          this.signOutUnconfirmed = true;
          this.clear('logoutFailed');
        }
      };
    }
    const visible = () => {
      if (document.visibilityState === 'visible' && this.access) {
        void this.currentUser().catch(() => {});
      }
    };
    document.addEventListener('visibilitychange', visible);
    return () => {
      document.removeEventListener('visibilitychange', visible);
      this.channel?.close();
      this.channel = null;
      clearTimeout(this.timer);
      this.running = false;
      queueMicrotask(() => {
        if (!this.running) {
          this.access = null;
          this.expires = 0;
          this.generation++;
        }
      });
    };
  };
  private async serialized<T>(work: () => Promise<T>): Promise<T> {
    // No tab-local fallback: it would race a shared rotating refresh cookie.
    if (!navigator.locks || typeof BroadcastChannel === 'undefined') {
      throw new AuthError('unsupported');
    }
    try {
      return await navigator.locks.request(LOCK, { signal: AbortSignal.timeout(TIMEOUT) }, work);
    } catch (error) {
      if (error instanceof AuthError) throw error;
      throw new AuthError('unavailable');
    }
  }
  private async request(
    path: string,
    method = 'GET',
    body?: unknown,
    csrf?: string,
    bearer = false,
  ): Promise<unknown> {
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (csrf) headers['X-CSRF-Token'] = csrf;
    if (bearer && this.access) headers.Authorization = `Bearer ${this.access}`;
    let response: Response;
    try {
      response = await fetch(this.base + path, {
        method,
        headers,
        credentials: 'same-origin',
        cache: 'no-store',
        redirect: 'error',
        referrerPolicy: 'same-origin',
        signal: AbortSignal.timeout(TIMEOUT),
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch {
      throw new AuthError('unavailable');
    }
    if (!response.ok) {
      // Never render/log arbitrary backend response text or reflected input.
      const issue: AuthIssue =
        response.status === 401
          ? 'expired'
          : response.status === 403
            ? 'csrf'
            : response.status === 429
              ? 'rateLimited'
              : response.status === 400 && path === '/activate'
                ? 'invitation'
                : response.status === 422
                  ? 'invalid'
                  : 'unavailable';
      throw new AuthError(issue);
    }
    if (response.status === 204) return null;
    try {
      return (await response.json()) as unknown;
    } catch {
      throw new AuthError('unavailable');
    }
  }
  private async mutation(path: string, body: unknown = {}, bearer = false, method = 'POST') {
    // Called only under the cross-tab lock. Each mutation obtains a fresh CSRF
    // cookie/header pair, including after login/refresh changes family binding.
    const data = await this.request('/csrf');
    if (
      !data ||
      typeof data !== 'object' ||
      !('csrf_token' in data) ||
      typeof data.csrf_token !== 'string'
    )
      throw new AuthError('unavailable');
    try {
      return await this.request(path, method, body, data.csrf_token, bearer);
    } catch (error) {
      if (path === '/refresh' && error instanceof AuthError && error.issue === 'unavailable')
        this.refreshUncertain = true;
      throw error;
    }
  }
  private accept(value: unknown) {
    if (!value || typeof value !== 'object') throw new AuthError('unavailable');
    const v = value as Record<string, unknown>;
    if (
      typeof v.access_token !== 'string' ||
      v.access_token.length > 8192 ||
      v.token_type !== 'bearer' ||
      v.expires_in !== 900
    )
      throw new AuthError('unavailable');
    const user = userContract(v.user);
    this.access = v.access_token;
    this.expires = Date.now() + 870000; // refresh 30 seconds before server TTL.
    this.publish({ status: 'authenticated', user, issue: null });
    this.schedule();
  }
  private schedule() {
    clearTimeout(this.timer);
    if (!this.running) return;
    this.timer = setTimeout(
      () => {
        if (document.visibilityState === 'visible') void this.currentUser().catch(() => {});
      },
      Math.max(1000, this.expires - Date.now()),
    );
  }
  private async ensureAccess() {
    if (this.signOutUnconfirmed) throw new AuthError('logoutFailed');
    if (!this.access || Date.now() >= this.expires) {
      // Exactly one attempt. A lost/ambiguous response is never replayed.
      if (this.refreshUncertain) throw new AuthError('expired');
      const generation = this.generation;
      const value = await this.mutation('/refresh');
      if (generation !== this.generation) throw new AuthError('expired');
      this.accept(value);
    }
  }
  private failed(error: unknown, broadcast = false): never {
    const issue = error instanceof AuthError ? error.issue : 'unavailable';
    this.clear(issue, broadcast);
    throw new AuthError(issue);
  }
  restore = (): Promise<void> => {
    if (this.restoration) return this.restoration;
    this.restoration = this.serialized(async () => {
      await this.ensureAccess();
      const generation = this.generation;
      const user = userContract(await this.request('/me', 'GET', undefined, undefined, true));
      if (generation !== this.generation) throw new AuthError('expired');
      this.publish({ status: 'authenticated', user, issue: null });
    })
      .catch((error: unknown) => {
        this.failed(error);
      })
      .finally(() => {
        this.restoration = null;
      });
    return this.restoration;
  };
  login = async (email: string, password: string) => {
    try {
      await this.serialized(async () => {
        const value = await this.mutation('/login', { email, password });
        this.generation++;
        this.refreshUncertain = false;
        this.signOutUnconfirmed = false;
        this.accept(value);
        this.channel?.postMessage('invalidate');
      });
    } catch (error) {
      if (error instanceof AuthError && error.issue === 'expired')
        this.failed(new AuthError('invalid'));
      this.failed(error);
    }
  };
  activate = async (token: string, password: string, language: 'en' | 'sw') => {
    try {
      await this.serialized(async () => {
        await this.mutation('/activate', {
          token,
          password,
          preferred_language: language,
          privacy_notice_version: 'synthetic-v1',
          privacy_notice_acknowledged: true,
        });
        this.clear(null, true);
      });
    } catch (error) {
      this.failed(error);
    }
  };
  currentUser = async () => {
    try {
      await this.serialized(async () => {
        await this.ensureAccess();
        const generation = this.generation;
        const user = userContract(await this.request('/me', 'GET', undefined, undefined, true));
        if (generation !== this.generation) throw new AuthError('expired');
        this.publish({ status: 'authenticated', user, issue: null });
      });
    } catch (error) {
      this.failed(error, error instanceof AuthError && error.issue === 'expired');
    }
  };
  sessions = async (cursor?: string): Promise<SessionPage> => {
    try {
      return await this.serialized(async () => {
        await this.ensureAccess();
        const generation = this.generation;
        const data = await this.request(
          '/sessions' + (cursor ? '?cursor=' + encodeURIComponent(cursor) : ''),
          'GET',
          undefined,
          undefined,
          true,
        );
        if (generation !== this.generation) throw new AuthError('expired');
        if (!data || typeof data !== 'object') throw new AuthError('unavailable');
        const v = data as SessionPage;
        if (
          !Array.isArray(v.items) ||
          v.items.length > 100 ||
          !(v.next_cursor === null || typeof v.next_cursor === 'string') ||
          v.items.some(
            (s) =>
              !s ||
              !/^[a-f\d-]{36}$/i.test(s.id) ||
              typeof s.is_current !== 'boolean' ||
              [s.created_at, s.expires_at, s.last_used_at].some(
                (t) => typeof t !== 'string' || !Number.isFinite(Date.parse(t)),
              ),
          )
        )
          throw new AuthError('unavailable');
        return v;
      });
    } catch (error) {
      return this.failed(error);
    }
  };
  revoke = async (id: string, current: boolean) => {
    if (!/^[a-f\d-]{36}$/i.test(id)) throw new AuthError('invalid');
    try {
      await this.serialized(async () => {
        await this.ensureAccess();
        await this.mutation('/sessions/' + id, {}, true, 'DELETE');
        if (current) this.clear('expired', true);
      });
    } catch (error) {
      this.failed(error);
    }
  };
  logout = async (all = false) => {
    try {
      await this.serialized(async () => {
        if (all) await this.ensureAccess();
        await this.mutation(all ? '/logout-all' : '/logout', {}, all);
      });
      this.signOutUnconfirmed = false;
      this.refreshUncertain = false;
      this.clear(null, true);
    } catch {
      this.signOutUnconfirmed = true;
      this.clear('logoutFailed');
      this.channel?.postMessage('logout-unconfirmed');
      throw new AuthError('logoutFailed');
    }
  };
}
