import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { LanguageSelector } from '../components/LanguageSelector';
import { LanguageProvider } from './LanguageProvider';
import { dictionaries, LANGUAGE_STORAGE_KEY, readLanguage, resolveMessage } from './messages';
import { Text } from './Text';

function Harness() {
  return (
    <LanguageProvider>
      <LanguageSelector />
      <Text message="homeTitle" />
    </LanguageProvider>
  );
}
describe('bilingual resources', () => {
  it('has complete, nonempty dictionaries', () => {
    expect(Object.keys(dictionaries.sw).sort()).toEqual(Object.keys(dictionaries.en).sort());
    for (const dictionary of Object.values(dictionaries)) {
      expect(Object.values(dictionary).every((value) => value.trim().length > 0)).toBe(true);
    }
  });
  it('persists only a language enum and restores it on remount', async () => {
    const user = userEvent.setup();
    const view = render(<Harness />);
    await user.selectOptions(screen.getByRole('combobox'), 'sw');
    expect(localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('sw');
    expect(localStorage.length).toBe(1);
    view.unmount();
    render(<Harness />);
    expect(screen.getByRole('combobox')).toHaveValue('sw');
    expect(document.documentElement.lang).toBe('sw');
  });
  it.each(['invalid', 'SW', '<script>alert(1)</script>', ''])(
    'rejects stored preference %s',
    (value) => {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, value);
      expect(readLanguage()).toBe('en');
    },
  );
  it('handles both storage reads and writes being denied', async () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('Denied');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('Denied');
    });
    const user = userEvent.setup();
    render(<Harness />);
    await user.selectOptions(screen.getByRole('combobox'), 'sw');
    expect(document.documentElement.lang).toBe('sw');
    expect(screen.getByText(dictionaries.sw.homeTitle)).toBeInTheDocument();
  });
  it('falls back to English for missing or empty translations', () => {
    expect(resolveMessage('sw', 'homeTitle', { en: dictionaries.en, sw: {} })).toEqual({
      text: dictionaries.en.homeTitle,
      language: 'en',
    });
    expect(
      resolveMessage('sw', 'homeTitle', { en: dictionaries.en, sw: { homeTitle: ' ' } }).language,
    ).toBe('en');
    expect(resolveMessage('sw', 'homeTitle', { en: {}, sw: {} }).text).toBe(
      dictionaries.en.errorTitle,
    );
  });
  it('marks English fallback within Kiswahili with the correct language', () => {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, 'sw');
    const original = dictionaries.sw.homeTitle;
    try {
      dictionaries.sw.homeTitle = '';
      render(<Harness />);
      expect(screen.getByText(dictionaries.en.homeTitle)).toHaveAttribute('lang', 'en');
    } finally {
      dictionaries.sw.homeTitle = original;
    }
  });
});
