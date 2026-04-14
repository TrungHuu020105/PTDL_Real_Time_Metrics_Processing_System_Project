import axios from 'axios'

const normalizeBaseUrl = (url) => url.replace(/\/+$/, '')

// Detect server URL based on environment
const getServerURL = () => {
    // Preferred for production (Render static site -> Render backend)
    const explicitApiBaseUrl = import.meta.env.VITE_API_BASE_URL
    if (explicitApiBaseUrl) {
        const normalized = normalizeBaseUrl(explicitApiBaseUrl)
        console.log('[API] Using VITE_API_BASE_URL:', normalized)
        return normalized
    }

    // Fallback for local/LAN development
    const serverIP =
        import.meta.env.VITE_SERVER_IP || 'localhost'
    const serverPort =
        import.meta.env.VITE_SERVER_PORT || '8000'

    const url = `http://${serverIP}:${serverPort}`
    console.log('[API] Server URL:', url)
    return url
}

export const getWebSocketBaseUrl = () => {
    const explicitApiBaseUrl = import.meta.env.VITE_API_BASE_URL
    if (explicitApiBaseUrl) {
        const parsed = new URL(explicitApiBaseUrl)
        const wsProtocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsBase = `${wsProtocol}//${parsed.host}`
        console.log('[API] WebSocket base URL:', wsBase)
        return wsBase
    }

    const serverIP = import.meta.env.VITE_SERVER_IP || 'localhost'
    const serverPort = import.meta.env.VITE_SERVER_PORT || '8000'
    const wsBase = `ws://${serverIP}:${serverPort}`
    console.log('[API] WebSocket base URL:', wsBase)
    return wsBase
}

const api = axios.create({
    baseURL: getServerURL(),
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000 // 30 second timeout
})

// Add error handling
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 404) {
            console.error('Endpoint not found:', error.config.url)
        }
        console.error('[API] Error:', {
            message: error.message,
            code: error.code,
            url: error.config?.url
        })
        return Promise.reject(error)
    }
)

export default api