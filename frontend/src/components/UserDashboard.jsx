import { useState, useEffect } from 'react'
import { RefreshCw, AlertTriangle, AlertCircle, CheckCircle, Server, Plus } from 'lucide-react'
import { useDevices } from '../context/DeviceContext'
import GaugeChart from './GaugeChart'
import AddDeviceModal from './AddDeviceModal'
import api from '../api'

export default function UserDashboard() {
  const { iotDevices: devices, selectedIoTDevice: selectedDevice, setSelectedIoTDevice: setSelectedDevice, createIoTDevice } = useDevices()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [alerts, setAlerts] = useState([])
  const [showAddDeviceModal, setShowAddDeviceModal] = useState(false)
  const [addingDevice, setAddingDevice] = useState(false)

  const currentDevice = devices?.find(d => d.id === selectedDevice)

  // Fetch data for selected device
  useEffect(() => {
    if (!selectedDevice || !currentDevice) return

    const fetchData = async () => {
      try {
        setLoading(true)
        const source = currentDevice.source

        // Fetch metrics for this device
        const [latestRes, historyRes] = await Promise.all([
          api.get(`/api/metrics/latest?source=${source}`),
          api.get(`/api/metrics/history?metric_type=${currentDevice.device_type}&source=${source}&minutes=120`)
        ])

        setData({
          latest: latestRes.data,
          history: historyRes.data?.data || []
        })
        setLastUpdate(new Date())
      } catch (err) {
        console.error('Failed to fetch device data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [selectedDevice, currentDevice])

  const formatTime = (date) => {
    return date.toLocaleTimeString('vi-VN')
  }

  const formatValue = (value) => {
    return typeof value === 'number' ? value.toFixed(2) : 'N/A'
  }

  const getDeviceTypeLabel = (type) => {
    const labels = {
      cpu: 'CPU Usage',
      memory: 'Memory Usage',
      temperature: 'Temperature',
      humidity: 'Humidity',
      soil_moisture: 'Soil Moisture',
      light_intensity: 'Light Intensity',
      pressure: 'Pressure'
    }
    return labels[type] || type
  }

  // Handle adding new device
  const handleAddDevice = async (deviceData) => {
    try {
      setAddingDevice(true)
      await createIoTDevice(deviceData)
      setShowAddDeviceModal(false)
    } catch (err) {
      console.error('Failed to add device:', err)
      throw err
    } finally {
      setAddingDevice(false)
    }
  }

  // No devices state
  if (!devices || devices.length === 0) {
    return (
      <div className="min-h-screen bg-dark-900 p-8 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="bg-dark-800 border border-yellow-500/30 rounded-xl p-12 mb-6">
            <Server className="w-16 h-16 text-yellow-400 mx-auto mb-4 opacity-50" />
            <h2 className="text-2xl font-bold text-white mb-4">No Devices Yet</h2>
            <p className="text-gray-400 mb-6">
              You haven't added any IoT devices yet. Create your first device by entering the sensor code and device details below.
            </p>
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6">
              <p className="text-sm text-yellow-400">
                💡 You can add IoT sensors like temperature, humidity, soil moisture, light intensity, or pressure sensors.
              </p>
            </div>
            <button
              onClick={() => setShowAddDeviceModal(true)}
              className="w-full px-6 py-3 bg-neon-cyan/20 border border-neon-cyan/60 rounded-lg text-neon-cyan font-semibold hover:bg-neon-cyan/30 transition-colors flex items-center justify-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Add Your First Device
            </button>
          </div>
        </div>

        <AddDeviceModal
          isOpen={showAddDeviceModal}
          onClose={() => setShowAddDeviceModal(false)}
          onAdd={handleAddDevice}
          isLoading={addingDevice}
        />
      </div>
    )
  }

  // Device not selected
  if (!currentDevice || !selectedDevice) {
    return (
      <div className="min-h-screen bg-dark-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 text-lg">Please select a device from the sidebar</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">{currentDevice.name}</h1>
          <div className="flex items-center gap-4 text-gray-400">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              {getDeviceTypeLabel(currentDevice.device_type)}
            </span>
            {currentDevice.location && <span>📍 {currentDevice.location}</span>}
            <span className="text-sm text-gray-500">Source: {currentDevice.source}</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-400 mb-1">Last updated</p>
          <p className="text-lg text-neon-cyan font-mono">{formatTime(lastUpdate)}</p>
        </div>
      </div>

      {/* Device Selector */}
      <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white">Available Devices</h3>
          <button
            onClick={() => setShowAddDeviceModal(true)}
            className="px-3 py-1 bg-neon-cyan/20 border border-neon-cyan/60 rounded-lg text-neon-cyan text-sm hover:bg-neon-cyan/30 transition-colors flex items-center gap-1"
          >
            <Plus className="w-4 h-4" />
            Add Device
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {devices.map(device => (
            <button
              key={device.id}
              onClick={() => setSelectedDevice(device.id)}
              className={`p-4 rounded-lg transition-all text-left border ${
                selectedDevice === device.id
                  ? 'bg-neon-cyan/20 border-neon-cyan/60 text-neon-cyan'
                  : 'bg-dark-900 border-gray-700 text-gray-400 hover:border-neon-cyan/40'
              }`}
            >
              <p className="font-semibold text-sm">{device.name}</p>
              <p className="text-xs mt-1 opacity-75">{device.device_type}</p>
            </button>
          ))}
        </div>
      </div>

      <AddDeviceModal
        isOpen={showAddDeviceModal}
        onClose={() => setShowAddDeviceModal(false)}
        onAdd={handleAddDevice}
        isLoading={addingDevice}
      />

      {/* Data Display */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="text-gray-400 flex items-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin" />
            Loading data...
          </div>
        </div>
      ) : data ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Current Value */}
          <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8">
            <h3 className="text-xl font-semibold text-white mb-6">Current Value</h3>
            <div className="text-center">
              <p className="text-6xl font-bold text-neon-cyan mb-2">
                {data.latest?.value ? formatValue(data.latest.value) : 'N/A'}
              </p>
              <p className="text-gray-400">
                {getDeviceTypeLabel(currentDevice.device_type)}
              </p>
              {data.latest?.timestamp && (
                <p className="text-sm text-gray-500 mt-4">
                  at {new Date(data.latest.timestamp).toLocaleTimeString('vi-VN')}
                </p>
              )}
            </div>
          </div>

          {/* Gauge Chart */}
          <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8">
            <h3 className="text-xl font-semibold text-white mb-6">Recent Trend</h3>
            {data.history && data.history.length > 0 ? (
              <GaugeChart data={data.history} />
            ) : (
              <p className="text-gray-400 text-center py-8">No data available</p>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-dark-800 border border-yellow-500/20 rounded-xl p-8 text-center">
          <AlertCircle className="w-8 h-8 text-yellow-400 mx-auto mb-3" />
          <p className="text-gray-400">No data available for this device</p>
        </div>
      )}

      {/* Recent Metrics */}
      {data?.history && data.history.length > 0 && (
        <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8">
          <h3 className="text-xl font-semibold text-white mb-6">Recent Metrics (Last 120 minutes)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 text-gray-400">Time</th>
                  <th className="text-right py-3 text-gray-400">Value</th>
                </tr>
              </thead>
              <tbody>
                {data.history.slice(-10).reverse().map((metric, idx) => (
                  <tr key={idx} className="border-b border-gray-700 hover:bg-dark-900 transition-all">
                    <td className="py-3 text-gray-300">
                      {new Date(metric.timestamp).toLocaleTimeString('vi-VN')}
                    </td>
                    <td className="text-right text-neon-cyan font-mono">
                      {formatValue(metric.value)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
