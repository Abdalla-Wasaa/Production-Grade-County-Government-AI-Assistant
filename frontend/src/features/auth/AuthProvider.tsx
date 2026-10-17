import { useEffect, useState, useSyncExternalStore } from 'react';
import type { ReactNode } from 'react';
import { AuthClient } from './client';
import { AuthContext } from './context';
export function AuthProvider({ children }: { children: ReactNode }) {
  const [client] = useState(() => new AuthClient());
  const state = useSyncExternalStore(client.subscribe, client.getSnapshot);
  useEffect(() => client.start(), [client]);
  // Public preview routes do not initiate auth requests against a health-only API.
  return <AuthContext value={{ client, state }}>{children}</AuthContext>;
}
