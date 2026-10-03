import { createElement as h, useState } from 'react'
import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'

export default function Layout() {
    const [menuOpen, setMenuOpen] = useState(false)
    return h('div', { className: 'app-shell' },
        h(Sidebar, { isOpen: menuOpen, onClose: () => setMenuOpen(false) }),
        h('div', { className: 'workspace-shell' }, h(Header, { onMenuClick: () => setMenuOpen(true) }), h('main', { className: 'page-content' }, h(Outlet))))
}