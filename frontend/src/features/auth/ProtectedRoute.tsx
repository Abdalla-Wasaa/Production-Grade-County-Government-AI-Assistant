import { useEffect } from 'react';
import { Navigate, Outlet } from 'react-router';
import { useAuth } from './context';
import { useLanguage } from '../../i18n/language';
import { AuthNotice } from './AuthNotice';
export function ProtectedRoute() {
  const { client, state } = useAuth();
  const { t } = useLanguage();
  useEffect(() => {
    void client.restore().catch(() => {});
  }, [client]);
  if (state.status === 'loading') return <p role="status">{t('authLoading')}</p>;
  if (state.status === 'unavailable')
    return (
      <section>
        <h1 tabIndex={-1}>{t('accountTitle')}</h1>
        <AuthNotice issue={state.issue} />
        <button
          className="primary-button"
          onClick={() => {
            void client.restore().catch(() => {});
          }}
        >
          {t('authRetry')}
        </button>
      </section>
    );
  if (state.status !== 'authenticated') return <Navigate to="/login" replace />;
  return <Outlet />;
}
