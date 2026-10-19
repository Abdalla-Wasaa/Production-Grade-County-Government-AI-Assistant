import { useEffect, useId, useRef } from 'react';
import { useLanguage } from '../../i18n/language';
import type { HistoryIssue } from './contracts';
import { HistoryNotice } from './HistoryNotice';
export function DeleteDialog({
  busy,
  error,
  onCancel,
  onConfirm,
}: {
  busy: boolean;
  error: HistoryIssue | null;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const { t } = useLanguage();
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const id = useId();
  useEffect(() => {
    const node = dialog.current;
    node?.showModal();
    cancel.current?.focus();
    return () => node?.close();
  }, []);
  return (
    <dialog
      ref={dialog}
      className="history-dialog"
      aria-labelledby={id + '-title'}
      aria-describedby={id + '-description'}
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onCancel();
      }}
    >
      <h2 id={id + '-title'}>{t('historyDeleteTitle')}</h2>
      <p id={id + '-description'}>{t('historyDeleteHelp')}</p>
      <HistoryNotice issue={error} />
      <div className="history-actions">
        <button
          ref={cancel}
          type="button"
          className="secondary-button"
          onClick={onCancel}
          disabled={busy}
        >
          {t('historyCancel')}
        </button>
        <button type="button" className="danger-button" onClick={onConfirm} disabled={busy}>
          {busy ? t('authWorking') : t('historyDeleteConfirm')}
        </button>
      </div>
    </dialog>
  );
}
