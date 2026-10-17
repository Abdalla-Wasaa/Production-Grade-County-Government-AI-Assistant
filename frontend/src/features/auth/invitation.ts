// Evaluate before React: remove fragment secrets before rendering/navigation.
// Query-string tokens are never consumed. Only the explicit activation route reads
// a fragment; no analytics, console, storage or persistent history entry is used.
let pending = '';
export function captureInvitation(): void {
  if (window.location.pathname === '/activate') {
    const match = /^#token=([A-Za-z0-9_-]{43})$/.exec(window.location.hash);
    pending = match?.[1] ?? '';
    window.history.replaceState(null, '', '/activate');
  }
}
captureInvitation();
export function invitationDraft(): string {
  return pending;
}
export function clearInvitationDraft(): void {
  pending = '';
}
