import { describe, expect, it } from 'vitest';
import { readPublicConfig } from './config';

describe('public configuration', () => {
  it('defaults to the versioned same-origin API path', () => {
    expect(readPublicConfig({})).toEqual({ apiBaseUrl: '/api/v1' });
    expect(readPublicConfig({ VITE_API_BASE_URL: '/api/v2' }).apiBaseUrl).toBe('/api/v2');
  });
  it.each([
    '',
    '//evil.invalid/api',
    'https://secret@host.invalid/api',
    '/api/../admin',
    '/api?password=secret',
    '/api#token',
    'javascript:alert(1)',
    '/api/',
  ])('rejects unsafe path %s', (value) => {
    expect(() => readPublicConfig({ VITE_API_BASE_URL: value })).toThrow(
      'Invalid public API configuration.',
    );
  });
});
