import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { afterEach, describe, expect, it } from 'vitest';
import { App } from '../../app/App';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { installServer } from './testServer';
let restore = () => {};
afterEach(() => {
  restore();
});
function mount(path: string, session = false) {
  const server = installServer(session);
  restore = server.restore;
  render(
    <LanguageProvider>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </LanguageProvider>,
  );
  return server;
}
describe('bilingual account pages', () => {
  it('guards account content until restored, supports login and logout', async () => {
    mount('/account');
    const user = userEvent.setup();
    await screen.findByRole('heading', { name: 'Sign in' });
    expect(screen.queryByText('sample@example.invalid')).not.toBeInTheDocument();
    await user.type(screen.getByLabelText('Email address'), 'sample@example.invalid');
    await user.type(screen.getByLabelText('Password', { exact: true }), 'Synthetic-example-2026');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));
    await screen.findByText('sample@example.invalid');
    await user.click(screen.getByRole('button', { name: 'Sign out this session' }));
    await screen.findByRole('heading', { name: 'Sign in' });
    expect(screen.queryByText('sample@example.invalid')).not.toBeInTheDocument();
  });
  it('renders account sessions in Kiswahili and revokes its own session', async () => {
    mount('/account', true);
    const user = userEvent.setup();
    await screen.findByText('sample@example.invalid');
    await user.selectOptions(screen.getByRole('combobox'), 'sw');
    await screen.findByText('Kikao cha kivinjari hiki');
    await user.click(screen.getByRole('button', { name: 'Futa kikao hiki' }));
    await screen.findByRole('heading', { name: 'Ingia' });
  });
  it('requires acknowledgement, activates and requests a separate login', async () => {
    mount('/activate');
    const user = userEvent.setup();
    await user.type(screen.getByLabelText('Invitation or recovery token'), 'a'.repeat(43));
    await user.type(screen.getByLabelText('Password', { exact: true }), 'Synthetic-example-2026');
    await user.type(screen.getByLabelText('Confirm password'), 'Synthetic-example-2026');
    await user.click(screen.getByRole('button', { name: 'Set password and activate' }));
    expect(screen.queryByText('Password saved')).not.toBeInTheDocument();
    await user.click(screen.getByRole('checkbox'));
    await user.click(screen.getByRole('button', { name: 'Set password and activate' }));
    await screen.findByRole('heading', { name: 'Password saved' });
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/login');
  });
  it('clears password inputs and focuses safe errors after login denial', async () => {
    const s = mount('/login');
    await waitFor(() => expect(screen.getByRole('button', { name: 'Sign in' })).toBeEnabled());
    const original = s.fetcher.getMockImplementation();
    s.fetcher.mockImplementation((url, init) =>
      url.endsWith('/login') ? Promise.resolve(s.response(401)) : original!(url, init),
    );
    const user = userEvent.setup();
    await user.type(screen.getByLabelText('Email address'), 'sample@example.invalid');
    await user.type(screen.getByLabelText('Password', { exact: true }), 'not-a-real-password');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveFocus());
    expect(screen.getByLabelText('Password', { exact: true })).toHaveValue('');
  });
});

it('preserves a valid supplementary-Unicode password without HTML truncation', async () => {
  const s = mount('/login');
  await waitFor(() => expect(screen.getByRole('button', { name: 'Sign in' })).toBeEnabled());
  const password = '🔐'.repeat(80);
  fireEvent.change(screen.getByLabelText('Email address'), {
    target: { value: 'sample@example.invalid' },
  });
  fireEvent.change(screen.getByLabelText('Password', { exact: true }), {
    target: { value: password },
  });
  await userEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  await screen.findByText('sample@example.invalid');
  const call = s.fetcher.mock.calls.find(([url]) => url.endsWith('/login'))!;
  expect((JSON.parse(call[1]!.body as string) as { password: string }).password).toBe(password);
});
