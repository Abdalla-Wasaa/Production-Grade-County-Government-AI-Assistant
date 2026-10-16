import { Link } from 'react-router';
import { Text } from '../../i18n/Text';
import { StateNotice } from '../../components/StateNotice';

export function AssistantPlaceholder() {
  return (
    <>
      <section className="page-introduction">
        <p className="eyebrow">
          <Text message="assistantEyebrow" />
        </p>
        <h1 tabIndex={-1}>
          <Text message="assistantTitle" />
        </h1>
        <p className="intro">
          <Text message="assistantIntro" />
        </p>
      </section>
      <div className="assistant-panel">
        <div className="assistant-panel-header">
          <span className="availability-badge">
            <Text message="unavailableBadge" />
          </span>
        </div>
        <StateNotice kind="empty" title={<Text message="emptyTitle" />}>
          <Text message="emptyBody" />
        </StateNotice>
      </div>
      <Link className="text-link" to="/">
        <span aria-hidden="true">← </span>
        <Text message="returnHome" />
      </Link>
    </>
  );
}
