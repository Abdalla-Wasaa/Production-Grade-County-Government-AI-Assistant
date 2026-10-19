import type { AuthClient } from '../auth/client';
import { HistoryError, conversation, message, page, text, uuid } from './contracts';
import type { Conversation, Language, Message, Page, Versioned } from './contracts';

type Ticket = {
  readonly content: string;
  readonly key: string;
  readonly status: 'saving' | 'uncertain';
};
// Only uncertain submissions survive route changes, in memory within one auth scope.
// There is no history cache, browser storage, token accessor or telemetry adapter.
export class ConversationClient {
  private lifecycle = 0;
  private controllers = new Set<AbortController>();
  private tickets = new Map<string, Ticket>();
  private flights = new Map<string, Promise<Versioned<Message>>>();
  private listeners = new Set<() => void>();
  private revision = 0;
  private unsubscribe = () => {};
  constructor(
    private auth: AuthClient,
    readonly scope: string,
  ) {
    // Construction is pure: StrictMode may discard memoized instances.
  }
  start = () => {
    this.unsubscribe = this.auth.subscribe(() => {
      if (!this.auth.isSessionScope(this.scope)) this.close();
    });
    return this.close;
  };
  private check(lifecycle = this.lifecycle) {
    if (lifecycle !== this.lifecycle || !this.auth.isSessionScope(this.scope))
      throw new HistoryError('unavailable');
  }
  close = () => {
    this.lifecycle++;
    this.controllers.forEach((c) => c.abort());
    this.controllers.clear();
    this.tickets.clear();
    this.flights.clear();
    this.unsubscribe();
    this.notify();
    this.listeners.clear();
  };
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  getRevision = () => this.revision;
  hasPending = () => this.tickets.size > 0;
  pending(id: string): Pick<Ticket, 'content' | 'status'> | undefined {
    return this.tickets.get(id);
  }
  private notify() {
    this.revision++;
    this.listeners.forEach((f) => f());
  }
  private path(id: string) {
    if (!uuid(id)) throw new HistoryError('invalid');
    return '/conversations/' + id;
  }
  private async request<T>(
    path: string,
    parse: (value: unknown) => T,
    options: {
      method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
      body?: unknown;
      headers?: { 'Idempotency-Key'?: string; 'If-Match'?: string };
      signal?: AbortSignal | undefined;
    } = {},
  ): Promise<{ value: T; etag: string | null }> {
    this.check();
    const lifecycle = this.lifecycle;
    const controller = new AbortController();
    this.controllers.add(controller);
    try {
      const response = await this.auth.conversationRequest(this.scope, path, {
        ...options,
        signal: AbortSignal.any([controller.signal, ...(options.signal ? [options.signal] : [])]),
      });
      this.check(lifecycle);
      if (response.status === 409 && options.method === 'DELETE') {
        // A hold is a deletion restriction, not a stale metadata version. Never
        // expose its reason or echo an untrusted server message.
        throw new HistoryError('restricted');
      }
      if (!response.ok)
        throw new HistoryError(
          response.status === 404
            ? 'missing'
            : response.status === 409 || response.status === 412 || response.status === 428
              ? 'conflict'
              : response.status === 429
                ? 'limited'
                : response.status === 422
                  ? 'invalid'
                  : 'unavailable',
        );
      let raw: unknown = null;
      if (response.status !== 204) {
        try {
          const body = await response.text();
          if (body.length > 2000000) throw new Error();
          raw = JSON.parse(body) as unknown;
        } catch {
          throw new HistoryError('unavailable');
        }
      }
      this.check(lifecycle);
      return { value: parse(raw), etag: response.headers.get('ETag') };
    } finally {
      this.controllers.delete(controller);
    }
  }
  private versioned<T extends { version: number }>(result: {
    value: T;
    etag: string | null;
  }): Versioned<T> {
    if (result.etag !== `"${result.value.version}"`) throw new HistoryError('unavailable');
    return { value: result.value, etag: result.etag };
  }
  async list(cursor?: string, signal?: AbortSignal): Promise<Page<Conversation>> {
    return (
      await this.request(
        '/conversations?limit=20' + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
        (v) => page(v, conversation),
        { signal },
      )
    ).value;
  }
  async get(id: string, signal?: AbortSignal): Promise<Versioned<Conversation>> {
    const result = this.versioned(await this.request(this.path(id), conversation, { signal }));
    if (result.value.id !== id) throw new HistoryError('unavailable');
    return result;
  }
  async create(title: string, language: Language): Promise<Versioned<Conversation>> {
    return this.versioned(
      await this.request('/conversations', conversation, {
        method: 'POST',
        body: { ...(title.trim() ? { title: text(title, 120) } : {}), language },
      }),
    );
  }
  async rename(id: string, title: string, etag: string): Promise<Versioned<Conversation>> {
    const result = this.versioned(
      await this.request(this.path(id), conversation, {
        method: 'PATCH',
        body: { title: text(title, 120) },
        headers: { 'If-Match': etag },
      }),
    );
    if (result.value.id !== id) throw new HistoryError('unavailable');
    return result;
  }
  async remove(id: string) {
    await this.request(this.path(id), () => null, { method: 'DELETE' });
    this.tickets.delete(id);
    this.notify();
  }
  async history(id: string, cursor?: string, signal?: AbortSignal): Promise<Page<Message>> {
    const result = (
      await this.request(
        this.path(id) +
          '/messages?limit=20' +
          (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''),
        (v) => page(v, (item) => message(item, id)),
        { signal },
      )
    ).value;
    if (result.items.some((m, i) => i > 0 && m.sequence <= result.items[i - 1]!.sequence))
      throw new HistoryError('unavailable');
    return result;
  }
  send(id: string, content: string): Promise<Versioned<Message>> {
    this.check();
    this.path(id);
    if (this.flights.has(id)) return this.flights.get(id)!;
    const lifecycle = this.lifecycle;
    const previous = this.tickets.get(id);
    const normalized = text(content, 4000);
    if (previous && previous.content !== normalized) throw new HistoryError('conflict');
    const ticket: Ticket = {
      key: previous?.key ?? crypto.randomUUID(),
      content: normalized,
      status: 'saving',
    };
    this.tickets.set(id, ticket);
    this.notify();
    const flight = this.request(this.path(id) + '/messages', (v) => message(v, id), {
      method: 'POST',
      body: { content: ticket.content },
      headers: { 'Idempotency-Key': ticket.key },
    })
      .then((result) => {
        this.check(lifecycle);
        if (!result.etag || !/^"[1-9]\d*"$/.test(result.etag))
          throw new HistoryError('unavailable');
        this.tickets.delete(id);
        this.notify();
        return { value: result.value, etag: result.etag };
      })
      .catch((error: unknown) => {
        if (lifecycle === this.lifecycle && this.auth.isSessionScope(this.scope)) {
          if (
            error instanceof HistoryError &&
            ['invalid', 'missing', 'limited'].includes(error.issue)
          )
            this.tickets.delete(id);
          else this.tickets.set(id, { ...ticket, status: 'uncertain' });
          this.notify();
        }
        throw error;
      })
      .finally(() => {
        if (this.flights.get(id) === flight) this.flights.delete(id);
      });
    this.flights.set(id, flight);
    return flight;
  }
}
