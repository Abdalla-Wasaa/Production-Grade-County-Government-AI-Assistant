import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router';
import { useLanguage } from '../../i18n/language';
import { useAuth } from './context';
import { invitationDraft, clearInvitationDraft, captureInvitation } from './invitation';
import { AuthError, formText } from './contracts';
import type { AuthIssue } from './contracts';
import { AuthNotice } from './AuthNotice';
export function ActivationPage() {
  const { client } = useAuth();
  const { t, language } = useLanguage();
  const [token, setToken] = useState(invitationDraft);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [issue, setIssue] = useState<AuthIssue | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (done) heading.current?.focus();
  }, [done]);
  useEffect(() => {
    clearInvitationDraft();
    const changed = () => {
      captureInvitation();
      setToken(invitationDraft());
      clearInvitationDraft();
    };
    window.addEventListener('hashchange', changed);
    return () => window.removeEventListener('hashchange', changed);
  }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const password = formText(data, 'password');
    if (
      data.get('notice') !== 'on' ||
      password !== data.get('confirm') ||
      [...password].length < 12 ||
      [...password].length > 128 ||
      !/^[A-Za-z0-9_-]{43}$/.test(token)
    ) {
      setIssue('invalid');
      return;
    }
    setBusy(true);
    setIssue(null);
    try {
      await client.activate(token, password, language);
      setDone(true);
    } catch (error) {
      setIssue(error instanceof AuthError ? error.issue : 'unavailable');
    } finally {
      form.reset();
      setToken('');
      setBusy(false);
    }
  }
  if (done)
    return (
      <section className="auth-card">
        <h1 tabIndex={-1} ref={heading}>
          {t('activationDone')}
        </h1>
        <p role="status">{t('activationLogin')}</p>
        <Link to="/login" className="primary-button">
          {t('loginSubmit')}
        </Link>
      </section>
    );
  return (
    <section className="auth-card">
      <p className="eyebrow">{t('authSynthetic')}</p>
      <h1 tabIndex={-1}>{t('activationTitle')}</h1>
      <p className="intro">{t('activationIntro')}</p>
      <AuthNotice issue={issue} />
      <form
        onSubmit={(event) => {
          void submit(event);
        }}
        aria-busy={busy}
        aria-describedby="auth-feedback"
      >
        <label htmlFor="invitation">{t('invitationLabel')}</label>
        <input
          id="invitation"
          name="invitation"
          type="password"
          autoComplete="off"
          value={token}
          onChange={(event) => setToken(event.target.value)}
          minLength={43}
          maxLength={43}
          required
          spellCheck={false}
        />
        <label htmlFor="new-password">{t('passwordLabel')}</label>
        <input
          id="new-password"
          name="password"
          type="password"
          autoComplete="new-password"
          aria-describedby="password-help"
          required
        />
        <p id="password-help">{t('passwordHelp')}</p>
        <label htmlFor="confirm-password">{t('confirmPassword')}</label>
        <input
          id="confirm-password"
          name="confirm"
          type="password"
          autoComplete="new-password"
          required
        />
        <p id="privacy-notice">{t('syntheticNotice')}</p>
        <label className="checkbox-label">
          <input name="notice" type="checkbox" required />
          {t('noticeAccept')}
        </label>
        <button className="primary-button" disabled={busy}>
          {busy ? t('authWorking') : t('activateSubmit')}
        </button>
      </form>
      <Link to="/login" className="text-link">
        {t('loginSubmit')}
      </Link>
    </section>
  );
}
