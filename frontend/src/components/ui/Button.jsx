import { createElement as h } from 'react'

export default function Button({ children, variant = 'primary', className = '', ...props }) {
    return h('button', { className: `button button-${variant} ${className}`, ...props }, children)
}