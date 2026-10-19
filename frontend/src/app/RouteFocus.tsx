import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router';
import { useLanguage } from '../i18n/language';

export function RouteFocus() {
  const { pathname } = useLocation();
  const { t } = useLanguage();
  const previousPath = useRef<string | null>(null);
  useEffect(() => {
    const title =
      pathname === '/'
        ? 'homePageTitle'
        : pathname === '/assistant'
          ? 'assistantPageTitle'
          : pathname === '/login'
            ? 'loginTitle'
            : pathname === '/activate'
              ? 'activationTitle'
              : pathname === '/conversations' || pathname.startsWith('/conversations/')
                ? 'historyTitle'
                : pathname === '/account'
                  ? 'accountTitle'
                  : 'notFoundPageTitle';
    document.title = `${t(title)} · ${t('appName')}`;
    // A language change updates titles without taking focus from its selector.
    if (previousPath.current !== pathname) {
      if (previousPath.current !== null) {
        document.querySelector<HTMLElement>('#main-content h1')?.focus();
      }
      previousPath.current = pathname;
    }
  }, [pathname, t]);
  return null;
}
