import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../api'

export default function RequestMetrics() {
  const [data, setData] = useState([])
  const [stats, setStats] = useState({ total: 0, avg: 0, max: 0 })
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    try {
      const response = await api.get('/api/metrics/history?metric_type=request_count&minutes=60')
      const metrics = response.data.data || []

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
        requests: Math.round(values.reduce((a, b) => a + b, 0) / values.length)
      }))

      const allValues = metrics.map(m => m.value)
      const total = allValues.reduce((a, b) => a + b, 0)
      
      setStats({
        total: Math.round(total),
        avg: (total / allValues.length).toFixed(0),
        max: Math.max(...allValues).toFixed(0)
      })

      setData(chartData)
    } catch (error) {
      console.error('Failed to fetch request metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Request Metrics</h1>
        <p className="text-gray-400 mt-2">Request count over the last 60 minutes</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Total</p>
          <p className="text-2xl font-bold text-neon-green mt-2">{stats.total}</p>
        </div>
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Average</p>
          <p className="text-2xl font-bold text-neon-green mt-2">{stats.avg}</p>
        </div>
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Peak</p>
          <p className="text-2xl font-bold text-neon-yellow mt-2">{stats.max}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="card-border p-6 bg-dark-800">
        <h3 className="text-gray-300 font-semibold mb-4">Request Count Timeline</h3>
        {loading ? (
          <p className="text-gray-400 py-12 text-center">Loading...</p>
        ) : data.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="requestGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00ff88" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#00ff88" stopOpacity={0.3}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,255,136,0.1)" vertical={false} />
              <XAxis dataKey="time" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1f3a',
                  border: '1px solid #00ff88',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                cursor={{ fill: 'rgba(0, 255, 136, 0.1)' }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Bar
                dataKey="requests"
                fill="url(#requestGradient)"
                radius={[4, 4, 0, 0]}
                name="Request Count"
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-400 py-12 text-center">No data available</p>
        )}
      </div>
    </div>
  )
}
