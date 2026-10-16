import { Link } from 'react-router';
import { Text } from '../../i18n/Text';

export function NotFoundPage() {
  return (
    <section className="page-introduction not-found">
      <p className="eyebrow">
        404 · <Text message="notFoundEyebrow" />
      </p>
      <h1 tabIndex={-1}>
        <Text message="notFoundTitle" />
      </h1>
      <p className="intro">
        <Text message="notFoundBody" />
      </p>
      <Link className="primary-button" to="/">
        <Text message="returnHome" />
      </Link>
    </section>
  );
}
