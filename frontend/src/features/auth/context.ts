import { createContext, useContext } from 'react';
import type { AuthClient } from './client';
import type { AuthState } from './contracts';
export const AuthContext = createContext<{ client: AuthClient; state: AuthState } | null>(null);
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('Authentication context unavailable.');
  return value;
}
