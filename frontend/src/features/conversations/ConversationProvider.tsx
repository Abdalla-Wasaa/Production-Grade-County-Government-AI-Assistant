import { useEffect, useMemo } from 'react';
import type { ReactNode } from 'react';
import { useAuth } from '../auth/context';
import { ConversationClient } from './client';
import { ConversationContext } from './context';
export function ConversationProvider({ children }: { children: ReactNode }) {
  const { client: auth, state } = useAuth();
  const scope = auth.getSessionScope();
  const authenticated = state.status === 'authenticated';
  const client = useMemo(
    () => (authenticated ? new ConversationClient(auth, scope) : null),
    [auth, scope, authenticated],
  );
  useEffect(() => {
    if (!client) return;
    const stop = client.start();
    const leaving = (event: BeforeUnloadEvent) => {
      if (client.hasPending()) event.preventDefault();
    };
    window.addEventListener('beforeunload', leaving);
    return () => {
      window.removeEventListener('beforeunload', leaving);
      stop();
    };
  }, [client]);
  return <ConversationContext value={client}>{children}</ConversationContext>;
}
