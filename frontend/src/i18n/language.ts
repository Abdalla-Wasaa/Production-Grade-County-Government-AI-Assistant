import { createContext, useContext } from 'react';
import type { Language, MessageKey } from './messages';

export interface LanguageState {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: MessageKey) => string;
}
export const LanguageContext = createContext<LanguageState | null>(null);
export function useLanguage(): LanguageState {
  const state = useContext(LanguageContext);
  if (!state) throw new Error('Language context unavailable.');
  return state;
}
