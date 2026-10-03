import { createElement as h } from 'react'
import { Menu, Search } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import useAuth from '../../hooks/useAuth'
import SelectorIdioma from './SelectorIdioma'

const referenceDate = new Date()

export default function Header({ onMenuClick }) {
    const { t, i18n } = useTranslation()
    const { user } = useAuth()
    const locale = i18n.resolvedLanguage === 'en' ? 'en-US' : 'es-MX'
    const today = new Intl.DateTimeFormat(locale, { weekday: 'long', day: 'numeric', month: 'long' }).format(referenceDate)
    return h('header', { className: 'topbar' },
        h('button', { className: 'icon-button mobile-menu-button', onClick: onMenuClick, 'aria-label': t('header.menu') }, h(Menu, { size: 20 })),
        h('div', { className: 'topbar-context' }, h('span', { className: 'topbar-kicker' }, t('header.today')), h('span', { className: 'topbar-date' }, today)),
        h('div', { className: 'topbar-actions' }, h('button', { className: 'icon-button search-button', 'aria-label': t('nav.transactions') }, h(Search, { size: 18 })), h(SelectorIdioma), h('span', { className: 'topbar-divider' }), h('div', { className: 'topbar-user' }, h('span', { className: 'avatar' }, user && user.name ? user.name.slice(0, 1) : ''), h('span', { className: 'topbar-user-copy' }, h('strong', null, user ? user.name : ''), h('small', null, t(`header.${user ? user.role : 'owner'}`)))))
    )
}