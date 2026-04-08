import { useState, useEffect } from 'react'
import { Server, Check, ShoppingCart, Zap, Cpu, Activity, X } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useDevices } from '../context/DeviceContext'
import api from '../api'

export default function ServerStore() {
  const { availableServers, myServers, fetchAvailableServers, subscribeToServer, loading } = useDevices()
  const [subscribing, setSubscribing] = useState({})
  const [localhostMetrics, setLocalhostMetrics] = useState({ cpu: null, memory: null })
  const [loadingMetrics, setLoadingMetrics] = useState(false)
  const [showChartModal, setShowChartModal] = useState(false)
  const [chartData, setChartData] = useState([])
  const [chartLoading, setChartLoading] = useState(false)
  const [cpuStats, setCpuStats] = useState({ average: 0, min: 0, max: 0 })
  const [memoryStats, setMemoryStats] = useState({ average: 0, min: 0, max: 0 })

  useEffect(() => {
    fetchAvailableServers()
  }, [])

  // Fetch localhost metrics every 5 seconds
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoadingMetrics(true)
        const response = await api.get('/api/metrics/latest')
        if (response.data) {
          setLocalhostMetrics({
            cpu: response.data.latest_cpu,
            memory: response.data.latest_memory
          })
        }
      } catch (err) {
        console.error('Failed to fetch metrics:', err)
      } finally {
        setLoadingMetrics(false)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000)
    return () => clearInterval(interval)
  }, [])

  // Fetch chart data for localhost (past 2 hours = 120 minutes)
  const handleOpenChart = async () => {
    setShowChartModal(true)
    setChartLoading(true)
    try {
      // Fetch both CPU and Memory history
      const [cpuRes, memoryRes] = await Promise.all([
        api.get('/api/metrics/history', { params: { metric_type: 'cpu', minutes: 120 } }),
        api.get('/api/metrics/history', { params: { metric_type: 'memory', minutes: 120 } })
      ])

      // Transform and merge data
      const cpuData = cpuRes.data.data || []
      const memoryData = memoryRes.data.data || []

      // Create map for quick lookup
      const cpuMap = {}
      cpuData.forEach(item => {
        const time = new Date(item.timestamp)
        const key = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        cpuMap[key] = item.value
      })

      const memoryMap = {}
      memoryData.forEach(item => {
        const time = new Date(item.timestamp)
        const key = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        memoryMap[key] = item.value
      })

      // Merge all timestamps and create chart data
      const allTimestamps = new Set([...Object.keys(cpuMap), ...Object.keys(memoryMap)])
      const mergedData = Array.from(allTimestamps)
        .sort()
        .map(time => ({
          time,
          cpu: cpuMap[time] || null,
          memory: memoryMap[time] || null
        }))

      // Calculate statistics for CPU
      const cpuValues = cpuData.map(d => d.value)
      if (cpuValues.length > 0) {
        const avgCpu = cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length
        setCpuStats({
          average: parseFloat(avgCpu.toFixed(2)),
          min: parseFloat(Math.min(...cpuValues).toFixed(2)),
          max: parseFloat(Math.max(...cpuValues).toFixed(2))
        })
      }

      // Calculate statistics for Memory
      const memoryValues = memoryData.map(d => d.value)
      if (memoryValues.length > 0) {
        const avgMemory = memoryValues.reduce((a, b) => a + b, 0) / memoryValues.length
        setMemoryStats({
          average: parseFloat(avgMemory.toFixed(2)),
          min: parseFloat(Math.min(...memoryValues).toFixed(2)),
          max: parseFloat(Math.max(...memoryValues).toFixed(2))
        })
      }

      setChartData(mergedData)
    } catch (err) {
      console.error('Failed to fetch chart data:', err)
      setChartData([])
      setCpuStats({ average: 0, min: 0, max: 0 })
      setMemoryStats({ average: 0, min: 0, max: 0 })
    } finally {
      setChartLoading(false)
    }
  }

  const handleCloseChart = () => {
    setShowChartModal(false)
    setChartData([])
    setCpuStats({ average: 0, min: 0, max: 0 })
    setMemoryStats({ average: 0, min: 0, max: 0 })
  }

  const isSubscribed = (serverId) => {
    return myServers.some(s => s.id === serverId)
  }

  const handleSubscribe = async (serverId) => {
    try {
      setSubscribing(prev => ({ ...prev, [serverId]: true }))
      await subscribeToServer(serverId)
      alert('Successfully subscribed!')
    } catch (err) {
      alert('Error: ' + err.message)
    } finally {
      setSubscribing(prev => ({ ...prev, [serverId]: false }))
    }
  }

  const getServerColor = (index) => {
    const colors = ['neon-cyan', 'neon-green', 'neon-purple', 'neon-orange']
    return colors[index % colors.length]
  }

  const ServerCard = ({ server, index }) => {
    const color = getServerColor(index)
    const subscribed = isSubscribed(server.id)

    return (
      <div className={`bg-dark-800 border border-${color}/30 rounded-xl p-6 hover:border-${color}/60 transition-all flex flex-col`}>
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className={`text-xl font-bold text-${color} mb-2`}>{server.name}</h3>
            <p className="text-gray-400 text-sm">{server.specs}</p>
          </div>
          {subscribed && (
            <span className="flex items-center gap-1 text-xs bg-green-500/20 text-green-400 px-3 py-1 rounded-full">
              <Check className="w-3 h-3" />
              Subscribed
            </span>
          )}
        </div>

        {/* Specs */}
        <div className="space-y-3 mb-6 flex-1">
          {server.cpu_cores && (
            <div className="flex items-center gap-3 p-3 bg-dark-900 rounded-lg">
              <Zap className="w-5 h-5 text-neon-yellow opacity-70" />
              <div>
                <p className="text-xs text-gray-500">CPU Cores</p>
                <p className="text-lg font-bold text-white">{server.cpu_cores}</p>
              </div>
            </div>
          )}

          {server.ram_gb && (
            <div className="flex items-center gap-3 p-3 bg-dark-900 rounded-lg">
              <Server className="w-5 h-5 text-neon-cyan opacity-70" />
              <div>
                <p className="text-xs text-gray-500">Memory</p>
                <p className="text-lg font-bold text-white">{server.ram_gb}GB RAM</p>
              </div>
            </div>
          )}

          {server.os_type && (
            <div className="flex items-center gap-3 p-3 bg-dark-900 rounded-lg">
              <Server className="w-5 h-5 text-neon-purple opacity-70" />
              <div>
                <p className="text-xs text-gray-500">Operating System</p>
                <p className="text-lg font-bold text-white">{server.os_type}</p>
              </div>
            </div>
          )}
        </div>

        {/* Pricing & Button */}
        <div className="border-t border-gray-700 pt-4">
          {server.price_per_hour ? (
            <div className="mb-4">
              <p className="text-sm text-gray-500 mb-1">Pricing</p>
              <p className="text-2xl font-bold text-white">
                ${server.price_per_hour}
                <span className="text-sm text-gray-400 font-normal">/hour</span>
              </p>
            </div>
          ) : (
            <div className="mb-4">
              <p className="text-sm text-gray-500 mb-1">Status</p>
              <p className={`text-lg font-bold text-${color}`}>Free to Monitor</p>
            </div>
          )}

          <button
            onClick={() => handleSubscribe(server.id)}
            disabled={subscribed || subscribing[server.id] || loading}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-all font-semibold ${
              subscribed
                ? 'bg-green-500/20 text-green-400 border border-green-500/40 cursor-not-allowed'
                : `bg-${color}/20 text-${color} border border-${color}/40 hover:border-${color} disabled:opacity-50`
            }`}
          >
            {subscribed ? (
              <>
                <Check className="w-5 h-5" />
                Already Subscribed
              </>
            ) : subscribing[server.id] ? (
              'Subscribing...'
            ) : (
              <>
                <ShoppingCart className="w-5 h-5" />
                Subscribe to Monitor
              </>
            )}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Server Store</h1>
        <p className="text-gray-400">Browse and subscribe to available servers for monitoring</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-6">
          <p className="text-gray-400 text-sm mb-2">Available Servers</p>
          <p className="text-3xl font-bold text-neon-cyan">{availableServers.length}</p>
        </div>
        <div className="bg-dark-800 border border-neon-green/20 rounded-xl p-6">
          <p className="text-gray-400 text-sm mb-2">My Subscriptions</p>
          <p className="text-3xl font-bold text-neon-green">{myServers.length}</p>
        </div>
        <div className="bg-dark-800 border border-neon-purple/20 rounded-xl p-6">
          <p className="text-gray-400 text-sm mb-2">Monthly Cost</p>
          <p className="text-3xl font-bold text-neon-purple">
            ${(myServers.reduce((sum, s) => sum + (s.price_per_hour || 0) * 730, 0)).toFixed(2)}
          </p>
        </div>
      </div>

      {/* Your Servers Section Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Your Servers</h2>
        <button
          onClick={() => alert('Admin can add servers through settings')}
          className="flex items-center gap-2 bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 hover:border-neon-cyan px-4 py-2 rounded-lg transition-all"
        >
          <span className="text-lg">+</span>
          Add Server
        </button>
      </div>

      {/* Localhost Server Card */}
      <div
        onClick={handleOpenChart}
        className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-6 hover:border-neon-cyan/60 hover:cursor-pointer transition-all hover:bg-dark-700"
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Server 1</h3>
            <p className="text-xs text-gray-500 font-mono">Source: localhost</p>
          </div>
          <span className="text-xs text-neon-cyan bg-neon-cyan/20 px-2 py-1 rounded">
            System Server
          </span>
        </div>

        {/* Real-time Metrics Display */}
        <div className="bg-dark-900/50 rounded-lg p-4 mb-4 border border-neon-cyan/20 space-y-3">
          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-gray-400">CPU Usage</p>
              <span className="text-sm font-bold text-neon-yellow">
                {localhostMetrics.cpu !== null ? `${localhostMetrics.cpu.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            <div className="w-full bg-dark-800 rounded-full h-1.5">
              <div
                className="bg-neon-yellow h-1.5 rounded-full transition-all"
                style={{ width: `${localhostMetrics.cpu || 0}%` }}
              ></div>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-gray-400">Memory Usage</p>
              <span className="text-sm font-bold text-neon-cyan">
                {localhostMetrics.memory !== null ? `${localhostMetrics.memory.toFixed(1)}%` : 'N/A'}
              </span>
            </div>
            <div className="w-full bg-dark-800 rounded-full h-1.5">
              <div
                className="bg-neon-cyan h-1.5 rounded-full transition-all"
                style={{ width: `${localhostMetrics.memory || 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
          <span className="text-xs text-green-400">Active</span>
        </div>
      </div>

      {/* Servers Grid */}
      {loading ? (
        <div className="text-center py-16">
          <p className="text-gray-400">Loading servers...</p>
        </div>
      ) : availableServers.length === 0 ? (
        <div className="text-center py-16">
          <Server className="w-16 h-16 text-gray-600 mx-auto mb-4 opacity-50" />
          <h3 className="text-xl font-semibold text-white mb-2">No Servers Available</h3>
          <p className="text-gray-400">Contact admin to add servers</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {availableServers.map((server, idx) => (
            <ServerCard key={server.id} server={server} index={idx} />
          ))}
        </div>
      )}

      {/* Chart Modal */}
      {showChartModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8 max-w-4xl w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold text-white mb-1">Server 1</h3>
                <p className="text-sm text-gray-400">Last 2 hours of system metrics</p>
              </div>
              <button
                onClick={() => handleCloseChart()}
                className="p-2 hover:bg-dark-700 rounded-lg transition-all"
              >
                <X className="w-6 h-6 text-gray-400" />
              </button>
            </div>

            {chartLoading ? (
              <div className="flex items-center justify-center h-96">
                <p className="text-gray-400">Loading chart data...</p>
              </div>
            ) : chartData.length > 0 ? (
              <div className="space-y-6">
                {/* CPU Statistics */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-dark-900/50 border border-neon-yellow/30 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">CPU Average</p>
                    <p className="text-2xl font-bold text-neon-yellow">
                      {cpuStats.average}
                      <span className="text-sm text-gray-400 ml-1">%</span>
                    </p>
                  </div>
                  <div className="bg-dark-900/50 border border-neon-green/30 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">CPU Minimum</p>
                    <p className="text-2xl font-bold text-neon-green">
                      {cpuStats.min}
                      <span className="text-sm text-gray-400 ml-1">%</span>
                    </p>
                  </div>
                  <div className="bg-dark-900/50 border border-neon-orange/30 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">CPU Maximum</p>
                    <p className="text-2xl font-bold text-neon-orange">
                      {cpuStats.max}
                      <span className="text-sm text-gray-400 ml-1">%</span>
                    </p>
                  </div>
                </div>

                {/* Memory Statistics */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-dark-900/50 border border-neon-cyan/30 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">Memory Average</p>
                    <p className="text-2xl font-bold text-neon-cyan">
                      {memoryStats.average}
                      <span className="text-sm text-gray-400 ml-1">%</span>
                    </p>
                  </div>
                  <div className="bg-dark-900/50 border border-neon-green/30 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">Memory Minimum</p>
                    <p className="text-2xl font-bold text-neon-green">
                      {memoryStats.min}
                      <span className="text-sm text-gray-400 ml-1">%</span>
                    </p>
                  </div>
                  <div className="bg-dark-900/50 border border-neon-orange/30 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">Memory Maximum</p>
                    <p className="text-2xl font-bold text-neon-orange">
                      {memoryStats.max}
                      <span className="text-sm text-gray-400 ml-1">%</span>
                    </p>
                  </div>
                </div>

                {/* Chart */}
                <div className="bg-dark-900/50 rounded-lg p-6 border border-gray-700">
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="time"
                        stroke="#9CA3AF"
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis
                        stroke="#9CA3AF"
                        tick={{ fontSize: 12 }}
                        label={{ value: '%', angle: -90, position: 'insideLeft' }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1a1a2e',
                          border: '1px solid #00d4ff',
                          borderRadius: '8px'
                        }}
                        labelStyle={{ color: '#fff' }}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="cpu"
                        stroke="#ffd700"
                        dot={false}
                        strokeWidth={2}
                        name="CPU %"
                      />
                      <Line
                        type="monotone"
                        dataKey="memory"
                        stroke="#00d4ff"
                        dot={false}
                        strokeWidth={2}
                        name="Memory %"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-96">
                <p className="text-gray-400">No data available for this period</p>
              </div>
            )}

            <div className="flex gap-3 pt-6">
              <button
                onClick={() => handleCloseChart()}
                className="flex-1 px-4 py-2 bg-gray-700/20 text-gray-300 rounded hover:bg-gray-700/40 transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      {myServers.length > 0 && (
        <div className="mt-16 border-t border-gray-700 pt-8">
          <h2 className="text-2xl font-bold text-white mb-6">Your Active Subscriptions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {myServers.map((server) => (
              <div key={server.id} className="bg-green-500/10 border border-green-500/30 rounded-xl p-6">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">{server.name}</h3>
                  <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Active</span>
                </div>
                <p className="text-gray-400 text-sm mb-4">{server.specs}</p>
                <p className="text-sm text-gray-500">
                  Subscribed since: {new Date(server.subscribed_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
