import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AppErrorBoundary } from './AppErrorBoundary';

function Broken(): never {
  throw new Error('password=must-not-escape stacktrace private-host');
}
describe('safe rendering failure', () => {
  it.each(['en', 'sw'] as const)('uses fixed %s fallback without exception data', (language) => {
    // React's root error reporting is separately disabled in the production entry.
    vi.spyOn(console, 'error').mockImplementation(() => {});
    render(
      <AppErrorBoundary language={language}>
        <Broken />
      </AppErrorBoundary>,
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByRole('button')).toHaveTextContent(
      language === 'en' ? 'Reload page' : 'Pakia ukurasa upya',
    );
    expect(document.body.textContent).not.toMatch(/password|stacktrace|private-host/);
  });
});
