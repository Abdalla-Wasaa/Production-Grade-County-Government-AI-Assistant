import { describe, it, expect } from 'vitest';
import { conversation, message, page, text } from './contracts';
import { firstId } from './testServer';
const row = {
  id: firstId,
  title: 'Synthetic',
  language: 'en',
  version: 1,
  created_at: '2026-10-18T12:00:00Z',
  updated_at: '2026-10-18T12:00:00Z',
  expires_at: '2026-11-17T12:00:00Z',
};
describe('persistence response and text boundaries', () => {
  it.each(['', '   ', '\0', '\ud800', 'x'.repeat(4001)])(
    'rejects invalid content without reflecting it',
    (content) => {
      expect(() => text(content, 4000)).toThrow('Conversation request could not be completed.');
    },
  );
  it('counts Unicode code points without truncation', () => {
    expect(text('😀'.repeat(4000), 4000)).toHaveLength(8000);
    expect(text('  Habari  ', 4000)).toBe('Habari');
  });
  it.each([
    { ...row, version: 0 },
    { ...row, language: 'fr' },
    { ...row, id: 'not-an-id' },
    { ...row, expires_at: 'invalid' },
  ])('rejects malformed metadata', (value) => {
    expect(() => conversation(value)).toThrow();
  });
  it('copies only public fields', () => {
    expect(conversation({ ...row, user_id: 'not-public' })).not.toHaveProperty('user_id');
  });
  it.each(['assistant', 'system', 'tool'])('rejects non-user history role %s', (role) => {
    expect(() =>
      message(
        {
          id: crypto.randomUUID(),
          conversation_id: firstId,
          sequence: 1,
          role,
          content: 'Synthetic',
          language: 'en',
          created_at: row.created_at,
        },
        firstId,
      ),
    ).toThrow();
  });
  it('rejects cross-conversation history and oversized pages/cursors', () => {
    expect(() =>
      message(
        {
          id: crypto.randomUUID(),
          conversation_id: crypto.randomUUID(),
          sequence: 1,
          role: 'user',
          content: 'Synthetic',
          language: 'en',
          created_at: row.created_at,
        },
        firstId,
      ),
    ).toThrow();
    expect(() => page({ items: Array(21).fill(row), next_cursor: null }, conversation)).toThrow();
    expect(() => page({ items: [], next_cursor: 'x'.repeat(2049) }, conversation)).toThrow();
  });
});
