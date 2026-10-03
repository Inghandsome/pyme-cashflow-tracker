import { useTranslation } from 'react-i18next'

export default function useCurrency() {
    const { i18n } = useTranslation()
    const locale = i18n.resolvedLanguage === 'en' ? 'en-US' : 'es-MX'
    const formatter = new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: 'MXN',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })

    return (amount) => formatter.format(amount)
}