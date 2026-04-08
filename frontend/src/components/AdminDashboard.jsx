import { useState, useEffect } from 'react'
import { Server, Users, AlertCircle, Zap, TrendingUp, Thermometer } from 'lucide-react'
import api from '../api'

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    totalServers: 0,
    totalUsers: 0,
    pendingUsers: 0,
    totalAlerts: 0,
    totalRevenue: 0,
    totalIoTDevices: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const [serversRes, usersRes, alertsRes, iotDevicesRes] = await Promise.all([
        api.get('/api/servers').catch(() => ({ data: { servers: [] } })),
        api.get('/api/admin/users').catch(() => ({ data: { users: [] } })),
        api.get('/api/alerts').catch(() => ({ data: { alerts: [] } })),
        api.get('/api/admin/iot-devices').catch(() => ({ data: { devices: [] } }))
      ])

      const servers = serversRes.data.servers || []
      const users = usersRes.data.users || []
      const alerts = alertsRes.data.alerts || []
      const iotDevices = iotDevicesRes.data.devices || []

      // Calculate metrics
      const totalRevenue = servers.reduce((sum, s) => {
        const monthlyRevenue = (s.price_per_hour || 0) * 730 * (s.subscribers_count || 0)
        return sum + monthlyRevenue
      }, 0)

      setStats({
        totalServers: servers.length,
        totalUsers: users.length,
        pendingUsers: users.filter(u => !u.is_approved).length,
        totalAlerts: alerts.length,
        totalRevenue: totalRevenue,
        totalIoTDevices: iotDevices.length
      })
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    } finally {
      setLoading(false)
    }
  }

  const StatCard = ({ icon: Icon, label, value, color, unit = '' }) => (
    <div className={`bg-dark-800 border border-${color}/30 rounded-xl p-6 hover:border-${color}/60 transition-all hover:shadow-lg hover:shadow-${color}/20`}>
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 bg-${color}/20 rounded-lg`}>
          <Icon className={`w-6 h-6 text-${color}`} />
        </div>
      </div>
      <p className="text-gray-400 text-sm mb-2">{label}</p>
      <p className={`text-3xl font-bold text-${color}`}>
        {loading ? '-' : `${value}${unit}`}
      </p>
    </div>
  )

  return (
    <div className="min-h-screen bg-dark-900 p-8">
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-white mb-2">Admin Dashboard</h1>
        <p className="text-gray-400">System overview and key metrics</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard 
          icon={Server} 
          label="Total Servers" 
          value={stats.totalServers} 
          color="neon-cyan" 
        />
        <StatCard 
          icon={Users} 
          label="Total Users" 
          value={stats.totalUsers} 
          color="neon-purple" 
        />
        <StatCard 
          icon={AlertCircle} 
          label="Pending Users" 
          value={stats.pendingUsers} 
          color="neon-yellow" 
        />
        <StatCard 
          icon={AlertCircle} 
          label="Total Alerts" 
          value={stats.totalAlerts} 
          color="neon-orange" 
        />
        <StatCard 
          icon={TrendingUp} 
          label="Monthly Revenue" 
          value={stats.totalRevenue.toFixed(2)} 
          color="neon-green"
          unit=" $"
        />
        <StatCard 
          icon={Thermometer} 
          label="Total IoT Devices" 
          value={stats.totalIoTDevices} 
          color="neon-red" 
        />
      </div>

      {/* Auto-refresh info */}
      <div className="mt-12 p-4 bg-dark-800/50 border border-gray-700/30 rounded-lg text-center">
        <p className="text-sm text-gray-400">
          📊 Dashboard metrics auto-refresh every 30 seconds
        </p>
      </div>
    </div>
  )
}
