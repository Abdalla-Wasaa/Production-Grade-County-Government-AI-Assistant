import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';

beforeEach(() => {
  localStorage.clear();
  document.documentElement.lang = 'en';
  // Component tests cannot make network requests. Browser tests check the build.
  vi.stubGlobal(
    'fetch',
    vi.fn(() => {
      throw new Error('Unexpected network request');
    }),
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
