import type { ReactNode } from 'react';

interface StateNoticeProps {
  kind: 'loading' | 'error' | 'empty';
  title: ReactNode;
  children: ReactNode;
}
export function StateNotice({ kind, title, children }: StateNoticeProps) {
  return (
    <section
      className={`state-notice state-${kind}`}
      role={kind === 'error' ? 'alert' : kind === 'loading' ? 'status' : undefined}
      aria-live={kind === 'loading' ? 'polite' : undefined}
    >
      <span className="state-symbol" aria-hidden="true">
        {kind === 'error' ? '!' : kind === 'loading' ? '…' : '○'}
      </span>
      <h2>{title}</h2>
      <p>{children}</p>
    </section>
  );
}
