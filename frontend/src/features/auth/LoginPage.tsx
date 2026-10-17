import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router';
import { useLanguage } from '../../i18n/language';
import { useAuth } from './context';
import { AuthNotice } from './AuthNotice';
import { AuthError, safeReturn, formText } from './contracts';
import type { AuthIssue } from './contracts';
export function LoginPage() {
  const { client, state } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<AuthIssue | null>(null);
  useEffect(() => {
    void client.restore().catch(() => {});
  }, [client]);
  useEffect(() => {
    if (state.status === 'authenticated') void navigate(safeReturn('/account'), { replace: true });
  }, [state.status, navigate]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const password = formText(data, 'password');
    if ([...password].length < 1 || [...password].length > 128) {
      form.reset();
      setIssue('invalid');
      return;
    }
    setBusy(true);
    setIssue(null);
    try {
      await client.login(formText(data, 'email'), formText(data, 'password'));
    } catch (error) {
      setIssue(error instanceof AuthError ? error.issue : 'unavailable');
    } finally {
      form.reset();
      setBusy(false);
    }
  }
  return (
    <section className="auth-card">
      <p className="eyebrow">{t('authSynthetic')}</p>
      <h1 tabIndex={-1}>{t('loginTitle')}</h1>
      <p className="intro">{t('loginIntro')}</p>
      <AuthNotice issue={busy ? null : (issue ?? state.issue)} />
      {state.status === 'loading' && <p role="status">{t('authLoading')}</p>}
      <form
        onSubmit={(event) => {
          void submit(event);
        }}
        aria-busy={busy}
        aria-describedby="auth-feedback"
      >
        <label htmlFor="email">{t('emailLabel')}</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          maxLength={254}
          required
        />
        <label htmlFor="password">{t('passwordLabel')}</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
        <button className="primary-button" disabled={busy || state.status === 'loading'}>
          {busy ? t('authWorking') : t('loginSubmit')}
        </button>
      </form>
      <p>{t('recoveryHelp')}</p>
      <Link className="text-link" to="/activate">
        {t('activateLink')}
      </Link>
      {state.issue === 'logoutFailed' && (
        <button
          type="button"
          className="text-link"
          onClick={() => {
            void client.logout().catch(() => {});
          }}
        >
          {t('logoutRetry')}
        </button>
      )}
    </section>
  );
}
