import { AlertTriangle, CheckCircle, AlertCircle, Zap } from 'lucide-react'

export default function Alerts() {
  const alertTypes = [
    {
      id: 1,
      type: 'info',
      icon: AlertCircle,
      title: 'Coming Soon',
      description: 'Alert system is planned for the next phase of development',
      timestamp: 'Planned'
    },
    {
      id: 2,
      type: 'info',
      icon: CheckCircle,
      title: 'System Healthy',
      description: 'All metrics are operating within normal parameters',
      timestamp: 'Ongoing'
    },
  ]

  const getIcon = (iconName) => {
    const icons = {
      AlertTriangle,
      CheckCircle,
      AlertCircle,
      Zap,
    }
    return icons[iconName] || AlertCircle
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Alerts & Anomalies</h1>
        <p className="text-gray-400 mt-2">System notifications and warnings</p>
      </div>

      {/* Alert Types Explanation */}
      <div className="card-border p-6 bg-dark-800">
        <h3 className="text-white font-semibold mb-4">About Alerts & Anomalies</h3>
        <p className="text-gray-400 text-sm mb-4">
          The alert system is planned for the next development phase. When implemented, it will include:
        </p>
        <ul className="space-y-2 text-sm text-gray-400">
          <li>🔴 <strong>Critical Alerts:</strong> CPU/Memory exceeds 90%</li>
          <li>🟡 <strong>Warning Alerts:</strong> Metrics trending upward</li>
          <li>🟢 <strong>Info Alerts:</strong> System status changes</li>
          <li>📊 <strong>Anomalies:</strong> Unusual patterns detected by ML</li>
          <li>🔔 <strong>Notifications:</strong> Email/Slack integration</li>
        </ul>
      </div>

      {/* Current Status */}
      <div className="space-y-4">
        {alertTypes.map((alert) => {
          const Icon = getIcon(alert.icon.name || 'AlertCircle')
          return (
            <div key={alert.id} className="card-border card-hover p-6 bg-dark-800 flex items-start gap-4">
              <Icon className="w-6 h-6 text-neon-cyan flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="text-white font-semibold">{alert.title}</h3>
                <p className="text-gray-400 text-sm mt-1">{alert.description}</p>
                <p className="text-xs text-gray-500 mt-2">{alert.timestamp}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Feature Roadmap */}
      <div className="card-border p-6 bg-dark-800">
        <h3 className="text-white font-semibold mb-4">📋 Feature Roadmap</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <input type="checkbox" checked disabled className="w-4 h-4" />
            <span className="text-gray-400 text-sm line-through">Backend metrics collection</span>
            <span className="text-neon-green text-xs ml-auto">✓ Done</span>
          </div>
          <div className="flex items-center gap-3">
            <input type="checkbox" checked disabled className="w-4 h-4" />
            <span className="text-gray-400 text-sm line-through">Frontend dashboard UI</span>
            <span className="text-neon-green text-xs ml-auto">✓ Done</span>
          </div>
          <div className="flex items-center gap-3">
            <input type="checkbox" checked disabled className="w-4 h-4" />
            <span className="text-gray-400 text-sm line-through">IoT sensor integration</span>
            <span className="text-neon-green text-xs ml-auto">✓ Done</span>
          </div>
          <div className="flex items-center gap-3">
            <input type="checkbox" disabled className="w-4 h-4" />
            <span className="text-gray-400 text-sm">Real-time alert system</span>
            <span className="text-neon-yellow text-xs ml-auto">Next</span>
          </div>
          <div className="flex items-center gap-3">
            <input type="checkbox" disabled className="w-4 h-4" />
            <span className="text-gray-400 text-sm">Anomaly detection</span>
            <span className="text-gray-500 text-xs ml-auto">Planned</span>
          </div>
          <div className="flex items-center gap-3">
            <input type="checkbox" disabled className="w-4 h-4" />
            <span className="text-gray-400 text-sm">Email notifications</span>
            <span className="text-gray-500 text-xs ml-auto">Planned</span>
          </div>
        </div>
      </div>
    </div>
  )
}
