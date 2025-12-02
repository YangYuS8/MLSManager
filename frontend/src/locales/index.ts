/**
 * i18n Configuration
 *
 * Internationalization setup using react-i18next.
 * Supports: English (en-US), Simplified Chinese (zh-CN)
 * Default language is detected from browser settings.
 */

import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import enUS from './en-US.json'
import zhCN from './zh-CN.json'

const resources = {
  en: {
    translation: enUS,
  },
  zh: {
    translation: zhCN,
  },
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    supportedLngs: ['en', 'zh'],
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    react: {
      useSuspense: false,
    },
  })

export default i18n
