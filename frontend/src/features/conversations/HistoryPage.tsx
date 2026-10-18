import { useEffect, useRef, useState } from 'react';
import { NavLink, useNavigate, useParams } from 'react-router';
import { useLanguage } from '../../i18n/language';
import { useConversations } from './context';
import { ConversationDetail } from './ConversationDetail';
import { HistoryNotice } from './HistoryNotice';
import { issue } from './contracts';
import type { Conversation, HistoryIssue } from './contracts';

export function HistoryPage() {
  const client = useConversations();
  return <HistoryWorkspace key={client.scope} />;
}
function HistoryWorkspace() {
  const client = useConversations();
  const { t, language } = useLanguage();
  const navigate = useNavigate();
  const { id } = useParams();
  const [items, setItems] = useState<Conversation[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [error, setError] = useState<HistoryIssue | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState('');
  const [revision, setRevision] = useState(0);
  const alive = useRef(false);
  const requests = useRef(0);
  const creatingNow = useRef(false);
  useEffect(() => {
    alive.current = true;
    const controller = new AbortController();
    const request = ++requests.current;
    client
      .list(undefined, controller.signal)
      .then((page) => {
        if (alive.current && request === requests.current) {
          setItems(page.items);
          setCursor(page.next_cursor);
          setError(null);
          setLoading(false);
        }
      })
      .catch((e: unknown) => {
        if (alive.current && request === requests.current) {
          setError(issue(e));
          setLoading(false);
        }
      });
    return () => {
      alive.current = false;
      controller.abort();
    };
  }, [client, revision]);
  function reload() {
    setLoading(true);
    setRevision((n) => n + 1);
  }
  async function more() {
    if (loading || !cursor) return;
    setLoading(true);
    setError(null);
    const request = ++requests.current;
    const previous = cursor;
    try {
      const page = await client.list(previous);
      if (!alive.current || request !== requests.current) return;
      if (page.next_cursor === previous) throw new Error('Invalid pagination');
      setItems((old) => {
        const merged = new Map(old.map((item) => [item.id, item]));
        page.items.forEach((item) => merged.set(item.id, item));
        return [...merged.values()];
      });
      setCursor(page.next_cursor);
    } catch (e) {
      if (alive.current && request === requests.current) setError(issue(e));
    } finally {
      if (alive.current && request === requests.current) setLoading(false);
    }
  }
  return (
    <section className="history-page" aria-labelledby="history-heading">
      <header>
        <p className="eyebrow">{t('authSynthetic')}</p>
        <h1 id="history-heading" tabIndex={-1}>
          {t('historyTitle')}
        </h1>
        <p>{t('historyIntro')}</p>
      </header>
      <div className="history-layout">
        <section className="history-sidebar" aria-labelledby="history-list-heading">
          <h2 id="history-list-heading">{t('historyListTitle')}</h2>
          <form
            className="history-form"
            onSubmit={(e) => {
              e.preventDefault();
              if (creatingNow.current) return;
              creatingNow.current = true;
              setCreating(true);
              setError(null);
              void client
                .create(title, language)
                .then((result) => {
                  if (alive.current) {
                    setTitle('');
                    reload();
                    void navigate('/conversations/' + result.value.id);
                  }
                })
                .catch((e: unknown) => {
                  if (alive.current) setError(issue(e));
                })
                .finally(() => {
                  creatingNow.current = false;
                  if (alive.current) setCreating(false);
                });
            }}
          >
            <label htmlFor="new-conversation-title">{t('historyNewTitle')}</label>
            <input
              id="new-conversation-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={creating}
              autoComplete="off"
              aria-describedby="new-title-help"
            />
            <p id="new-title-help" className="field-help">
              {t('historyNewHelp')}
            </p>
            <button type="submit" className="primary-button" disabled={creating}>
              {creating ? t('authWorking') : t('historyCreate')}
            </button>
          </form>
          <HistoryNotice issue={error} />
          <button type="button" className="secondary-button" disabled={loading} onClick={reload}>
            {t('historyRefreshList')}
          </button>
          {loading ? (
            <p role="status">{t('historyLoading')}</p>
          ) : items.length === 0 && !error ? (
            <p>{t('historyEmpty')}</p>
          ) : null}
          <ul className="history-list" aria-label={t('historyListTitle')}>
            {items.map((item) => (
              <li key={item.id}>
                <NavLink to={'/conversations/' + item.id}>
                  <span>{item.title}</span>
                  <time dateTime={item.updated_at}>
                    {new Date(item.updated_at).toLocaleDateString(
                      language === 'sw' ? 'sw-KE' : 'en-KE',
                    )}
                  </time>
                </NavLink>
              </li>
            ))}
          </ul>
          {cursor ? (
            <button
              type="button"
              className="secondary-button"
              disabled={loading}
              onClick={() => {
                void more();
              }}
            >
              {t('historyMoreConversations')}
            </button>
          ) : null}
        </section>
        {id ? (
          <ConversationDetail key={id} id={id} onChanged={reload} />
        ) : (
          <section className="history-detail">
            <h2>{t('historySelectTitle')}</h2>
            <p>{t('historySelectHelp')}</p>
          </section>
        )}
      </div>
    </section>
  );
}
