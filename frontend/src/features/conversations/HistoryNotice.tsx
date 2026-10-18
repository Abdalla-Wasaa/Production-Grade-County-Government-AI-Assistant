import { useEffect, useRef } from 'react';
import { useLanguage } from '../../i18n/language';
import type { HistoryIssue } from './contracts';
export function HistoryNotice({ issue }: { issue: HistoryIssue | null }) {
  const { t } = useLanguage();
  const ref = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    if (issue) ref.current?.focus();
  }, [issue]);
  return issue ? (
    <p className="auth-feedback" role="alert" tabIndex={-1} ref={ref}>
      {t(`history_${issue}`)}
    </p>
  ) : null;
}
