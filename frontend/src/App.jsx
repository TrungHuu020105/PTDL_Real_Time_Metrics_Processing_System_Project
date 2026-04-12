import { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import { DeviceProvider } from './context/DeviceContext'
import api from './api'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import UserDashboard from './components/UserDashboard'
import AdminDashboard from './components/AdminDashboard'
import CPUMetrics from './components/CPUMetrics'
import IoTMetrics from './components/IoTMetrics'
import IoTDeviceManager from './components/IoTDeviceManager'
import MemoryMetrics from './components/MemoryMetrics'
import Alerts from './components/Alerts'
import AdminPanel from './components/AdminPanel'
import ClientMonitor from './components/ClientMonitor'
import ServerStore from './components/ServerStore'
import Login from './components/Login'

function AppContent() {
  const [activeMenu, setActiveMenu] = useState('iot-devices')
  const [health, setHealth] = useState(null)
  const { user, token, loading } = useAuth()

  useEffect(() => {
    // Check backend health
    const checkHealth = async () => {
      try {
        const response = await api.get('/api/health')
        setHealth(response.data)
      } catch (error) {
        console.error('Backend not available:', error)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 10000)
    return () => clearInterval(interval)
  }, [])

  const renderContent = () => {
    switch (activeMenu) {
      case 'dashboard':
        // Admin gets AdminDashboard, users get UserDashboard
        if (user?.role === 'admin') {
          return <AdminDashboard />
        } else {
          return <UserDashboard />
        }
      case 'iot-devices':
        return <IoTDeviceManager />
      case 'servers':
        return <ServerStore />
      case 'cpu':
        return <CPUMetrics />
      case 'memory':
        return <MemoryMetrics />
      case 'iot':
        return <IoTMetrics />
      case 'alerts':
        return <Alerts />
      case 'client-monitor':
        return <ClientMonitor />
      case 'admin-panel':
        return <AdminPanel />
      default:
        // Default: admin gets dashboard, users get IoT devices (UserDashboard)
        return user?.role === 'admin' ? <AdminDashboard /> : <UserDashboard />
    }
  }

  // Show loading
  if (loading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  // Show login if not authenticated
  if (!token || !user) {
    return <Login />
  }

  // Show dashboard if authenticated
  return (
    <div className="flex h-screen bg-dark-900">
      <Sidebar activeMenu={activeMenu} setActiveMenu={setActiveMenu} health={health} />
      <div className="flex-1 overflow-y-auto">
        {renderContent()}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <DeviceProvider>
        <AppContent />
      </DeviceProvider>
    </AuthProvider>
  )
}
