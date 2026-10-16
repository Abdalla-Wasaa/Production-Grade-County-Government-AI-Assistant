import { useLanguage } from '../i18n/language';
import { Text } from '../i18n/Text';

export function LanguageSelector() {
  const { language, setLanguage } = useLanguage();
  return (
    <div className="language-control">
      <label htmlFor="interface-language">
        <Text message="languageLabel" />
      </label>
      <select
        id="interface-language"
        value={language}
        onChange={(event) => {
          setLanguage(event.target.value === 'sw' ? 'sw' : 'en');
        }}
      >
        <option value="en" lang="en">
          English
        </option>
        <option value="sw" lang="sw">
          Kiswahili
        </option>
      </select>
    </div>
  );
}
