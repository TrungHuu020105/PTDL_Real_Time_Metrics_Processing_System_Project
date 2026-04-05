import { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import CPUMetrics from './components/CPUMetrics'
import IoTMetrics from './components/IoTMetrics'
import MemoryMetrics from './components/MemoryMetrics'
import Alerts from './components/Alerts'
import Login from './components/Login'

function AppContent() {
  const [activeMenu, setActiveMenu] = useState('dashboard')
  const [health, setHealth] = useState(null)
  const { user, token, loading } = useAuth()

  useEffect(() => {
    // Check backend health
    const checkHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/health')
        const data = await response.json()
        setHealth(data)
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
        return <Dashboard />
      case 'cpu':
        return <CPUMetrics />
      case 'memory':
        return <MemoryMetrics />
      case 'iot':
        return <IoTMetrics />
      case 'alerts':
        return <Alerts />
      default:
        return <Dashboard />
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
      <AppContent />
    </AuthProvider>
  )
}
