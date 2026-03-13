import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { en } from '../i18n/locales/en';
import { zh } from '../i18n/locales/zh';

type Language = 'en' | 'zh';
const dictionaries = { en, zh };

interface I18nState {
  language: Language;
  setLanguage: (lang: Language) => void;
  // translation function
  t: (key: keyof typeof en, params?: Record<string, string | number>) => string;
}

export const useI18nStore = create<I18nState>()(
  persist(
    (set, get) => ({
      language: 'en', // default
      setLanguage: (lang) => set({ language: lang }),
      t: (key, params) => {
        const { language } = get();
        const dict = dictionaries[language] || dictionaries.en;
        let text = dict[key] || en[key] || key; // fallback to English then to key

        // Simple interpolation
        if (params) {
          Object.entries(params).forEach(([k, v]) => {
            text = text.replace(new RegExp(`{${k}}`, 'g'), String(v));
          });
        }
        return text;
      },
    }),
    {
      name: 'i18n-storage',
      partialize: (state) => ({ language: state.language }), // only save language
    }
  )
);
