import { BarChart3, Cpu, Zap, Activity, Gauge, AlertCircle, Wifi } from 'lucide-react'

export default function Sidebar({ activeMenu, setActiveMenu, health }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Gauge },
    { id: 'cpu', label: 'CPU Metrics', icon: Cpu },
    { id: 'memory', label: 'Memory', icon: Zap },
    { id: 'requests', label: 'Requests', icon: Activity },
    { id: 'iot', label: 'IoT Sensors', icon: Wifi },
    { id: 'alerts', label: 'Alerts', icon: AlertCircle, badge: 'Soon' },
  ]

  return (
    <div className="w-64 bg-dark-800 border-r border-neon-cyan/20 p-6 flex flex-col">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-3">
        <div className="p-2 bg-neon-cyan/20 rounded-lg">
          <BarChart3 className="w-6 h-6 text-neon-cyan" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-neon-cyan neon-glow">MetricsPulse</h1>
          <p className="text-xs text-gray-400">MONITORING</p>
        </div>
      </div>

      {/* Health Status */}
      {health && (
        <div className="mb-6 p-3 bg-dark-900 rounded-lg border border-green-500/30">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-400">Backend Online</span>
          </div>
        </div>
      )}

      {/* Menu Items */}
      <nav className="flex-1 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = activeMenu === item.id

          return (
            <button
              key={item.id}
              onClick={() => setActiveMenu(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? 'bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-dark-700'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge && (
                <span className="text-xs bg-neon-yellow/20 text-neon-yellow px-2 py-1 rounded">
                  {item.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="pt-4 border-t border-gray-700 text-xs text-gray-500">
        <p>Version 1.0.0</p>
        <p>Real-Time Monitoring System</p>
      </div>
    </div>
  )
}
