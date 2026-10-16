import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router';
import { App } from './app/App';
import { LanguageProvider } from './i18n/LanguageProvider';
import './styles.css';

const container = document.getElementById('root');
if (!container) throw new Error('Application container unavailable.');
// React's default caught-error reporting can include arbitrary exception content.
// The boundary supplies fixed messages; no browser telemetry is enabled here.
createRoot(container, {
  onCaughtError: () => {},
  onUncaughtError: () => {},
  onRecoverableError: () => {},
}).render(
  <StrictMode>
    <LanguageProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </LanguageProvider>
  </StrictMode>,
);
