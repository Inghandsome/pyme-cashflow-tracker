import { createElement as h, useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { LoaderCircle } from 'lucide-react'
import { AuthProvider } from './context/AuthContext'
import useAuth from './hooks/useAuth'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import PlaceholderPage from './pages/PlaceholderPage'
import TransactionsPage from './pages/TransactionsPage'

function AppRoutes() {
    const { user, isLoading } = useAuth()
    const { i18n } = useTranslation()
    useEffect(() => { document.documentElement.lang = i18n.resolvedLanguage || 'es' }, [i18n.resolvedLanguage])
    if (isLoading) return h('main', { className: 'auth-loading' }, h(LoaderCircle, { size: 22 }), h('span', null, i18n.t('common.loading')))
    return h(Routes, null,
        h(Route, { path: '/login', element: user ? h(Navigate, { to: '/dashboard', replace: true }) : h(Login) }),
        h(Route, { element: user ? h(Layout) : h(Navigate, { to: '/login', replace: true }) },
            h(Route, { index: true, element: h(Navigate, { to: '/dashboard', replace: true }) }),
            h(Route, { path: 'dashboard', element: h(Dashboard) }),
            h(Route, { path: 'transactions', element: h(TransactionsPage) }),
            ...['budgets', 'cashflow', 'receivables', 'reports', 'team'].map((page) => h(Route, { key: page, path: page, element: h(PlaceholderPage, { pageKey: page }) }))),
        h(Route, { path: '*', element: h(Navigate, { to: user ? '/dashboard' : '/login', replace: true }) }))
}

export default function App() {
    return h(AuthProvider, null, h(BrowserRouter, null, h(AppRoutes)))
}