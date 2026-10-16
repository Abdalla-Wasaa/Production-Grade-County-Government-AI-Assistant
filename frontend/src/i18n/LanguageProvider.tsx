import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { LanguageContext } from './language';
import { readLanguage, resolveMessage, saveLanguage } from './messages';
import type { Language } from './messages';

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(readLanguage);
  useEffect(() => {
    document.documentElement.lang = language;
    saveLanguage(language);
  }, [language]);
  return (
    <LanguageContext
      value={{ language, setLanguage, t: (key) => resolveMessage(language, key).text }}
    >
      {children}
    </LanguageContext>
  );
}
