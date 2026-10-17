import { useEffect, useRef } from 'react';
import { useLanguage } from '../../i18n/language';
import type { AuthIssue } from './contracts';
export function AuthNotice({ issue }: { issue: AuthIssue | null }) {
  const { t } = useLanguage();
  const ref = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    if (issue) ref.current?.focus();
  }, [issue]);
  return (
    <p
      id="auth-feedback"
      className="auth-feedback"
      role={issue ? 'alert' : 'status'}
      tabIndex={-1}
      ref={ref}
    >
      {issue ? t(`auth_${issue}`) : ''}
    </p>
  );
}
