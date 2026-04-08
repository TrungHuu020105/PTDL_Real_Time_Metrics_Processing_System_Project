import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { AlertCircle, Lock } from 'lucide-react'
import api from '../api'
import { checkMetricAlert } from '../utils/alertUtils'
import { saveAlert } from '../utils/alertService'

export default function IoTMetrics() {
  const [metricType, setMetricType] = useState('temperature')
  const [data, setData] = useState([])
  const [current, setCurrent] = useState(0)
  const [stats, setStats] = useState({ avg: 0, max: 0, min: 0 })
  const [alert, setAlert] = useState(null)
  const [loading, setLoading] = useState(true)
  const [accessDenied, setAccessDenied] = useState(false)
  const lastAlertRef = useRef(null)

  const iotMetrics = {
    temperature: { label: '🌡️ Temperature', unit: '°C', color: '#ff6b6b', min: 15, max: 35 },
    humidity: { label: '💧 Humidity', unit: '%', color: '#4ecdc4', min: 30, max: 90 },
    soil_moisture: { label: '🌱 Soil Moisture', unit: '%', color: '#95e1d3', min: 0, max: 100 },
    light_intensity: { label: '💡 Light Intensity', unit: 'lux', color: '#ffe66d', min: 0, max: 1000 },
    pressure: { label: '🌊 Pressure', unit: 'hPa', color: '#a8dadc', min: 900, max: 1100 },
  }

  const fetchData = async () => {
    try {
      setAccessDenied(false)
      const [historyRes] = await Promise.all([
        api.get(`/api/metrics/history?metric_type=${metricType}&minutes=120`)
      ])
      const metrics = historyRes.data.data || []
      
      // Set current to latest value
      if (metrics.length > 0) {
        const latestValue = metrics[metrics.length - 1].value
        setCurrent(latestValue)
        // Check for alerts
        const newAlert = checkMetricAlert(metricType, latestValue)
        setAlert(newAlert)

        // Save alert if status is not normal and hasn't been saved recently
        if (newAlert.status !== 'normal') {
          const now = Date.now()
          const lastAlertTime = lastAlertRef.current?.timestamp
          const timeSinceLastAlert = lastAlertTime ? now - lastAlertTime : Infinity

          // Save alert if status changed or 5 minutes have passed
          if (!lastAlertRef.current || lastAlertRef.current.status !== newAlert.status || timeSinceLastAlert > 5 * 60 * 1000) {
            const thresholdMap = {
              temperature: { warning: 30, critical: 35 },
              humidity: { warning: 75, critical: 90 },
              soil_moisture: { warning: 30, critical: 20 },
              light_intensity: { warning: 500, critical: 100 },
              pressure: { warning: 1020, critical: 1050 }
            }
            const threshold = thresholdMap[metricType][newAlert.status]
            
            saveAlert(metricType, newAlert.status, latestValue, threshold, newAlert.fullMessage)
            lastAlertRef.current = { status: newAlert.status, timestamp: now }
          }
        }
      }

      const grouped = {}
      metrics.forEach(metric => {
        const time = new Date(metric.timestamp).toLocaleTimeString('vi-VN', {
          hour: '2-digit',
          minute: '2-digit'
        })
        if (!grouped[time]) {
          grouped[time] = []
        }
        grouped[time].push(metric.value)
      })

      const chartData = Object.entries(grouped).map(([time, values]) => ({
        time,
        value: (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2)
      }))

      const allValues = metrics.map(m => m.value)
      if (allValues.length > 0) {
        setStats({
          avg: (allValues.reduce((a, b) => a + b, 0) / allValues.length).toFixed(2),
          max: Math.max(...allValues).toFixed(2),
          min: Math.min(...allValues).toFixed(2)
        })
      }

      setData(chartData)
      setLoading(false)
    } catch (error) {
      if (error.response?.status === 403) {
        setAccessDenied(true)
      }
      console.error('Failed to fetch IoT metrics:', error)
      setData([])
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [metricType])

  useEffect(() => {
    const interval = setInterval(fetchData, 3000)
    return () => clearInterval(interval)
  }, [metricType])

  const currentMetric = iotMetrics[metricType]

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">📡 IoT Sensor Metrics</h1>
        <p className="text-gray-400 mt-2">Real-time IoT sensor data monitoring</p>
      </div>

      {/* Access Denied Message */}
      {accessDenied && (
        <div className="card-border p-6 bg-red-500/10 border-red-500/30 flex items-center gap-4">
          <Lock className="w-6 h-6 text-red-400" />
          <div>
            <p className="text-red-400 font-semibold">No Access</p>
            <p className="text-red-300 text-sm mt-1">You don't have access to any IoT metrics. Please contact your administrator to request device access.</p>
          </div>
        </div>
      )}

      {/* Metric Type Selector */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {Object.entries(iotMetrics).map(([key, metric]) => (
          <button
            key={key}
            onClick={() => setMetricType(key)}
            className={`p-4 rounded-lg border transition-all ${
              metricType === key
                ? 'border-white bg-dark-700'
                : 'border-gray-600 hover:border-gray-400 bg-dark-800'
            }`}
          >
            <p className="text-sm">{metric.label}</p>
            <p className="text-xs text-gray-400 mt-1">{metric.unit}</p>
          </button>
        ))}
      </div>

      {/* Current Status */}
      <div 
        className="card-border p-6 bg-dark-700 border-2"
        style={{ borderColor: alert?.color }}
      >
        <div className="flex items-start justify-between">
          <div>
            <p className="text-gray-400 text-sm mb-2">CURRENT STATUS</p>
            <div className="text-5xl font-bold neon-glow" style={{ color: alert?.color }}>
              {current}{currentMetric.unit}
            </div>
            <p className="text-gray-500 text-sm mt-2">Live {currentMetric.label}</p>
          </div>
          {alert && alert.status !== 'normal' && (
            <div className="text-right">
              <span
                className="px-3 py-1 rounded text-xs font-semibold text-dark-900"
                style={{ backgroundColor: alert.color }}
              >
                {alert.message}
              </span>
              <p className="text-xs mt-2 text-gray-500 max-w-xs">{alert.fullMessage}</p>
            </div>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Average</p>
          <p className="text-2xl font-bold mt-2" style={{ color: alert?.color }}>
            {stats.avg}{currentMetric.unit}
          </p>
        </div>
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Peak</p>
          <p className="text-2xl font-bold text-neon-yellow mt-2">{stats.max}{currentMetric.unit}</p>
        </div>
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Low</p>
          <p className="text-2xl font-bold text-neon-green mt-2">{stats.min}{currentMetric.unit}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="card-border p-6 bg-dark-800">
        <h3 className="text-gray-300 font-semibold mb-4">{currentMetric.label} Timeline</h3>
        {loading ? (
          <p className="text-gray-400 py-12 text-center">Loading...</p>
        ) : data.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="iotGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={currentMetric.color} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={currentMetric.color} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis dataKey="time" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1f3a',
                  border: `1px solid ${currentMetric.color}`,
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                cursor={{ stroke: currentMetric.color, strokeWidth: 2 }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line
                type="monotone"
                dataKey="value"
                stroke={currentMetric.color}
                dot={false}
                strokeWidth={2.5}
                isAnimationActive={false}
                fill="url(#iotGradient)"
                name={`${currentMetric.label} (${currentMetric.unit})`}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-400 py-12 text-center">
            No data available. Generate IoT data with: <code className="bg-dark-700 px-2 py-1 rounded text-xs">python generate_iot_data.py</code>
          </p>
        )}
      </div>

      {/* Reference Ranges */}
      <div className="card-border p-6 bg-dark-800">
        <h3 className="text-gray-300 font-semibold mb-4">📊 Sensor Reference Ranges</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(iotMetrics).map(([key, metric]) => (
            <div key={key} className="bg-dark-900 p-3 rounded">
              <p className="text-sm text-gray-400">{metric.label}</p>
              <p className="text-xs text-gray-500 mt-2">Range: {metric.min}-{metric.max} {metric.unit}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
