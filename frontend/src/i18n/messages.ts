import { en } from './en';
import { sw } from './sw';

export type Language = 'en' | 'sw';
export type MessageKey = keyof typeof en;
export type Messages = Record<MessageKey, string>;
export const dictionaries: Record<Language, Messages> = { en, sw };
export const LANGUAGE_STORAGE_KEY = 'county.ui.language.v1';

export function resolveMessage(
  language: Language,
  key: MessageKey,
  source: Record<Language, Partial<Messages>> = dictionaries,
): { text: string; language: Language } {
  const translated = source[language][key];
  if (translated?.trim()) return { text: translated, language };
  return { text: source.en[key]?.trim() || en.errorTitle, language: 'en' };
}

export function readLanguage(): Language {
  try {
    return localStorage.getItem(LANGUAGE_STORAGE_KEY) === 'sw' ? 'sw' : 'en';
  } catch {
    return 'en';
  }
}

export function saveLanguage(language: Language): void {
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch {
    /* Storage denial must not prevent in-memory language selection. */
  }
}
