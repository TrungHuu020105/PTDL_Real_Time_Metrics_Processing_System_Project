import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../api'

export default function CPUMetrics() {
  const [data, setData] = useState([])
  const [stats, setStats] = useState({ avg: 0, max: 0, min: 0 })
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    try {
      const response = await api.get('/api/metrics/history?metric_type=cpu&minutes=60')
      const metrics = response.data.data || []

      // Group by timestamp and calculate average
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

      // Transform data
      const chartData = Object.entries(grouped).map(([time, values]) => ({
        time,
        cpu: (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2)
      }))

      // Calculate stats
      const allValues = metrics.map(m => m.value)
      setStats({
        avg: (allValues.reduce((a, b) => a + b, 0) / allValues.length).toFixed(2),
        max: Math.max(...allValues).toFixed(2),
        min: Math.min(...allValues).toFixed(2)
      })

      setData(chartData)
    } catch (error) {
      console.error('Failed to fetch CPU metrics:', error)
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
        <h1 className="text-3xl font-bold text-white">CPU Metrics</h1>
        <p className="text-gray-400 mt-2">CPU usage over the last 60 minutes</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Average</p>
          <p className="text-2xl font-bold text-neon-cyan mt-2">{stats.avg}%</p>
        </div>
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Peak</p>
          <p className="text-2xl font-bold text-neon-yellow mt-2">{stats.max}%</p>
        </div>
        <div className="card-border p-4 bg-dark-800">
          <p className="text-gray-400 text-sm">Low</p>
          <p className="text-2xl font-bold text-neon-green mt-2">{stats.min}%</p>
        </div>
      </div>

      {/* Chart */}
      <div className="card-border p-6 bg-dark-800">
        <h3 className="text-gray-300 font-semibold mb-4">CPU Usage Timeline</h3>
        {loading ? (
          <p className="text-gray-400 py-12 text-center">Loading...</p>
        ) : data.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00f0ff" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,240,255,0.1)" vertical={false} />
              <XAxis dataKey="time" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1f3a',
                  border: '1px solid #00f0ff',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                cursor={{ stroke: '#00f0ff', strokeWidth: 2 }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line
                type="monotone"
                dataKey="cpu"
                stroke="#00f0ff"
                dot={false}
                strokeWidth={2.5}
                isAnimationActive={false}
                fill="url(#cpuGradient)"
                name="CPU Usage (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-400 py-12 text-center">No data available</p>
        )}
      </div>
    </div>
  )
}
