import { createContext, useContext } from 'react';
import type { ConversationClient } from './client';
export const ConversationContext = createContext<ConversationClient | null>(null);
export function useConversations() {
  const client = useContext(ConversationContext);
  if (!client) throw new Error('Conversation context unavailable.');
  return client;
}
