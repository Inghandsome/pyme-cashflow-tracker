import { createElement as h, useEffect, useState } from 'react'
import { ArrowDownLeft, ArrowUpRight, CircleAlert, LoaderCircle, Plus, RefreshCw } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import useAuth from '../hooks/useAuth'
import useCurrency from '../hooks/useCurrency'
import { apiRequest, ApiError } from '../services/api'

function fechaLocal() {
    const today = new Date()
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
}

export default function TransactionsPage() {
    const { t, i18n } = useTranslation()
    const { token, user } = useAuth()
    const formatCurrency = useCurrency()
    const [transactions, setTransactions] = useState([])
    const [totals, setTotals] = useState({ ingresos: 0, egresos: 0, saldo: 0 })
    const [categories, setCategories] = useState([])
    const [type, setType] = useState('egreso')
    const [categoryId, setCategoryId] = useState('')
    const [filter, setFilter] = useState('todos')
    const [isLoading, setIsLoading] = useState(true)
    const [isSaving, setIsSaving] = useState(false)
    const [error, setError] = useState('')
    const [saved, setSaved] = useState(false)
    const [reloadKey, setReloadKey] = useState(0)
    const isOwner = user && user.role === 'owner'
    const visibleCategories = categories.filter((category) => category.tipo === type)
    const visibleTransactions = filter === 'todos' ? transactions : transactions.filter((transaction) => transaction.tipo === filter)
    const dateLocale = i18n.resolvedLanguage === 'en' ? 'en-US' : 'es-MX'

    useEffect(() => {
        let active = true
        Promise.all([
            apiRequest('/transacciones?limite=100', { token, language: i18n.resolvedLanguage || 'es' }),
            apiRequest('/categorias', { token, language: i18n.resolvedLanguage || 'es' }),
        ]).then(([transactionData, categoryData]) => {
            if (!active) return
            setTransactions(transactionData.transacciones)
            setTotals(transactionData.totales)
            setCategories(categoryData)
            const firstCategory = categoryData.find((category) => category.tipo === 'egreso')
            setCategoryId(firstCategory ? String(firstCategory.id) : '')
            setError('')
        }).catch((requestError) => {
            if (active) setError(requestError instanceof ApiError ? requestError.message : t('common.connectionError'))
        }).finally(() => { if (active) setIsLoading(false) })
        return () => { active = false }
    }, [token, i18n.resolvedLanguage, reloadKey, t])

    async function handleSubmit(event) {
        event.preventDefault()
        const form = event.currentTarget
        const formData = new FormData(form)
        setError('')
        setSaved(false)
        setIsSaving(true)
        try {
            await apiRequest('/transacciones', {
                method: 'POST',
                token,
                language: i18n.resolvedLanguage || 'es',
                body: {
                    monto: formData.get('monto'),
                    tipo: type,
                    categoria_id: Number(formData.get('categoria_id')),
                    descripcion: formData.get('descripcion'),
                    fecha: isOwner ? formData.get('fecha') : undefined,
                    metodo_pago: formData.get('metodo_pago'),
                },
            })
            form.reset()
            setSaved(true)
            setReloadKey((value) => value + 1)
        } catch (requestError) {
            setError(requestError instanceof ApiError ? requestError.message : t('common.connectionError'))
        } finally {
            setIsSaving(false)
        }
    }

    const dateFormatter = new Intl.DateTimeFormat(dateLocale, { day: 'numeric', month: 'short', year: 'numeric' })
    const rows = visibleTransactions.map((transaction) => {
        const income = transaction.tipo === 'ingreso'
        const description = transaction.descripcion || transaction.categoria || t('transactions.noDescription')
        const date = transaction.fecha ? dateFormatter.format(new Date(`${transaction.fecha}T12:00:00`)) : '-'
        return h('tr', { key: transaction.id },
            h('td', null, h('span', { className: `transaction-type-icon ${income ? 'transaction-income' : 'transaction-expense'}` }, income ? h(ArrowDownLeft, { size: 16 }) : h(ArrowUpRight, { size: 16 }))),
            h('td', null, h('strong', { className: 'transaction-description' }, description), h('small', { className: 'transaction-mobile-category' }, transaction.categoria || '')),
            h('td', { className: 'transaction-date' }, date),
            h('td', { className: 'transaction-category' }, transaction.categoria || '-'),
            h('td', { className: 'transaction-method' }, t(`transactions.methods.${transaction.metodo_pago}`, { defaultValue: transaction.metodo_pago })),
            h('td', { className: `transaction-amount ${income ? 'amount-income' : 'amount-expense'}` }, `${income ? '+' : '-'}${formatCurrency(transaction.monto)}`))
    })

    return h('div', { className: 'transactions-page' },
            h('div', { className: 'page-heading' }, h('div', null, h('span', { className: 'eyebrow' }, t('nav.overview')), h('h1', null, t('transactions.title')), h('p', null, t('transactions.subtitle'))), h('span', { className: 'period-button' }, t(isOwner ? 'dashboard.period' : 'dashboard.today'))),
            h('section', { className: 'transaction-totals' },
                h(Card, { className: 'transaction-total-card' }, h('span', null, t('dashboard.income')), h('strong', { className: 'amount-income' }, formatCurrency(totals.ingresos))),
                h(Card, { className: 'transaction-total-card' }, h('span', null, t('dashboard.expenses')), h('strong', { className: 'amount-expense' }, formatCurrency(totals.egresos))),
                h(Card, { className: 'transaction-total-card' }, h('span', null, t('dashboard.balance')), h('strong', null, formatCurrency(totals.saldo)))),
            h('div', { className: 'transactions-layout' },
                h(Card, { className: 'transaction-form-card' },
                    h('div', { className: 'section-heading' }, h('div', null, h('h2', null, t('transactions.newTitle')), h('p', null, t('transactions.formSubtitle')))),
                    h('div', { className: 'transaction-type-toggle', role: 'group', 'aria-label': t('transactions.type') },
                        h('button', { type: 'button', className: type === 'ingreso' ? 'type-toggle-active type-toggle-income' : '', onClick: () => { setType('ingreso'); const category = categories.find((item) => item.tipo === 'ingreso');
                                setCategoryId(category ? String(category.id) : '') }, 'aria-pressed': type === 'ingreso' }, t('dashboard.income')),
                        h('button', { type: 'button', className: type === 'egreso' ? 'type-toggle-active type-toggle-expense' : '', onClick: () => { setType('egreso'); const category = categories.find((item) => item.tipo === 'egreso');
                                setCategoryId(category ? String(category.id) : '') }, 'aria-pressed': type === 'egreso' }, t('dashboard.expenses'))),
                    h('form', { className: 'transaction-form', onSubmit: handleSubmit },
                        h('label', { className: 'field-label', htmlFor: 'transaction-amount' }, t('transactions.amount')),
                        h('div', { className: 'amount-input-wrap' }, h('span', null, '$'), h('input', { className: 'text-input', id: 'transaction-amount', name: 'monto', type: 'number', min: '0.01', step: '0.01', placeholder: '0.00', required: true })),
                        h('label', { className: 'field-label', htmlFor: 'transaction-category' }, t('transactions.category')),
                        h('select', { className: 'text-input', id: 'transaction-category', name: 'categoria_id', value: categoryId, onChange: (event) => setCategoryId(event.target.value), required: true }, ...visibleCategories.map((category) => h('option', { key: category.id, value: String(category.id) }, `${category.icono ? `${category.icono} ` : ''}${category.nombre_mostrado}`))),
                    h('label', { className: 'field-label', htmlFor: 'transaction-description' }, t('transactions.description')),
                    h('input', { className: 'text-input', id: 'transaction-description', name: 'descripcion', type: 'text', maxLength: 250, placeholder: t('transactions.descriptionPlaceholder') }),
                    h('div', { className: 'transaction-form-row' },
                        h('span', null, h('label', { className: 'field-label', htmlFor: 'transaction-date' }, t('transactions.date')), h('input', { className: 'text-input', id: 'transaction-date', name: 'fecha', type: 'date', defaultValue: fechaLocal(), disabled: !isOwner })),
                        h('span', null, h('label', { className: 'field-label', htmlFor: 'transaction-method' }, t('transactions.method')), h('select', { className: 'text-input', id: 'transaction-method', name: 'metodo_pago', defaultValue: 'efectivo' }, ...['efectivo', 'transferencia', 'tarjeta', 'otro'].map((method) => h('option', { key: method, value: method }, t(`transactions.methods.${method}`))))),
                    ),
                    error && h('div', { className: 'form-error', role: 'alert' }, h(CircleAlert, { size: 16 }), error),
                    saved && h('p', { className: 'transaction-saved', role: 'status' }, t('transactions.saved')),
                    h(Button, { className: 'transaction-submit', type: 'submit', disabled: isSaving || visibleCategories.length === 0 }, isSaving ? h(LoaderCircle, { size: 16, className: 'spin-icon' }) : h(Plus, { size: 16 }), t(isSaving ? 'transactions.saving' : 'transactions.save'))),
            ),
            h(Card, { className: 'transaction-list-card' },
                h('div', { className: 'section-heading transaction-list-heading' }, h('div', null, h('h2', null, t('transactions.listTitle')), h('p', null, t('transactions.listCount', { count: transactions.length }))),
                    h('label', { className: 'transaction-filter' }, h('span', { className: 'sr-only' }, t('transactions.filter')), h('select', { value: filter, onChange: (event) => setFilter(event.target.value) }, h('option', { value: 'todos' }, t('transactions.allTypes')), h('option', { value: 'ingreso' }, t('dashboard.income')), h('option', { value: 'egreso' }, t('dashboard.expenses'))))),
                error && !isLoading && h('div', { className: 'transaction-load-error', role: 'alert' }, h('span', null, error), h('button', { className: 'icon-button', title: t('transactions.retry'), 'aria-label': t('transactions.retry'), onClick: () => { setIsLoading(true); setError(''); setReloadKey((value) => value + 1) } }, h(RefreshCw, { size: 16 }))),
                isLoading ? h('div', { className: 'transaction-loading' }, h(LoaderCircle, { size: 20, className: 'spin-icon' }), t('common.loading')) :
                    rows.length ? h('div', { className: 'transaction-table-wrap' }, h('table', { className: 'transaction-table' }, h('thead', null, h('tr', null, h('th', null, ''), h('th', null, t('transactions.description')), h('th', null, t('transactions.date')), h('th', null, t('transactions.category')), h('th', null, t('transactions.method')), h('th', null, t('transactions.amount')))), h('tbody', null, rows))) :
                        h('div', { className: 'transaction-empty' }, h(RefreshCw, { size: 19 }), h('p', null, t('transactions.empty')))))
    )
}