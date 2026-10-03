import { createElement as h } from 'react'

export default function Card({ children, className = '' }) {
    return h('section', { className: `surface-card ${className}` }, children)
}