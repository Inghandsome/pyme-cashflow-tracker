import { createElement as h } from 'react'
import { Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export default function SelectorIdioma() {
    const { i18n, t } = useTranslation()
    return h('label', { className: 'language-select', 'aria-label': t('language.label') },
        h(Languages, { size: 16, 'aria-hidden': true }),
        h('select', { value: i18n.resolvedLanguage || 'es', onChange: (event) => i18n.changeLanguage(event.target.value) },
            h('option', { value: 'es' }, 'ES'), h('option', { value: 'en' }, 'EN')))
}