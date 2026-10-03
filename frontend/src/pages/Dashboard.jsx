import { createElement as h, useEffect, useState } from 'react'
import { ArrowUpRight, ArrowUpRightFromSquare, CalendarDays, CircleHelp, LoaderCircle, Plus, RefreshCw } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import useAuth from '../hooks/useAuth'
import useCurrency from '../hooks/useCurrency'
import { apiRequest } from '../services/api'
import { ApiError } from '../services/api'

function MetricCard({ metric }) {
    const { t } = useTranslation()
    const formatCurrency = useCurrency()
    const value = metric.isCount ? new Intl.NumberFormat().format(metric.amount) : formatCurrency(metric.amount)
    return h(Card, { className: 'metric-card' },
        h('div', { className: 'metric-heading' }, h('span', null, t(`dashboard.${metric.key}`)), h('button', { className: 'icon-button hint-button', 'aria-label': t('dashboard.period') }, h(CircleHelp, { size: 15 }))),
        h('strong', { className: 'metric-amount' }, value),
        h('div', { className: 'metric-foot' }, h('span', { className: 'metric-change metric-neutral' }, t(metric.caption, metric.detail === undefined ? undefined : { count: metric.detail }))))
}

function CashflowChart({ days }) {
    const { t, i18n } = useTranslation()
    const formatCurrency = useCurrency()
    const maxAmount = Math.max(1, ...days.flatMap((day) => [day.ingresos, day.egresos]))
    const chartDays = days.map((day) => {
        const label = new Intl.DateTimeFormat(i18n.resolvedLanguage === 'en' ? 'en-US' : 'es-MX', { weekday: 'short' }).format(new Date(`${day.fecha}T12:00:00`))
        const incomeHeight = `${Math.max(day.ingresos / maxAmount * 100, day.ingresos ? 2 : 0)}%`
        const expenseHeight = `${Math.max(day.egresos / maxAmount * 100, day.egresos ? 2 : 0)}%`
        return h('div', { className: 'chart-day', key: day.fecha }, h('div', { className: 'bar-pair' }, h('span', { className: 'chart-bar chart-income', style: { height: incomeHeight } }), h('span', { className: 'chart-bar chart-expense', style: { height: expenseHeight } })), h('small', null, label))
    })
    const labels = [1, 0.75, 0.5, 0.25, 0].map((fraction) => h('span', { key: fraction }, formatCurrency(maxAmount * fraction)))
    return h('div', { className: 'chart-area', role: 'img', 'aria-label': t('dashboard.cashflowSubtitle') },
        h('div', { className: 'chart-y-labels' }, labels),
        h('div', { className: 'chart-plot' }, h('div', { className: 'chart-grid' }, ...[1, 2, 3, 4, 5].map((line) => h('i', { key: line }))), h('div', { className: 'chart-columns' }, chartDays)))
}

function ActivityList({ transactions }) {
    const { t, i18n } = useTranslation()
    const formatCurrency = useCurrency()
    const dateFormatter = new Intl.DateTimeFormat(i18n.resolvedLanguage === 'en' ? 'en-US' : 'es-MX', { day: 'numeric', month: 'short' })
    return h('div', { className: 'activity-list' }, transactions.map((transaction) => {
        const type = transaction.tipo === 'ingreso' ? 'income' : 'expense'
        const initials = (transaction.categoria || transaction.descripcion || '?').slice(0, 2).toLocaleUpperCase()
        const fecha = transaction.fecha ? dateFormatter.format(new Date(`${transaction.fecha}T12:00:00`)) : ''
        const description = transaction.descripcion || transaction.categoria || t(type === 'income' ? 'dashboard.income' : 'dashboard.expenses')
        const amount = `${type === 'income' ? '+' : '-'}${formatCurrency(transaction.monto)}`
        return h('div', { className: 'activity-row', key: transaction.id },
            h('span', { className: `activity-avatar activity-${type}` }, initials),
            h('span', { className: 'activity-copy' }, h('strong', null, description), h('small', null, `${transaction.categoria || ''}${transaction.categoria && fecha ? ' · ' : ''}${fecha}`)),
            h('strong', { className: `activity-amount amount-${type}` }, amount))
    }))
}

export default function Dashboard() {
    const { t, i18n } = useTranslation()
    const { user, token } = useAuth()
    const navigate = useNavigate()
    const [data, setData] = useState(null)
    const [error, setError] = useState('')
    const [isLoading, setIsLoading] = useState(true)
    const [reloadKey, setReloadKey] = useState(0)

    useEffect(() => {
        let active = true
        apiRequest('/dashboard/resumen', { token, language: i18n.resolvedLanguage || 'es' })
            .then((summary) => {
                if (active) {
                    setData(summary);
                    setError('')
                }
            })
            .catch((requestError) => { if (active) setError(requestError instanceof ApiError ? requestError.message : t('common.connectionError')) })
            .finally(() => { if (active) setIsLoading(false) })
        return () => { active = false }
    }, [token, i18n.resolvedLanguage, reloadKey, t])

    if (isLoading) return h('div', { className: 'dashboard-state' }, h(LoaderCircle, { size: 22, className: 'spin-icon' }), h('span', null, t('common.loading')))
    if (error) return h('div', { className: 'dashboard-state dashboard-error', role: 'alert' }, h('p', null, error), h('button', {
        className: 'period-button',
        onClick: () => {
            setIsLoading(true);
            setError('');
            setReloadKey((value) => value + 1)
        }
    }, h(RefreshCw, { size: 15 }), t('dashboard.retry')))

    const isOwner = data.rol === 'dueno'
    const metrics = [
        { key: 'income', amount: data.totales.ingresos, caption: 'dashboard.period' },
        { key: 'expenses', amount: data.totales.egresos, caption: 'dashboard.period' },
        { key: 'balance', amount: data.totales.saldo, caption: 'dashboard.period' },
        ...(isOwner ? [{ key: 'receivables', amount: data.cuentas_por_cobrar.saldo, caption: 'dashboard.openAccounts', detail: data.cuentas_por_cobrar.abiertas }] : [{ key: 'movementCount', amount: data.cantidad_movimientos, caption: 'dashboard.today', isCount: true }]),
    ]
    const periodLabel = t(data.periodo.tipo === 'mes' ? 'dashboard.period' : 'dashboard.today')

    return h('div', { className: 'dashboard-page' },
        h('div', { className: 'page-heading' }, h('div', null, h('span', { className: 'eyebrow' }, t('nav.overview')), h('h1', null, t('dashboard.greeting', { name: user ? user.name : '' })), h('p', null, t('dashboard.subtitle'))), h('div', { className: 'heading-actions' }, h('span', { className: 'period-button' }, h(CalendarDays, { size: 16 }), periodLabel), h(Button, { className: 'add-movement', onClick: () => navigate('/transactions') }, h(Plus, { size: 17 }), t('nav.transactions')))),
        h('section', { className: 'metrics-grid', 'aria-label': t('nav.overview') }, metrics.map((metric) => h(MetricCard, { key: metric.key, metric }))),
        h('div', { className: 'dashboard-grid' },
            isOwner && h(Card, { className: 'chart-card' }, h('div', { className: 'section-heading' }, h('div', null, h('h2', null, t('dashboard.cashflowTitle')), h('p', null, t('dashboard.cashflowSubtitle'))), h('span', { className: 'icon-button chart-menu', 'aria-hidden': true }, h(ArrowUpRightFromSquare, { size: 16 }))), h('div', { className: 'chart-legend' }, h('span', null, h('i', { className: 'legend-income' }), t('dashboard.incomeLegend')), h('span', null, h('i', { className: 'legend-expense' }), t('dashboard.expenseLegend')), h('span', { className: 'chart-period' }, t('dashboard.week'))), h(CashflowChart, { days: data.flujo_diario })),
            h(Card, { className: 'activity-card' }, h('div', { className: 'section-heading' }, h('div', null, h('h2', null, t('dashboard.activityTitle')), h('p', null, periodLabel)), h('span', { className: 'icon-button chart-menu', 'aria-hidden': true }, h(ArrowUpRightFromSquare, { size: 16 }))), data.actividad.length ? h(ActivityList, { transactions: data.actividad }) : h('p', { className: 'empty-activity' }, t('dashboard.emptyActivity')), h('a', { className: 'activity-link', href: '/transactions' }, t('dashboard.viewAll'), h(ArrowUpRight, { size: 15 })))),
        h('p', { className: 'sample-data-note' }, t('dashboard.periodRange', { start: data.periodo.desde, end: data.periodo.hasta })))
}