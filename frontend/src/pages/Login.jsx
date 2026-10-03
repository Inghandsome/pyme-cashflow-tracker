import { createElement as h, useState } from 'react'
import { AlertCircle, ArrowRight, Armchair, Eye, EyeOff, LoaderCircle, ShieldCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import Button from '../components/ui/Button'
import SelectorIdioma from '../components/layout/SelectorIdioma'
import useAuth from '../hooks/useAuth'
import { ApiError } from '../services/api'

export default function Login() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { signIn } = useAuth()
    const [showPassword, setShowPassword] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [loginError, setLoginError] = useState('')
    const handleSubmit = async(event) => {
        event.preventDefault();
        const formData = new FormData(event.currentTarget)
        setIsSubmitting(true)
        setLoginError('')
        try {
            await signIn(String(formData.get('email') || ''), String(formData.get('password') || ''))
            navigate('/dashboard')
        } catch (error) {
            setLoginError(error instanceof ApiError ? error.message : t('common.connectionError'))
        } finally {
            setIsSubmitting(false)
        }
    }

    return h('main', { className: 'login-page' },
        h('section', { className: 'login-visual', 'aria-label': t('brand.descriptor') },
            h('div', { className: 'login-photo' }), h('div', { className: 'photo-grain' }),
            h('div', { className: 'visual-brand' }, h('span', { className: 'brand-mark brand-mark-light' }, h(Armchair, { size: 21 })), h('span', null, h('strong', null, t('brand.name')), h('small', null, t('brand.descriptor')))),
            h('div', { className: 'visual-caption' }, h('span', { className: 'eyebrow eyebrow-light' }, t('login.eyebrow')), h('h1', null, t('login.title')), h('p', null, t('login.description')), h('span', { className: 'caption-rule' }), h('small', null, t('login.copyright'))),
            h('div', { className: 'visual-credit' }, h('span', null, '01 / 03'), h('span', { className: 'credit-line' }), h('span', null, 'HECHO A MANO, CON PROPÓSITO'))),
        h('section', { className: 'login-panel' },
            h('div', { className: 'login-panel-top' }, h('span', { className: 'mobile-brand' }, h(Armchair, { size: 20 }), t('brand.name')), h(SelectorIdioma)),
            h('div', { className: 'login-form-wrap' },
                h('span', { className: 'eyebrow' }, t('login.eyebrow')), h('h2', null, t('login.welcome')), h('p', { className: 'login-subtitle' }, t('login.subtitle')),
                loginError && h('div', { className: 'form-error', role: 'alert' }, h(AlertCircle, { size: 16 }), loginError),
                h('form', { onSubmit: handleSubmit },
                    h('label', { className: 'field-label', htmlFor: 'email' }, t('login.email')),
                    h('input', { className: 'text-input', id: 'email', name: 'email', type: 'email', placeholder: t('login.emailPlaceholder'), autoComplete: 'email', required: true }),
                    h('div', { className: 'password-label-row' }, h('label', { className: 'field-label', htmlFor: 'password' }, t('login.password')), h('button', { type: 'button', className: 'text-link' }, t('login.forgotPassword'))),
                    h('div', { className: 'password-field' }, h('input', { className: 'text-input', id: 'password', name: 'password', type: showPassword ? 'text' : 'password', placeholder: '••••••••', autoComplete: 'current-password', required: true }), h('button', { type: 'button', className: 'password-toggle', onClick: () => setShowPassword((visible) => !visible), 'aria-label': t('login.password') }, h(showPassword ? EyeOff : Eye, { size: 17 }))),
                    h('div', { className: 'login-role-note' }, h(ShieldCheck, { size: 15 }), h('span', null, t('login.accountRole'))),
                    h(Button, { type: 'submit', className: 'login-submit', disabled: isSubmitting }, isSubmitting ? t('login.submitting') : t('login.submit'), h(isSubmitting ? LoaderCircle : ArrowRight, { size: 17, className: isSubmitting ? 'spin-icon' : '' }))),
                h('div', { className: 'demo-note' }, h(ShieldCheck, { size: 15 }), h('span', null, t('login.demoNote')))),
            h('footer', { className: 'login-footer' }, h('span', null, `© 2026 ${t('brand.name')}`), h('span', null, t('common.demoUser'))))
    )
}