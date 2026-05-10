import axios from 'axios'

const coreIP = import.meta.env.VITE_CORE_SERVER_IP || import.meta.env.VITE_SERVER_IP || 'localhost'
const corePort = import.meta.env.VITE_CORE_SERVER_PORT || import.meta.env.VITE_SERVER_PORT || '8000'
const iotIP = import.meta.env.VITE_IOT_SERVER_IP || coreIP
const iotPort = import.meta.env.VITE_IOT_SERVER_PORT || (iotIP === 'localhost' ? '8100' : corePort)
const coreBaseURL = `http://${coreIP}:${corePort}`
const iotBaseURL = `http://${iotIP}:${iotPort}`

const iotApiPrefixes = [
    '/api/health',
    '/api/iot-devices',
    '/api/metrics',
    '/api/alerts',
    '/api/admin/iot-devices',
]

const isIotApi = (url = '') => iotApiPrefixes.some(prefix => url.startsWith(prefix))

const api = axios.create({
    baseURL: coreBaseURL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000 // 30 second timeout
})

api.interceptors.request.use((config) => {
    const targetBase = isIotApi(config.url || '') ? iotBaseURL : coreBaseURL
    config.baseURL = targetBase
    return config
})

console.log('[API] Core Base URL:', coreBaseURL)
console.log('[API] IoT Base URL:', iotBaseURL)

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
