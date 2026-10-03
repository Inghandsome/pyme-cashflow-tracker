const API_BASE_URL = (
    import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

export class ApiError extends Error {
    constructor(message, status, code) {
        super(message)
        this.name = 'ApiError'
        this.status = status
        this.code = code
    }
}

export async function apiRequest(path, options = {}) {
    const language = options.language || window.localStorage.getItem('roble-language') || 'es'
    const headers = {
        Accept: 'application/json',
        'Accept-Language': language,
    }

    if (options.token) headers.Authorization = `Bearer ${options.token}`
    if (options.body !== undefined) headers['Content-Type'] = 'application/json'

    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: options.method || 'GET',
        headers,
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
    const envelope = await response.json().catch(() => null)

    if (!response.ok || (envelope && envelope.ok === false)) {
        const apiError = envelope && envelope.error ? envelope.error : {}
        throw new ApiError(apiError.mensaje || 'No fue posible completar la solicitud.', response.status, apiError.codigo)
    }

    return envelope ? envelope.datos : null
}