import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { describe, expect, it } from 'vitest';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { App } from './App';

function renderApp(path = '/') {
  return render(
    <LanguageProvider>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </LanguageProvider>,
  );
}
describe('application shell', () => {
  it('renders landmarks, real limitations and the English default', () => {
    renderApp();
    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Primary navigation' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'A clearer path to county information.',
    );
    expect(
      screen.getByText('Fictional development environment. No government endorsement.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('contentinfo')).toHaveTextContent('pending human review');
    expect(document.documentElement.lang).toBe('en');
    expect(document.title).toBe('Home · County Government AI Assistant');
  });
  it('navigates to the honest placeholder and moves focus', async () => {
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole('link', { name: 'View assistant preview' }));
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'The assistant is taking shape.',
    );
    expect(screen.getByRole('heading', { level: 1 })).toHaveFocus();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /send/i })).not.toBeInTheDocument();
    expect(screen.getByText('Chat is not available')).toBeInTheDocument();
    expect(document.title).toContain('Assistant preview');
  });
  it('localizes an unmatched route without reflecting path input', async () => {
    const user = userEvent.setup();
    renderApp('/private-hostname?secret=do-not-reflect');
    await user.selectOptions(screen.getByRole('combobox'), 'sw');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Hatukuweza kupata ukurasa huo.',
    );
    expect(screen.getByRole('link', { name: 'Rudi mwanzo' })).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('do-not-reflect');
  });
  it('supports keyboard language selection without stealing focus or resetting the page', async () => {
    const user = userEvent.setup();
    renderApp('/assistant');
    const selector = screen.getByRole('combobox', { name: 'Interface language' });
    selector.focus();
    await user.keyboard('s');
    await user.selectOptions(selector, 'sw');
    expect(selector).toHaveFocus();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Msaidizi anaendelea kuandaliwa.',
    );
    expect(document.documentElement.lang).toBe('sw');
  });
});
