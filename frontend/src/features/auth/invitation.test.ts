import { afterEach, expect, it, vi } from 'vitest';
afterEach(() => {
  window.history.replaceState(null, '', '/');
});
it('scrubs a fragment before rendering and clears the in-memory handoff', async () => {
  vi.resetModules();
  window.history.replaceState(null, '', '/activate#token=' + 'a'.repeat(43));
  const invitation = await import('./invitation');
  expect(window.location.hash).toBe('');
  expect(invitation.invitationDraft()).toHaveLength(43);
  invitation.clearInvitationDraft();
  expect(invitation.invitationDraft()).toBe('');
});
it('never consumes a token in a query string', async () => {
  vi.resetModules();
  window.history.replaceState(null, '', '/activate?token=do-not-use');
  const invitation = await import('./invitation');
  expect(invitation.invitationDraft()).toBe('');
  expect(window.location.search).toBe('');
});
