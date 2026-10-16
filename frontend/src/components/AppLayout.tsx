import { NavLink, Outlet } from 'react-router';
import { useLanguage } from '../i18n/language';
import { Text } from '../i18n/Text';
import { LanguageSelector } from './LanguageSelector';

export function AppLayout() {
  const { t } = useLanguage();
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        <Text message="skipLink" />
      </a>
      <div className="environment-banner">
        <div className="page-width">
          <span className="notice-dot" aria-hidden="true" />
          <Text message="environmentNotice" />
        </div>
      </div>
      <header className="site-header">
        <div className="page-width header-inner">
          <NavLink to="/" className="brand">
            <span className="brand-symbol" aria-hidden="true">
              C
            </span>
            <span>
              <Text message="appName" />
            </span>
          </NavLink>
          <LanguageSelector />
        </div>
        <nav className="page-width primary-nav" aria-label={t('primaryNav')}>
          <NavLink to="/" end>
            <Text message="navHome" />
          </NavLink>
          <NavLink to="/assistant">
            <Text message="navAssistant" />
          </NavLink>
        </nav>
      </header>
      <main id="main-content" className="page-width main-content" tabIndex={-1}>
        <Outlet />
      </main>
      <footer className="site-footer">
        <div className="page-width footer-inner">
          <p>
            <Text message="footerNotice" />
          </p>
          <p className="review-note">
            <Text message="translationReview" />
          </p>
        </div>
      </footer>
    </div>
  );
}
