import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { useNavigate } from 'react-router';
import { useLanguage } from '../../i18n/language';
import { useConversations } from './context';
import { issue, text } from './contracts';
import type { Conversation, HistoryIssue, Message } from './contracts';
import { HistoryNotice } from './HistoryNotice';
import { DeleteDialog } from './DeleteDialog';

type Detail = {
  conversation: Conversation;
  etag: string;
  messages: Message[];
  cursor: string | null;
};
export function ConversationDetail({ id, onChanged }: { id: string; onChanged: () => void }) {
  const client = useConversations();
  const { t, language } = useLanguage();
  const navigate = useNavigate();
  const [data, setData] = useState<Detail | null>(null);
  const [error, setError] = useState<HistoryIssue | null>(null);
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState('');
  const [draft, setDraft] = useState('');
  const [confirm, setConfirm] = useState(false);
  const [deletionError, setDeletionError] = useState<HistoryIssue | null>(null);
  const [announcement, setAnnouncement] = useState('');
  const [load, setLoad] = useState(0);
  const alive = useRef(false);
  const working = useRef(false);
  const epoch = useRef(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const deletionButton = useRef<HTMLButtonElement>(null);
  useSyncExternalStore(client.subscribe, client.getRevision);
  const pending = client.pending(id);
  useEffect(() => {
    // Restore focus after the dialog has unmounted and closed. Focusing the
    // background in the cancel handler fails while the modal makes it inert.
    if (!confirm) deletionButton.current?.focus();
  }, [confirm]);
  useEffect(() => {
    alive.current = true;
    const controller = new AbortController();
    const current = ++epoch.current;
    Promise.all([
      client.get(id, controller.signal),
      client.history(id, undefined, controller.signal),
    ])
      .then(([item, history]) => {
        if (alive.current && current === epoch.current) {
          setData({
            conversation: item.value,
            etag: item.etag,
            messages: history.items,
            cursor: history.next_cursor,
          });
          setTitle(item.value.title);
          setError(null);
        }
      })
      .catch((e: unknown) => {
        if (alive.current && current === epoch.current) {
          setData(null);
          setError(issue(e));
        }
      });
    return () => {
      alive.current = false;
      controller.abort();
    };
  }, [client, id, load]);
  const selectedId = data?.conversation.id;
  useEffect(() => {
    if (selectedId) heading.current?.focus();
  }, [selectedId]);
  async function perform(work: () => Promise<void>) {
    if (working.current) return;
    working.current = true;
    setBusy(true);
    setError(null);
    try {
      await work();
    } catch (e) {
      if (alive.current) setError(issue(e));
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function save() {
    await client.send(id, pending?.content ?? text(draft, 4000));
    if (!alive.current) return;
    // A message ETag may include another tab's metadata update. Read the full
    // metadata again rather than pairing a new version with an old title.
    setData(null);
    setLoad((v) => v + 1);
    setDraft('');
    setAnnouncement('historySaved');
    onChanged();
  }
  function more() {
    if (!data?.cursor) return;
    const cursor = data.cursor;
    void perform(async () => {
      const next = await client.history(id, cursor);
      if (!alive.current) return;
      if (next.next_cursor === cursor) throw new Error('Invalid pagination');
      const merged = new Map(data.messages.map((m) => [m.id, m]));
      next.items.forEach((m) => merged.set(m.id, m));
      setData({
        ...data,
        messages: [...merged.values()].sort((a, b) => a.sequence - b.sequence),
        cursor: next.next_cursor,
      });
    });
  }
  function reload() {
    if (!working.current) {
      setData(null);
      setLoad((v) => v + 1);
    }
  }
  return (
    <section
      className="history-detail"
      aria-label={t('historySavedConversation')}
      aria-busy={busy || (!data && !error)}
    >
      <HistoryNotice issue={error} />
      {!data ? (
        <>
          {!error ? <p role="status">{t('historyLoading')}</p> : null}
          <button type="button" className="secondary-button" onClick={reload}>
            {t('historyReload')}
          </button>
        </>
      ) : (
        <>
          <header>
            <p className="eyebrow">{t('historySavedConversation')}</p>
            <h2 id="conversation-heading" ref={heading} tabIndex={-1}>
              {data.conversation.title}
            </h2>
          </header>
          <div className="history-actions">
            <button type="button" className="secondary-button" onClick={reload} disabled={busy}>
              {t('historyReload')}
            </button>
            <button
              type="button"
              className="danger-button"
              ref={deletionButton}
              onClick={() => {
                setDeletionError(null);
                setConfirm(true);
              }}
              disabled={busy}
            >
              {t('historyDelete')}
            </button>
          </div>
          <form
            className="history-form"
            onSubmit={(e) => {
              e.preventDefault();
              void perform(async () => {
                const renamed = await client.rename(id, title, data.etag);
                if (alive.current) {
                  setData({ ...data, conversation: renamed.value, etag: renamed.etag });
                  setTitle(renamed.value.title);
                  setAnnouncement('historyRenamed');
                  onChanged();
                }
              });
            }}
          >
            <label htmlFor="conversation-title">{t('historyRenameLabel')}</label>
            <input
              id="conversation-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={busy}
              autoComplete="off"
              aria-describedby="title-help"
            />
            <p id="title-help" className="field-help">
              {t('historyTitleHelp')}
            </p>
            <button className="secondary-button" type="submit" disabled={busy}>
              {t('historyRename')}
            </button>
          </form>
          <h3>{t('historyMessages')}</h3>
          {data.messages.length === 0 ? (
            <p>{t('historyMessagesEmpty')}</p>
          ) : (
            <ol className="history-messages" aria-label={t('historyMessages')}>
              {data.messages.map((m) => (
                <li key={m.id}>
                  <div className="message-meta">
                    <strong>{t('historyYou')}</strong>
                    <time dateTime={m.created_at}>
                      {new Date(m.created_at).toLocaleString(language === 'sw' ? 'sw-KE' : 'en-KE')}
                    </time>
                  </div>
                  <p lang={m.language}>{m.content}</p>
                </li>
              ))}
            </ol>
          )}
          {data.cursor ? (
            <button type="button" className="secondary-button" disabled={busy} onClick={more}>
              {t('historyMoreMessages')}
            </button>
          ) : null}
          <form
            className="history-form"
            onSubmit={(e) => {
              e.preventDefault();
              void perform(save);
            }}
          >
            <label htmlFor="message-content">{t('historyMessageLabel')}</label>
            <textarea
              id="message-content"
              value={pending?.content ?? draft}
              onChange={(e) => setDraft(e.target.value)}
              readOnly={Boolean(pending)}
              disabled={busy}
              rows={5}
              autoComplete="off"
              spellCheck={false}
              aria-describedby="message-help message-length"
            />
            <p id="message-help" className="field-help">
              {t('historyMessageHelp')}
            </p>
            <p id="message-length">{Array.from(pending?.content ?? draft).length} / 4000</p>
            {pending?.status === 'uncertain' ? <p role="status">{t('historyUncertain')}</p> : null}
            <button
              type="submit"
              className="primary-button"
              disabled={busy || pending?.status === 'saving'}
            >
              {busy ? t('authWorking') : pending ? t('historyRetrySave') : t('historySaveMessage')}
            </button>
          </form>
          <p role="status" className="history-announcement">
            {announcement === 'historySaved'
              ? t('historySaved')
              : announcement === 'historyRenamed'
                ? t('historyRenamed')
                : ''}
          </p>
        </>
      )}
      {confirm ? (
        <DeleteDialog
          busy={busy}
          error={deletionError}
          onCancel={() => {
            setConfirm(false);
          }}
          onConfirm={() => {
            if (working.current) return;
            working.current = true;
            setBusy(true);
            setDeletionError(null);
            void client
              .remove(id)
              .then(() => {
                if (alive.current) {
                  setConfirm(false);
                  onChanged();
                  void navigate('/conversations', { replace: true });
                }
              })
              .catch((e: unknown) => {
                if (alive.current) setDeletionError(issue(e));
              })
              .finally(() => {
                working.current = false;
                if (alive.current) setBusy(false);
              });
          }}
        />
      ) : null}
    </section>
  );
}
