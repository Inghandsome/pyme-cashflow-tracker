import { createElement as h } from 'react'
import { ArrowLeft, Construction } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function PlaceholderPage({ pageKey }) {
    const { t } = useTranslation()
    const section = t(`nav.${pageKey}`)
    return h('div', { className: 'placeholder-page' },
        h('div', { className: 'placeholder-mark' }, h(Construction, { size: 24, strokeWidth: 1.7 })),
        h('span', { className: 'eyebrow' }, t('placeholder.eyebrow')),
        h('h1', null, t('placeholder.title', { section })), h('p', null, t('placeholder.description')),
        h(Link, { className: 'placeholder-link', to: '/dashboard' }, h(ArrowLeft, { size: 16 }), t('placeholder.back')))
}