import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import es from './locales/es.json'

const savedLanguage = window.localStorage.getItem('roble-language')

i18n.use(initReactI18next).init({
    resources: {
        es: { translation: es },
        en: { translation: en },
    },
    lng: savedLanguage === 'en' ? 'en' : 'es',
    fallbackLng: 'es',
    interpolation: { escapeValue: false },
})

i18n.on('languageChanged', (language) => {
    window.localStorage.setItem('roble-language', language)
})

export default i18n