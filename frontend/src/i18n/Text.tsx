import { useLanguage } from './language';
import { resolveMessage } from './messages';
import type { MessageKey } from './messages';

export function Text({ message }: { message: MessageKey }) {
  const { language } = useLanguage();
  const result = resolveMessage(language, message);
  return (
    <span lang={result.language !== language ? result.language : undefined}>{result.text}</span>
  );
}
