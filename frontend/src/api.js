import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  }
})

// Add error handling
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 404) {
      console.error('Endpoint not found:', error.config.url)
    }
    return Promise.reject(error)
  }
)

export default api
