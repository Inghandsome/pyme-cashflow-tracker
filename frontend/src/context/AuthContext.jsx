import { createElement as h, useEffect, useMemo, useState } from 'react'
import AuthContext from './authContextValue'
import { apiRequest } from '../services/api'

const TOKEN_KEY = 'roble-access-token'

function normalizeUser(apiUser) {
    return {
        id: apiUser.id,
        name: apiUser.nombre,
        email: apiUser.email,
        role: apiUser.rol === 'dueno' ? 'owner' : 'cashier',
        language: apiUser.idioma,
        company: apiUser.empresa,
    }
}

function storedLanguage() {
    return window.localStorage.getItem('roble-language') || 'es'
}

export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => window.localStorage.getItem(TOKEN_KEY))
    const [user, setUser] = useState(null)
    const [isLoading, setIsLoading] = useState(() => Boolean(window.localStorage.getItem(TOKEN_KEY)))

    useEffect(() => {
        if (!token) return undefined
        let active = true
        apiRequest('/auth/perfil', { token, language: storedLanguage() })
            .then((apiUser) => { if (active) setUser(normalizeUser(apiUser)) })
            .catch(() => {
                if (!active) return
                window.localStorage.removeItem(TOKEN_KEY)
                setToken(null)
                setUser(null)
            })
            .finally(() => { if (active) setIsLoading(false) })
        return () => { active = false }
    }, [token])

    async function signIn(email, password) {
        const session = await apiRequest('/auth/login', {
            method: 'POST',
            body: { email, password },
            language: storedLanguage(),
        })
        window.localStorage.setItem(TOKEN_KEY, session.token)
        setUser(normalizeUser(session.usuario))
        setIsLoading(true)
        setToken(session.token)
    }

    function signOut() {
        window.localStorage.removeItem(TOKEN_KEY)
        setToken(null)
        setUser(null)
        setIsLoading(false)
    }

    const value = useMemo(() => ({
        user,
        token,
        isLoading,
        signIn,
        signOut,
    }), [user, token, isLoading])
    return h(AuthContext.Provider, { value }, children)
}