import { AuthProvider } from '../features/auth/AuthProvider';
import { LoginPage } from '../features/auth/LoginPage';
import { ActivationPage } from '../features/auth/ActivationPage';
import { AccountPage } from '../features/auth/AccountPage';
import { ProtectedRoute } from '../features/auth/ProtectedRoute';
import { Route, Routes } from 'react-router';
import { AppLayout } from '../components/AppLayout';
import { HomePage } from '../features/home/HomePage';
import { AssistantPlaceholder } from '../features/assistant/AssistantPlaceholder';
import { NotFoundPage } from '../features/not-found/NotFoundPage';
import { useLanguage } from '../i18n/language';
import { readPublicConfig } from '../config';
import { AppErrorBoundary } from './AppErrorBoundary';
import { RouteFocus } from './RouteFocus';

function AppRoutes() {
  readPublicConfig(import.meta.env);
  return (
    <>
      <RouteFocus />
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<HomePage />} />
          <Route path="assistant" element={<AssistantPlaceholder />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="activate" element={<ActivationPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="account" element={<AccountPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </>
  );
}
export function App() {
  const { language } = useLanguage();
  return (
    <AppErrorBoundary language={language}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </AppErrorBoundary>
  );
}
