import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import CPUMetrics from './components/CPUMetrics'
import IoTMetrics from './components/IoTMetrics'
import MemoryMetrics from './components/MemoryMetrics'
import RequestMetrics from './components/RequestMetrics'
import Alerts from './components/Alerts'

export default function App() {
  const [activeMenu, setActiveMenu] = useState('dashboard')
  const [health, setHealth] = useState(null)

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
      case 'requests':
        return <RequestMetrics />
      case 'iot':
        return <IoTMetrics />
      case 'alerts':
        return <Alerts />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="flex h-screen bg-dark-900">
      <Sidebar activeMenu={activeMenu} setActiveMenu={setActiveMenu} health={health} />
      <div className="flex-1 overflow-y-auto">
        {renderContent()}
      </div>
    </div>
  )
}
