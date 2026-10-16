import { Link } from 'react-router';
import { Text } from '../../i18n/Text';

export function HomePage() {
  return (
    <>
      <div className="hero-grid">
        <section className="hero-copy">
          <p className="eyebrow">
            <Text message="previewLabel" />
          </p>
          <h1 tabIndex={-1}>
            <Text message="homeTitle" />
          </h1>
          <p className="intro">
            <Text message="homeIntro" />
          </p>
          <Link className="primary-button" to="/assistant">
            <Text message="viewAssistant" />
            <span aria-hidden="true">↗</span>
          </Link>
        </section>
        <aside className="preview-card">
          <div className="card-motif" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <h2>
            <Text message="previewIncludes" />
          </h2>
          <p>
            <Text message="previewDescription" />
          </p>
          <ul>
            {(['featureLanguages', 'featureNavigation', 'featureScope'] as const).map((key) => (
              <li key={key}>
                <span aria-hidden="true" className="checkmark">
                  ✓
                </span>
                <Text message={key} />
              </li>
            ))}
          </ul>
        </aside>
      </div>
      <div className="principles-grid">
        {(
          [
            ['scopeTitle', 'scopeBody'],
            ['languageTitle', 'languageBody'],
            ['privacyTitle', 'privacyBody'],
          ] as const
        ).map(([title, body], index) => (
          <section className="principle" key={title}>
            <span className="section-number" aria-hidden="true">
              0{index + 1}
            </span>
            <h2>
              <Text message={title} />
            </h2>
            <p>
              <Text message={body} />
            </p>
          </section>
        ))}
      </div>
    </>
  );
}
