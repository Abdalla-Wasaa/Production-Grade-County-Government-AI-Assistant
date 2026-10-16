import { Component } from 'react';
import type { ReactNode } from 'react';
import { dictionaries } from '../i18n/messages';
import type { Language } from '../i18n/messages';

interface Props {
  children: ReactNode;
  language: Language;
}
export class AppErrorBoundary extends Component<Props, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (!this.state.failed) return this.props.children;
    const copy = dictionaries[this.props.language];
    return (
      <main className="page-width error-page" role="alert">
        <h1>{copy.errorTitle}</h1>
        <p>{copy.errorBody}</p>
        <button className="primary-button" onClick={() => window.location.reload()}>
          {copy.reload}
        </button>
      </main>
    );
  }
}
