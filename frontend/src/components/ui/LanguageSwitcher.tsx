import { Globe } from 'lucide-preact';
import { useI18nStore } from '../../store/i18n';

export function LanguageSwitcher() {
  const { language, setLanguage } = useI18nStore();

  return (
    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
      <Globe className="w-4 h-4" />
      <select
        value={language}
        onChange={(e) => setLanguage(e.currentTarget.value as 'en' | 'zh')}
        className="bg-transparent border-none focus:ring-0 cursor-pointer hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
      >
        <option value="en">EN</option>
        <option value="zh">中</option>
      </select>
    </div>
  );
}
