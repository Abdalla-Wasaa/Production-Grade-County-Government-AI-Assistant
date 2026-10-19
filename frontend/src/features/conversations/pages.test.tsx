import { StrictMode } from 'react';
import { act, render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../../app/App';
import { LanguageProvider } from '../../i18n/LanguageProvider';
import { firstId, secondId, installHistoryServer } from './testServer';
let restore = () => {};
const dialogMethods = {
  showModal: Object.getOwnPropertyDescriptor(HTMLDialogElement.prototype, 'showModal'),
  close: Object.getOwnPropertyDescriptor(HTMLDialogElement.prototype, 'close'),
};
beforeEach(() => {
  // jsdom has the element but not the native modal methods. Browser tests retain
  // the real dialog implementation and verify focus/inert behavior separately.
  Object.defineProperty(HTMLDialogElement.prototype, 'showModal', {
    configurable: true,
    writable: true,
    value: function (this: HTMLDialogElement) {
      this.open = true;
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, 'close', {
    configurable: true,
    writable: true,
    value: function (this: HTMLDialogElement) {
      this.open = false;
    },
  });
});
afterEach(() => {
  restore();
  vi.restoreAllMocks();
  for (const name of ['showModal', 'close'] as const) {
    const original = dialogMethods[name];
    if (original) Object.defineProperty(HTMLDialogElement.prototype, name, original);
    else Reflect.deleteProperty(HTMLDialogElement.prototype, name);
  }
});
function mount(path = '/conversations', count = 2, messages = 2) {
  const s = installHistoryServer(count, messages);
  restore = s.restore;
  render(
    <StrictMode>
      <LanguageProvider>
        <MemoryRouter initialEntries={[path]}>
          <App />
        </MemoryRouter>
      </LanguageProvider>
    </StrictMode>,
  );
  return s;
}
describe('private bilingual conversation workspace', () => {
  it('lists and opens ordered saved messages under StrictMode', async () => {
    mount();
    await userEvent.click(await screen.findByRole('link', { name: /Synthetic conversation 1/ }));
    await screen.findByText('Synthetic message 1');
    expect(screen.getByText('Synthetic message 2')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Synthetic conversation 1' })).toHaveFocus();
  });
  it('creates a conversation and saves only a user message', async () => {
    const s = mount();
    await screen.findByRole('link', { name: /Synthetic conversation 1/ });
    fireEvent.change(screen.getByLabelText('New conversation title (optional)'), {
      target: { value: 'New synthetic topic' },
    });
    await userEvent.click(screen.getByRole('button', { name: 'Create conversation' }));
    await screen.findByRole('heading', { name: 'New synthetic topic' });
    fireEvent.change(screen.getByLabelText('Your fictional message'), {
      target: { value: 'Synthetic permit question' },
    });
    await userEvent.click(screen.getByRole('button', { name: 'Save message' }));
    await screen.findByText('Synthetic permit question');
    const call = s.calls.find((c) => c.init.method === 'POST' && c.path.includes('/messages'))!;
    expect(JSON.parse(call.init.body as string)).toEqual({ content: 'Synthetic permit question' });
    expect(screen.queryByText('assistant', { exact: true })).not.toBeInTheDocument();
  });
  it('renames with an ETag and deletes only after explicit confirmation', async () => {
    const s = mount('/conversations/' + firstId);
    await screen.findByText('Synthetic message 1');
    fireEvent.change(screen.getByLabelText('Conversation title'), {
      target: { value: 'Renamed synthetic topic' },
    });
    await userEvent.click(screen.getByRole('button', { name: 'Save title' }));
    await screen.findByRole('heading', { name: 'Renamed synthetic topic' });
    await userEvent.click(screen.getByRole('button', { name: 'Delete conversation' }));
    expect(screen.getByRole('button', { name: 'Keep conversation' })).toHaveFocus();
    await userEvent.click(screen.getByRole('button', { name: 'Keep conversation' }));
    expect(s.records.has(firstId)).toBe(true);
    expect(screen.getByRole('button', { name: 'Delete conversation' })).toHaveFocus();
    await userEvent.click(screen.getByRole('button', { name: 'Delete conversation' }));
    await userEvent.click(screen.getByRole('button', { name: 'Delete permanently' }));
    await screen.findByRole('heading', { name: 'Choose a conversation' });
    expect(s.records.has(firstId)).toBe(false);
  });
  it('loads bounded conversation and message pages without duplicates', async () => {
    mount('/conversations/' + firstId, 21, 21);
    await screen.findByText('Synthetic message 1');
    expect(screen.queryByText('Synthetic message 21')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Load more messages' }));
    await screen.findByText('Synthetic message 21');
    await userEvent.click(screen.getByRole('button', { name: 'Load more conversations' }));
    expect(
      (await screen.findByText('Synthetic conversation 21', { exact: true })).closest('a'),
    ).toHaveAttribute('href', '/conversations/10000000-0000-4000-8000-000000000021');
    expect(screen.getAllByText('Synthetic message 1', { exact: true })).toHaveLength(1);
  });
  it('renders plain text rather than injected HTML and supports Kiswahili', async () => {
    const s = mount('/conversations/' + firstId);
    s.messages.get(firstId)![0]!.content = '<img src=x onerror=alert(1)>';
    await screen.findByText('<img src=x onerror=alert(1)>');
    expect(document.querySelector('.history-messages img')).toBeNull();
    await userEvent.selectOptions(screen.getByRole('combobox'), 'sw');
    await screen.findByRole('heading', { name: 'Mazungumzo yako yaliyohifadhiwa' });
    expect(screen.getByLabelText('Ujumbe wako wa kubuni')).toBeInTheDocument();
  });
  it('shows unavailable and empty states with a working reload', async () => {
    const s = mount('/conversations', 0);
    await screen.findByText('No saved conversations yet. Create one to begin.');
    s.fetcher.mockResolvedValueOnce(s.response(503));
    await userEvent.click(screen.getByRole('button', { name: 'Refresh conversations' }));
    await screen.findByRole('alert');
    await userEvent.click(screen.getByRole('button', { name: 'Refresh conversations' }));
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  });
  it('rejects cross-user/missing resource responses without showing old messages', async () => {
    mount('/conversations/' + crypto.randomUUID());
    await screen.findByRole('alert');
    expect(screen.queryByText('Synthetic message 1')).not.toBeInTheDocument();
  });
  it('removes history immediately after cross-tab session invalidation', async () => {
    mount('/conversations/' + firstId);
    await screen.findByText('Synthetic message 1');
    const channel = new BroadcastChannel('county.auth.invalidate.v1');
    channel.postMessage('invalidate');
    channel.close();
    await screen.findByRole('heading', { name: 'Sign in' });
    expect(screen.queryByText('Synthetic message 1')).not.toBeInTheDocument();
  });
  it('does not render delayed history from the previous selection', async () => {
    const s = mount();
    await screen.findByRole('link', { name: /Synthetic conversation 1/ });
    const original = s.fetcher.getMockImplementation()!;
    let release!: () => void;
    let delayed = false;
    s.fetcher.mockImplementation((url, init) => {
      if (url.includes(firstId + '/messages') && !delayed && !init?.signal?.aborted) {
        delayed = true;
        // Return headers promptly so the auth lock can serve the next selection.
        // Delay only the body to exercise an actual late-response render race.
        return Promise.resolve(
          new Response(
            new ReadableStream<Uint8Array>({
              start(controller) {
                release = () => {
                  controller.enqueue(
                    new TextEncoder().encode(
                      JSON.stringify({
                        items: [
                          {
                            ...s.messages.get(firstId)![0]!,
                            content: 'Old selection must stay hidden',
                          },
                        ],
                        next_cursor: null,
                      }),
                    ),
                  );
                  controller.close();
                };
              },
            }),
            { headers: { 'Content-Type': 'application/json' } },
          ),
        );
      }
      return original(url, init);
    });
    await userEvent.click(screen.getByRole('link', { name: /Synthetic conversation 1/ }));
    await vi.waitFor(() => expect(release).toBeDefined());
    await userEvent.click(screen.getByRole('link', { name: /Synthetic conversation 2/ }));
    await screen.findByRole('heading', { name: 'Synthetic conversation 2' });
    await act(async () => {
      release();
      await Promise.resolve();
    });
    expect(screen.queryByText('Old selection must stay hidden')).not.toBeInTheDocument();
    expect(s.calls.some((c) => c.path.includes(secondId))).toBe(true);
  });
});
