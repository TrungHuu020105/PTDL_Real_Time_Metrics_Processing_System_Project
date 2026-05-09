import { useState, useEffect } from 'react'
import { AlertTriangle, AlertCircle, CheckCircle, Sparkles, X } from 'lucide-react'
import api from '../api'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [lastUpdated, setLastUpdated] = useState(null)
  const [explainingAlertId, setExplainingAlertId] = useState(null)
  const [aiExplainModal, setAiExplainModal] = useState({ open: false, title: '', content: '', meta: null })

  const formatMetricName = (metric) => {
    const names = {
      cpu: 'CPU Usage',
      memory: 'Memory Usage',
      temperature: 'Temperature',
      humidity: 'Humidity',
      soil_moisture: 'Soil Moisture',
      light_intensity: 'Light Intensity',
      pressure: 'Pressure',
    }
    return names[metric] || metric
  }

  const getMetricUnit = (metric) => {
    const units = {
      cpu: '%',
      memory: '%',
      temperature: '°C',
      humidity: '%',
      soil_moisture: '%',
      light_intensity: 'lux',
      pressure: 'hPa',
    }
    return units[metric] || ''
  }

  const formatVNDateTime = (value) => {
    if (!value) return 'N/A'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return String(value)
    return date.toLocaleString('vi-VN', { hour12: false })
  }

  const formatVNTime = (value) => {
    const date = value instanceof Date ? value : new Date(value)
    if (Number.isNaN(date.getTime())) return 'N/A'
    return date.toLocaleTimeString('vi-VN', { hour12: false })
  }

  const fetchAlerts = async () => {
    try {
      const response = await api.get('/api/alerts/recent?hours=24&limit=100')
      setAlerts(response.data?.alerts || [])
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Error fetching alerts:', error)
    }
  }

  useEffect(() => {
    fetchAlerts()
    const interval = setInterval(fetchAlerts, 2000)
    return () => clearInterval(interval)
  }, [])

  const getAlertIcon = (status) => {
    switch (status) {
      case 'critical':
        return <AlertTriangle className="w-6 h-6 flex-shrink-0" />
      case 'warning':
        return <AlertCircle className="w-6 h-6 flex-shrink-0" />
      default:
        return <CheckCircle className="w-6 h-6 flex-shrink-0" />
    }
  }

  const getAlertColor = (status) => {
    switch (status) {
      case 'critical':
        return 'text-neon-red'
      case 'warning':
        return 'text-neon-yellow'
      default:
        return 'text-neon-green'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'critical':
        return '#ff3333'
      case 'warning':
        return '#ffcc00'
      default:
        return '#00ff88'
    }
  }

  const explainWithAI = async (alert) => {
    try {
      setExplainingAlertId(alert.id)
      const response = await api.get(`/api/alerts/${alert.id}/explain-ai`)
      const apiSuccess = Boolean(response?.data?.success)
      const apiMessage = response?.data?.message || ''
      const apiErrorCode = response?.data?.error_code || null
      const apiErrorDetail = response?.data?.error_detail || null
      const apiRetryAfter = response?.data?.retry_after_seconds
      const shortMessage = apiMessage?.split('Chi tiet ky thuat:')[0]?.trim() || apiMessage
      const explanation = apiSuccess
        ? (response?.data?.explanation || 'Không có nội dung giải thích.')
        : `Không thể tạo giải thích AI: ${shortMessage || 'Lỗi không xác định từ backend.'}`
      const retryLine = !apiSuccess && apiRetryAfter
        ? `\n[Debug] retry_after_seconds: ${apiRetryAfter}`
        : ''
      const debugText = !apiSuccess
        ? `\n\n[Debug] error_code: ${apiErrorCode || 'N/A'}${retryLine}\n[Debug] error_detail: ${apiErrorDetail || 'N/A'}`
        : ''
      setAiExplainModal({
        open: true,
        title: `${formatMetricName(alert.metric_type)} - ${alert.status.toUpperCase()}`,
        content: `${explanation}${debugText}`,
        meta: response?.data?.context || null,
      })
    } catch (error) {
      const httpStatus = error?.response?.status
      const backendDetail = error?.response?.data?.detail
      setAiExplainModal({
        open: true,
        title: 'Giải thích bằng AI',
        content:
          `Không thể tạo giải thích AI: ${backendDetail || error.message}\n\n` +
          `[Debug] http_status: ${httpStatus || 'N/A'}\n` +
          `[Debug] backend_detail: ${backendDetail || 'N/A'}`,
        meta: null,
      })
    } finally {
      setExplainingAlertId(null)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Alerts & Anomalies</h1>
        <p className="text-gray-400 mt-2">
          System notifications and warnings
          {lastUpdated && (
            <span className="ml-4 text-xs text-gray-500">
              Last updated: {formatVNTime(lastUpdated)}
            </span>
          )}
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Critical Alerts</p>
          <p className="text-2xl font-bold text-neon-red">{alerts.filter((a) => a.status === 'critical').length}</p>
        </div>
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Warning Alerts</p>
          <p className="text-2xl font-bold text-neon-yellow">{alerts.filter((a) => a.status === 'warning').length}</p>
        </div>
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Total Alerts (24h)</p>
          <p className="text-2xl font-bold text-neon-cyan">{alerts.length}</p>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="card-border p-6 bg-dark-800">
          <div className="flex items-center gap-4">
            <CheckCircle className="w-8 h-8 text-neon-green flex-shrink-0" />
            <div>
              <h3 className="text-white font-semibold">All Systems Healthy</h3>
              <p className="text-gray-400 text-sm mt-1">No alerts in the last 24 hours</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="card-border card-hover p-6 bg-dark-800 flex items-start gap-4 border border-opacity-50"
              style={{ borderColor: getStatusColor(alert.status) }}
            >
              <div className={getAlertColor(alert.status)}>{getAlertIcon(alert.status)}</div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-semibold">{formatMetricName(alert.metric_type)}</h3>
                  <span className="px-3 py-1 rounded text-xs font-semibold text-dark-900" style={{ backgroundColor: getStatusColor(alert.status) }}>
                    {alert.status.toUpperCase()}
                  </span>
                </div>
                <p className="text-gray-400 text-sm mt-2">{alert.message}</p>
                <div className="flex items-center gap-4 mt-3">
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-gray-500">Current:</p>
                    <p className="text-lg font-bold text-white">
                      {alert.current_value}
                      <span className="text-xs text-gray-400 ml-1">{getMetricUnit(alert.metric_type)}</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-gray-500">Threshold:</p>
                    <p className="text-lg font-bold text-neon-yellow">
                      {alert.threshold}
                      <span className="text-xs text-gray-400 ml-1">{getMetricUnit(alert.metric_type)}</span>
                    </p>
                  </div>
                  <p className="text-xs text-gray-500 ml-auto">{formatVNDateTime(alert.created_at)}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => explainWithAI(alert)}
                    disabled={explainingAlertId === alert.id}
                    className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-neon-cyan/15 border border-neon-cyan/40 text-neon-cyan hover:bg-neon-cyan/25 disabled:opacity-50 transition-all text-sm"
                  >
                    <Sparkles className="w-4 h-4" />
                    {explainingAlertId === alert.id ? 'Đang phân tích...' : 'Giải thích bằng AI'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {aiExplainModal.open && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 border border-neon-cyan/30 rounded-xl w-full max-w-4xl p-6 md:p-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-2xl md:text-3xl font-bold text-neon-cyan">{aiExplainModal.title}</h3>
              <button onClick={() => setAiExplainModal({ open: false, title: '', content: '', meta: null })} className="text-gray-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>
            {aiExplainModal.meta && (
              <p className="text-sm md:text-base text-gray-400 mb-4">
                Weather context: {aiExplainModal.meta.has_weather ? 'available' : 'not available'} | Environment: {aiExplainModal.meta.environment_type || 'unknown'}
              </p>
            )}
            <pre className="whitespace-pre-wrap text-gray-200 leading-8 font-sans text-base md:text-lg bg-dark-900/60 rounded-lg p-5 md:p-6 border border-gray-700 max-h-[60vh] overflow-y-auto">
              {aiExplainModal.content}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
