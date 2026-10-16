import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StateNotice } from './StateNotice';

describe('state conventions', () => {
  it('announces loading politely', () => {
    render(
      <StateNotice kind="loading" title="Loading">
        Please wait.
      </StateNotice>,
    );
    expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite');
    expect(screen.getByRole('status')).toHaveTextContent('Please wait.');
  });
  it('announces errors and escapes untrusted text', () => {
    render(
      <StateNotice kind="error" title="Unavailable">
        {'<script>secret()</script>'}
      </StateNotice>,
    );
    expect(screen.getByRole('alert')).toHaveTextContent('<script>secret()</script>');
    expect(document.querySelector('script')).toBeNull();
  });
  it('keeps empty states out of live announcement regions', () => {
    render(
      <StateNotice kind="empty" title="Empty">
        No messages.
      </StateNotice>,
    );
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Empty');
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
