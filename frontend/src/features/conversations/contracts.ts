export type Language = 'en' | 'sw';
export interface Conversation {
  id: string;
  title: string;
  language: Language;
  version: number;
  created_at: string;
  updated_at: string;
  expires_at: string;
}
export interface Message {
  id: string;
  conversation_id: string;
  sequence: number;
  role: 'user';
  content: string;
  language: Language;
  created_at: string;
}
export interface Page<T> {
  items: T[];
  next_cursor: string | null;
}
export interface Versioned<T> {
  value: T;
  etag: string;
}
export type HistoryIssue =
  'invalid' | 'missing' | 'conflict' | 'limited' | 'restricted' | 'unavailable';
export class HistoryError extends Error {
  constructor(readonly issue: HistoryIssue) {
    super('Conversation request could not be completed.');
  }
}
export function uuid(value: unknown): value is string {
  return typeof value === 'string' && /^[a-f\d]{8}-(?:[a-f\d]{4}-){3}[a-f\d]{12}$/i.test(value);
}
export function text(value: string, max: number): string {
  const clean = value.trim();
  if (
    !clean ||
    Array.from(clean).length > max ||
    clean.includes('\0') ||
    Array.from(clean).some((c) => c.length === 1 && /[\uD800-\uDFFF]/u.test(c))
  )
    throw new HistoryError('invalid');
  return clean;
}
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value))
    throw new HistoryError('unavailable');
  return value as Record<string, unknown>;
}
function date(value: unknown): value is string {
  return typeof value === 'string' && value.length <= 40 && Number.isFinite(Date.parse(value));
}
export function conversation(value: unknown): Conversation {
  const v = record(value);
  if (
    !uuid(v.id) ||
    typeof v.title !== 'string' ||
    !v.title.trim() ||
    Array.from(v.title).length > 120 ||
    !['en', 'sw'].includes(String(v.language)) ||
    !Number.isSafeInteger(v.version) ||
    Number(v.version) < 1 ||
    !date(v.created_at) ||
    !date(v.updated_at) ||
    !date(v.expires_at)
  )
    throw new HistoryError('unavailable');
  // Copy allowlisted fields; never retain unexpected ownership/internal fields.
  return {
    id: v.id,
    title: v.title,
    language: v.language as Language,
    version: Number(v.version),
    created_at: v.created_at,
    updated_at: v.updated_at,
    expires_at: v.expires_at,
  };
}
export function message(value: unknown, owner: string): Message {
  const v = record(value);
  if (
    !uuid(v.id) ||
    v.conversation_id !== owner ||
    v.role !== 'user' ||
    typeof v.content !== 'string' ||
    !v.content.trim() ||
    Array.from(v.content).length > 4000 ||
    !Number.isSafeInteger(v.sequence) ||
    Number(v.sequence) < 1 ||
    !['en', 'sw'].includes(String(v.language)) ||
    !date(v.created_at)
  )
    throw new HistoryError('unavailable');
  return {
    id: v.id,
    conversation_id: owner,
    sequence: Number(v.sequence),
    role: 'user',
    content: v.content,
    language: v.language as Language,
    created_at: v.created_at,
  };
}
export function page<T>(value: unknown, parse: (value: unknown) => T): Page<T> {
  const v = record(value);
  if (
    !Array.isArray(v.items) ||
    v.items.length > 20 ||
    !(v.next_cursor === null || (typeof v.next_cursor === 'string' && v.next_cursor.length <= 2048))
  )
    throw new HistoryError('unavailable');
  return { items: v.items.map(parse), next_cursor: v.next_cursor };
}
export function issue(error: unknown): HistoryIssue {
  return error instanceof HistoryError ? error.issue : 'unavailable';
}
