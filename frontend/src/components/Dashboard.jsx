import { useState, useEffect } from 'react'
import { RefreshCw, AlertTriangle } from 'lucide-react'
import GaugeChart from './GaugeChart'
import MetricCard from './MetricCard'
import api from '../api'

export default function Dashboard() {
  const [data, setData] = useState({
    latest: {},
    summary: {},
    latestIoT: {}
  })
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [hasData, setHasData] = useState(true)

  const fetchData = async () => {
    try {
      setLoading(true)
      const [latestRes, summaryRes, iotRes] = await Promise.all([
        api.get('/api/metrics/latest'),
        api.get('/api/metrics/summary?minutes=1'),
        api.get('/api/metrics/history?metric_type=temperature&minutes=120')
      ])

      // Check if we have data
      if (latestRes.data && latestRes.data.latest_cpu !== null) {
        setHasData(true)
        setData({
          latest: latestRes.data,
          summary: summaryRes.data,
          latestIoT: iotRes.data?.data?.[0] || {}
        })
      } else {
        setHasData(false)
      }
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Failed to fetch data:', error)
      setHasData(false)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 1000) // Auto-refresh
    return () => clearInterval(interval)
  }, [])

  const formatTime = (date) => {
    return date.toLocaleTimeString('vi-VN')
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Real-Time Metrics Dashboard</h1>
          <p className="text-gray-400 mt-2">Live system performance monitoring</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-gray-400">Last updated</p>
            <p className="text-lg text-neon-cyan font-mono">{formatTime(lastUpdate)}</p>
          </div>
          <button
            onClick={fetchData}
            className="p-3 bg-dark-800 border border-neon-cyan/30 rounded-lg hover:border-neon-cyan transition-all"
          >
            <RefreshCw className={`w-5 h-5 text-neon-cyan ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Status Warning */}
      {!hasData ? (
        <div className="p-6 bg-dark-800 border border-neon-yellow/40 rounded-lg flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-neon-yellow mt-1 flex-shrink-0" />
          <div>
            <h3 className="text-neon-yellow font-semibold">⚠️ Warning — No Recent Data</h3>
            <p className="text-gray-400 text-sm mt-1">
              Generate sample data by running: <code className="bg-dark-700 px-2 py-1 rounded">python generate_iot_data.py</code>
            </p>
          </div>
        </div>
      ) : null}

      {/* Gauge Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GaugeChart
          title="CURRENT CPU"
          value={data.latest?.latest_cpu || 0}
          unit="%"
          color="neon-cyan"
          max={100}
        />
        <GaugeChart
          title="CURRENT MEMORY"
          value={data.latest?.latest_memory || 0}
          unit="%"
          color="neon-purple"
          max={100}
        />
        <div className="card-border card-hover p-6 bg-dark-800 flex flex-col justify-center">
          <h3 className="text-gray-400 text-sm mb-4">SYSTEM STATUS</h3>
          <div className="space-y-3">
            {hasData ? (
              <>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-green-400 text-sm">System Active</span>
                </div>
                <div className="text-2xl text-green-400 font-bold">Healthy</div>
              </>
            ) : (
              <>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-neon-yellow rounded-full animate-pulse"></div>
                  <span className="text-neon-yellow text-sm">Waiting for data</span>
                </div>
                <div className="text-2xl text-neon-yellow font-bold">Standby</div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Alerts & Anomalies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card-border card-hover p-6 bg-dark-800">
          <h3 className="text-gray-400 text-sm mb-4">Alerts & Anomalies</h3>
          <p className="text-gray-500 text-sm">Planned for next phase</p>
        </div>
        <div className="card-border card-hover p-6 bg-dark-800">
          <h3 className="text-gray-400 text-sm mb-4">Recommendations</h3>
          <p className="text-gray-500 text-sm">System performing optimally</p>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <MetricCard
          title="CPU"
          value={data.latest?.latest_cpu || 0}
          unit="%"
          icon="Cpu"
          color="neon-cyan"
        />
        <MetricCard
          title="MEMORY"
          value={data.latest?.latest_memory || 0}
          unit="%"
          icon="Zap"
          color="neon-purple"
        />
        <MetricCard
          title="REQUESTS"
          value={data.latest?.latest_request_count || 0}
          unit=""
          icon="Activity"
          color="neon-green"
        />
        <MetricCard
          title="AVG CPU (1M)"
          value={data.summary?.avg_cpu_1m || 0}
          unit="%"
          icon="TrendingUp"
          color="neon-cyan"
        />
        <MetricCard
          title="AVG MEM (1M)"
          value={data.summary?.avg_memory_1m || 0}
          unit="%"
          icon="BarChart3"
          color="neon-purple"
        />
        <MetricCard
          title="TOTAL REQ (1M)"
          value={data.summary?.total_request_count_1m || 0}
          unit=""
          icon="Wifi"
          color="neon-green"
        />
      </div>

      {/* IoT Quick View */}
      {data.latestIoT && data.latestIoT.value !== undefined && (
        <div className="card-border card-hover p-6 bg-dark-800">
          <h3 className="text-gray-400 text-sm mb-4">📡 Latest IoT Sensor Reading</h3>
          <div className="text-2xl text-neon-green font-bold">
            {data.latestIoT?.value || 'N/A'}°C
          </div>
          <p className="text-gray-500 text-sm mt-2">Temperature from {data.latestIoT?.source || 'unknown'}</p>
        </div>
      )}
    </div>
  )
}
