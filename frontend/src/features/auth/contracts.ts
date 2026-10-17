export interface User {
  id: string;
  email: string;
  role: 'citizen' | 'staff' | 'admin';
  preferred_language: 'en' | 'sw';
}
export interface Session {
  id: string;
  created_at: string;
  expires_at: string;
  last_used_at: string;
  is_current: boolean;
}
export interface SessionPage {
  items: Session[];
  next_cursor: string | null;
}
export type AuthIssue =
  | 'expired'
  | 'unavailable'
  | 'csrf'
  | 'rateLimited'
  | 'invalid'
  | 'invitation'
  | 'unsupported'
  | 'logoutFailed';
export class AuthError extends Error {
  constructor(public readonly issue: AuthIssue) {
    super('Authentication request could not complete.');
  }
}
export interface AuthState {
  status: 'loading' | 'guest' | 'authenticated' | 'unavailable';
  user: User | null;
  issue: AuthIssue | null;
}
export function safeReturn(value: unknown): string {
  // An exact allowlist avoids URL parsing, encoded separators and redirect chains.
  return value === '/' || value === '/account' ? value : '/account';
}
export function userContract(value: unknown): User {
  if (!value || typeof value !== 'object') throw new AuthError('unavailable');
  const u = value as Record<string, unknown>;
  if (
    typeof u.id !== 'string' ||
    !/^[a-f\d-]{36}$/i.test(u.id) ||
    typeof u.email !== 'string' ||
    u.email.length > 254 ||
    !['citizen', 'staff', 'admin'].includes(String(u.role)) ||
    !['en', 'sw'].includes(String(u.preferred_language))
  )
    throw new AuthError('unavailable');
  return {
    id: u.id,
    email: u.email,
    role: u.role as User['role'],
    preferred_language: u.preferred_language as User['preferred_language'],
  };
}

export function formText(data: FormData, key: string): string {
  const value = data.get(key);
  return typeof value === 'string' ? value : '';
}
