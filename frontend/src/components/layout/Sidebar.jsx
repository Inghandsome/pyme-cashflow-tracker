import { createElement as h, Fragment, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Armchair, BarChart3, BookOpenText, ChevronLeft, CircleDollarSign, ClipboardList, LayoutDashboard, LogOut, ReceiptText, Users, WalletCards, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import useAuth from '../../hooks/useAuth'

const navigation = [
    { key: 'overview', to: '/dashboard', icon: LayoutDashboard },
    { key: 'transactions', to: '/transactions', icon: ReceiptText },
    { key: 'budgets', to: '/budgets', icon: ClipboardList, ownerOnly: true },
    { key: 'cashflow', to: '/cashflow', icon: BarChart3, ownerOnly: true },
    { key: 'receivables', to: '/receivables', icon: CircleDollarSign },
    { key: 'reports', to: '/reports', icon: BookOpenText, ownerOnly: true },
    { key: 'team', to: '/team', icon: Users, ownerOnly: true },
]

export default function Sidebar({ isOpen, onClose }) {
    const { t } = useTranslation()
    const { user, signOut } = useAuth()
    const [collapsed, setCollapsed] = useState(false)
    const links = navigation.filter((item) => !item.ownerOnly || (user && user.role === 'owner')).map(({ key, to, icon: Icon }) => h(NavLink, {
        key,
        to,
        onClick: onClose,
        title: t(`nav.${key}`),
        className: ({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`,
    }, h(Icon, { size: 18, strokeWidth: 1.8, 'aria-hidden': true }), h('span', null, t(`nav.${key}`)), key === 'overview' && h('span', { className: 'nav-indicator' })))

    return h(Fragment, null,
        isOpen && h('button', { className: 'sidebar-scrim', 'aria-label': t('header.menu'), onClick: onClose }),
        h('aside', { className: `sidebar ${collapsed ? 'sidebar-collapsed' : ''} ${isOpen ? 'sidebar-open' : ''}` },
            h('div', { className: 'sidebar-brand' }, h('span', { className: 'brand-mark' }, h(Armchair, { size: 21, strokeWidth: 1.8 })), h('span', { className: 'brand-copy' }, h('strong', null, t('brand.name')), h('small', null, t('brand.descriptor'))), h('button', { className: 'icon-button sidebar-close', 'aria-label': t('header.menu'), onClick: onClose }, h(X, { size: 18 }))),
            h('div', { className: 'workspace-label' }, t('nav.workspace')),
            h('nav', { className: 'sidebar-nav', 'aria-label': t('nav.workspace') }, links),
            h('div', { className: 'sidebar-bottom' },
                h('div', { className: 'store-card' }, h('span', { className: 'store-icon' }, h(WalletCards, { size: 17 })), h('span', { className: 'store-copy' }, h('strong', null, t('nav.store')), h('small', null, h('i'), t('nav.online')))),
                h('div', { className: 'profile-row' }, h('span', { className: 'avatar avatar-sidebar' }, user && user.name ? user.name.slice(0, 1) : ''), h('span', { className: 'profile-copy' }, h('strong', null, user ? user.name : ''), h('small', null, t(`header.${user ? user.role : 'owner'}`))), h('button', { className: 'icon-button logout-button', 'aria-label': t('common.logout'), title: t('common.logout'), onClick: signOut }, h(LogOut, { size: 17 })))),
            h('button', { className: 'collapse-button', onClick: () => setCollapsed((value) => !value), 'aria-label': t('header.menu') }, h(ChevronLeft, { size: 16 }))))
}