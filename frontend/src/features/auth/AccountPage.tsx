import { useEffect, useRef, useState } from 'react';
import { useAuth } from './context';
import { useLanguage } from '../../i18n/language';
import { AuthError } from './contracts';
import type { AuthIssue, SessionPage } from './contracts';
import { AuthNotice } from './AuthNotice';
export function AccountPage() {
  const { client, state } = useAuth();
  const { t, language } = useLanguage();
  const [page, setPage] = useState<SessionPage | null>(null);
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<AuthIssue | null>(null);
  const reload = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    let active = true;
    void client
      .sessions()
      .then((value) => {
        if (active) setPage(value);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [client]);
  async function action(work: () => Promise<void>, refresh = true) {
    if (busy) return;
    setBusy(true);
    setIssue(null);
    try {
      await work();
      if (refresh) setPage(await client.sessions());
      reload.current?.focus();
    } catch (error) {
      setIssue(error instanceof AuthError ? error.issue : 'unavailable');
    } finally {
      setBusy(false);
    }
  }
  const date = (value: string) =>
    new Intl.DateTimeFormat(language === 'sw' ? 'sw-KE' : 'en-KE', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value));
  return (
    <section className="account-page">
      <h1 tabIndex={-1}>{t('accountTitle')}</h1>
      <p className="intro">{t('accountIntro')}</p>
      <AuthNotice issue={issue} />
      <dl className="identity-summary">
        <dt>{t('emailLabel')}</dt>
        <dd>{state.user?.email}</dd>
        <dt>{t('roleLabel')}</dt>
        <dd>{state.user ? t(`role_${state.user.role}`) : ''}</dd>
      </dl>
      <div className="auth-actions">
        <button
          className="primary-button"
          disabled={busy}
          onClick={() => {
            void client.logout().catch(() => {});
          }}
        >
          {t('logout')}
        </button>
        <button
          className="secondary-button"
          disabled={busy}
          onClick={() => {
            void client.logout(true).catch(() => {});
          }}
        >
          {t('logoutAll')}
        </button>
      </div>
      <h2>{t('sessionsTitle')}</h2>
      <p>{t('sessionsHelp')}</p>
      <button
        ref={reload}
        className="secondary-button"
        disabled={busy}
        onClick={() => {
          void action(async () => {});
        }}
      >
        {t('sessionsReload')}
      </button>
      <div aria-live="polite" aria-busy={busy}>
        {!page ? (
          <p role="status">{t('authLoading')}</p>
        ) : page.items.length === 0 ? (
          <p>{t('sessionsEmpty')}</p>
        ) : (
          <ul className="session-list">
            {page.items.map((session) => (
              <li key={session.id}>
                <h3>{session.is_current ? t('sessionCurrent') : t('sessionOther')}</h3>
                <p>
                  {t('sessionCreated')}:{' '}
                  <time dateTime={session.created_at}>{date(session.created_at)}</time>
                </p>
                <p>
                  {t('sessionUsed')}:{' '}
                  <time dateTime={session.last_used_at}>{date(session.last_used_at)}</time>
                </p>
                <p>
                  {t('sessionExpires')}:{' '}
                  <time dateTime={session.expires_at}>{date(session.expires_at)}</time>
                </p>
                <button
                  className="secondary-button"
                  disabled={busy}
                  onClick={() => {
                    void action(() => client.revoke(session.id, session.is_current));
                  }}
                >
                  {session.is_current ? t('revokeCurrent') : t('revokeOther')}
                </button>
              </li>
            ))}
          </ul>
        )}
        {page?.next_cursor && (
          <button
            className="secondary-button"
            disabled={busy}
            onClick={() => {
              const cursor = page.next_cursor;
              if (cursor)
                void action(async () => {
                  setPage(await client.sessions(cursor));
                }, false);
            }}
          >
            {t('sessionsNext')}
          </button>
        )}
      </div>
    </section>
  );
}
