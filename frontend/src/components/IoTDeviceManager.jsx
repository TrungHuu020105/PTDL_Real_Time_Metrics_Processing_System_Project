import { useState, useEffect } from 'react'
import { Plus, Trash2, Edit2, Home, Radio, X, Power, PowerOff } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useDevices } from '../context/DeviceContext'
import { useAuth } from '../context/AuthContext'
import api from '../api'

export default function IoTDeviceManager() {
  const { iotDevices, allIoTDevices, createIoTDevice, updateIoTDevice, deleteIoTDevice } = useDevices()
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  
  // Use allIoTDevices if admin, otherwise use iotDevices
  const displayDevices = isAdmin ? allIoTDevices : iotDevices
  
  // Debug log
  useEffect(() => {
    console.log('IoTDeviceManager - user:', user)
    console.log('IoTDeviceManager - isAdmin:', isAdmin)
    console.log('IoTDeviceManager - iotDevices:', iotDevices)
    console.log('IoTDeviceManager - allIoTDevices:', allIoTDevices)
    console.log('IoTDeviceManager - displayDevices:', displayDevices)
  }, [isAdmin, iotDevices, allIoTDevices, displayDevices])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showChartModal, setShowChartModal] = useState(false)
  const [selectedDeviceForChart, setSelectedDeviceForChart] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    device_type: 'temperature',
    source: '',
    location: ''
  })
  const [loading, setLoading] = useState(false)
  const [latestMetrics, setLatestMetrics] = useState({})
  const [chartData, setChartData] = useState([])
  const [chartLoading, setChartLoading] = useState(false)
  const [chartStats, setChartStats] = useState({
    average: 0,
    min: 0,
    max: 0
  })
  const [deviceOwners, setDeviceOwners] = useState({})
  const [chartLastUpdated, setChartLastUpdated] = useState(null)

  // Fetch owner information for all devices
  useEffect(() => {
    const fetchOwnerInfo = async () => {
      try {
        const owners = {}
        
        // Fetch owner info for each device
        for (const device of displayDevices) {
          if (device.user_id) {
            try {
              const response = await api.get(`/api/auth/users/${device.user_id}`)
              owners[device.id] = response.data.username || response.data.email
              console.log(`Fetched owner for device ${device.id}:`, owners[device.id])
            } catch (err) {
              console.error(`Failed to fetch owner for device ${device.id}:`, err)
              owners[device.id] = `User #${device.user_id}`
            }
          }
        }
        
        setDeviceOwners(owners)
        console.log('All device owners fetched:', owners)
      } catch (err) {
        console.error('Failed to fetch owner information:', err)
      }
    }

    if (displayDevices.length > 0) {
      fetchOwnerInfo()
    }
  }, [displayDevices])

  // Fetch latest metrics for all devices
  useEffect(() => {
    const fetchLatestMetrics = async () => {
      try {
        const metrics = {}
        for (const device of displayDevices) {
          try {
            // Fetch history with very recent timeframe to get latest value
            const response = await api.get('/api/metrics/history', {
              params: {
                metric_type: device.device_type,
                minutes: 5
              }
            })
            
            // Get the latest value from the returned data
            if (response.data.data && response.data.data.length > 0) {
              // Sort by timestamp descending and get the first (most recent)
              const latest = response.data.data.sort((a, b) => 
                new Date(b.timestamp) - new Date(a.timestamp)
              )[0]
              
              metrics[device.id] = {
                value: latest.value,
                timestamp: latest.timestamp
              }
            } else {
              metrics[device.id] = {
                value: null,
                timestamp: null
              }
            }
          } catch (err) {
            console.error(`Failed to fetch latest metric for device ${device.id}:`, err)
            metrics[device.id] = {
              value: null,
              timestamp: null
            }
          }
        }
        setLatestMetrics(metrics)
      } catch (err) {
        console.error('Failed to fetch latest metrics:', err)
      }
    }

    // Fetch immediately and then every 5 seconds
    fetchLatestMetrics()
    const interval = setInterval(fetchLatestMetrics, 5000)
    return () => clearInterval(interval)
  }, [displayDevices])

  // Helper function to aggregate data by minute (1 point per minute)
  const aggregateDataByMinute = (rawData) => {
    if (!rawData || rawData.length === 0) return []
    
    // Group data by minute
    const minuteGroups = {}
    rawData.forEach(item => {
      const date = new Date(item.timestamp)
      // Round to nearest minute
      date.setSeconds(0, 0)
      const minuteKey = date.getTime()
      
      if (!minuteGroups[minuteKey]) {
        minuteGroups[minuteKey] = []
      }
      minuteGroups[minuteKey].push(item.value)
    })
    
    // Calculate average for each minute and format
    const aggregatedData = Object.keys(minuteGroups)
      .sort((a, b) => parseInt(a) - parseInt(b))
      .map(minuteKey => {
        const values = minuteGroups[minuteKey]
        const avgValue = values.reduce((a, b) => a + b, 0) / values.length
        const date = new Date(parseInt(minuteKey))
        
        return {
          time: date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
          }),
          value: parseFloat(avgValue.toFixed(2)),
          timestamp: date.toISOString()
        }
      })
    
    return aggregatedData
  }

  // Fetch chart data for selected device (past 2 hours = 120 minutes)
  const handleOpenChart = async (device) => {
    setSelectedDeviceForChart(device)
    setShowChartModal(true)
    setChartLoading(true)
    try {
      const response = await api.get('/api/metrics/history', {
        params: {
          metric_type: device.device_type,
          minutes: 120 // 2 hours
        }
      })
      
      // Aggregate data by minute (1 point per minute)
      const formattedData = aggregateDataByMinute(response.data.data)
      
      // Calculate statistics from original data (not aggregated)
      if (response.data.data && response.data.data.length > 0) {
        const values = response.data.data.map(d => d.value)
        const average = values.reduce((a, b) => a + b, 0) / values.length
        const min = Math.min(...values)
        const max = Math.max(...values)
        
        setChartStats({
          average: parseFloat(average.toFixed(2)),
          min: parseFloat(min.toFixed(2)),
          max: parseFloat(max.toFixed(2))
        })
      }
      
      setChartData(formattedData)
      setChartLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to fetch chart data:', err)
      setChartData([])
      setChartStats({ average: 0, min: 0, max: 0 })
    } finally {
      setChartLoading(false)
    }
  }

  // Auto-refresh chart every 1 minute when modal is open
  useEffect(() => {
    if (!showChartModal || !selectedDeviceForChart) return

    const refreshChartData = async () => {
      try {
        console.log('Refreshing chart data for device:', selectedDeviceForChart.device_type)
        const response = await api.get('/api/metrics/history', {
          params: {
            metric_type: selectedDeviceForChart.device_type,
            minutes: 120 // 2 hours
          }
        })
        
        // Aggregate data by minute (1 point per minute)
        const formattedData = aggregateDataByMinute(response.data.data)
        
        // Calculate statistics from original data (not aggregated)
        if (response.data.data && response.data.data.length > 0) {
          const values = response.data.data.map(d => d.value)
          const average = values.reduce((a, b) => a + b, 0) / values.length
          const min = Math.min(...values)
          const max = Math.max(...values)
          
          setChartStats({
            average: parseFloat(average.toFixed(2)),
            min: parseFloat(min.toFixed(2)),
            max: parseFloat(max.toFixed(2))
          })
        }
        
        setChartData(formattedData)
        setChartLastUpdated(new Date())
        console.log('Chart updated at:', new Date().toLocaleTimeString())
      } catch (err) {
        console.error('Failed to refresh chart data:', err)
      }
    }

    // Refresh immediately when modal opens
    refreshChartData()
    
    // Then refresh every 1 minute (60000 ms)
    const interval = setInterval(refreshChartData, 60000)
    
    return () => clearInterval(interval)
  }, [showChartModal, selectedDeviceForChart])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      
      if (editingId) {
        await updateIoTDevice(editingId, formData)
        setEditingId(null)
      } else {
        await createIoTDevice(formData)
      }
      
      setFormData({
        name: '',
        device_type: 'temperature',
        source: '',
        location: ''
      })
      setShowCreateModal(false)
    } catch (err) {
      alert('Error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (deviceId) => {
    if (confirm('Delete this IoT device?')) {
      try {
        await deleteIoTDevice(deviceId)
      } catch (err) {
        alert('Error: ' + err.message)
      }
    }
  }

  // Admin functions
  const disconnectIoTDevice = async (deviceId) => {
    try {
      await api.put(`/api/admin/iot-devices/${deviceId}/disconnect`)
      alert('Device disconnected successfully')
      // Refresh devices list
      window.location.reload()
    } catch (err) {
      alert('Error disconnecting device: ' + (err.response?.data?.detail || err.message))
    }
  }

  const reconnectIoTDevice = async (deviceId) => {
    try {
      await api.put(`/api/admin/iot-devices/${deviceId}/reconnect`)
      alert('Device reconnected successfully')
      // Refresh devices list
      window.location.reload()
    } catch (err) {
      alert('Error reconnecting device: ' + (err.response?.data?.detail || err.message))
    }
  }

  const adminDeleteIoTDevice = async (deviceId) => {
    if (confirm('Delete this IoT device? (Admin action)')) {
      try {
        await api.delete(`/api/admin/iot-devices/${deviceId}`)
        alert('Device deleted successfully')
        // Refresh devices list
        window.location.reload()
      } catch (err) {
        alert('Error deleting device: ' + (err.response?.data?.detail || err.message))
      }
    }
  }

  const startEdit = (device) => {
    setFormData({
      name: device.name,
      device_type: device.device_type,
      source: device.source,
      location: device.location || ''
    })
    setEditingId(device.id)
    setShowCreateModal(true)
  }

  const getDeviceTypeColor = (type) => {
    const colors = {
      temperature: 'neon-orange',
      humidity: 'neon-cyan',
      soil_moisture: 'neon-green',
      light_intensity: 'neon-yellow',
      pressure: 'neon-purple'
    }
    return colors[type] || 'neon-cyan'
  }

  const getMetricUnit = (type) => {
    const units = {
      temperature: '°C',
      humidity: '%',
      soil_moisture: '%',
      light_intensity: 'lux',
      pressure: 'hPa'
    }
    return units[type] || ''
  }

  const getLatestValue = (deviceId) => {
    const metric = latestMetrics[deviceId]
    if (!metric || metric.value === null || metric.value === undefined) {
      return 'N/A'
    }
    return typeof metric.value === 'number' ? metric.value.toFixed(2) : metric.value
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">IoT Devices</h1>
          <p className="text-gray-400">Manage your IoT sensors and devices</p>
        </div>
        <button
          onClick={() => {
            setEditingId(null)
            setFormData({ name: '', device_type: 'temperature', source: '', location: '' })
            setShowCreateModal(true)
          }}
          className="flex items-center gap-2 bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 hover:border-neon-cyan px-4 py-2 rounded-lg transition-all"
        >
          <Plus className="w-5 h-5" />
          Add Device
        </button>
      </div>

      {/* Devices Grid */}
      {displayDevices.length === 0 ? (
        <div className="text-center py-16">
          <Radio className="w-16 h-16 text-gray-600 mx-auto mb-4 opacity-50" />
          <h3 className="text-xl font-semibold text-white mb-2">No IoT Devices</h3>
          <p className="text-gray-400 mb-6">Create your first IoT device to start monitoring</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 px-6 py-3 rounded-lg hover:border-neon-cyan transition-all"
          >
            <Plus className="w-5 h-5" />
            Create First Device
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {displayDevices.map(device => (
            <div
              key={device.id}
              onClick={() => handleOpenChart(device)}
              className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-6 hover:border-neon-cyan/60 hover:cursor-pointer transition-all hover:bg-dark-700"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white mb-1">{device.name}</h3>
                  <p className="text-xs text-gray-500 font-mono">Source: {device.source}</p>
                  {deviceOwners[device.id] && (
                    <p className="text-xs text-gray-500">Created by: {deviceOwners[device.id]}</p>
                  )}
                </div>
                <span className={`text-xs text-${getDeviceTypeColor(device.device_type)} bg-${getDeviceTypeColor(device.device_type)}/20 px-2 py-1 rounded`}>
                  {device.device_type}
                </span>
              </div>

              {device.location && (
                <div className="flex items-center gap-2 text-sm text-gray-400 mb-4">
                  <Home className="w-4 h-4" />
                  {device.location}
                </div>
              )}

              {/* Real-time Metric Display */}
              <div className="bg-dark-900/50 rounded-lg p-4 mb-4 border border-neon-cyan/20">
                <p className="text-xs text-gray-400 mb-2">Real-time Value</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-neon-cyan">
                    {getLatestValue(device.id)}
                  </span>
                  <span className="text-sm text-gray-400">
                    {getMetricUnit(device.device_type)}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 mb-4">
                <span className={`w-2 h-2 ${device.is_active ? 'bg-green-500' : 'bg-red-500'} rounded-full`}></span>
                <span className={`text-xs ${device.is_active ? 'text-green-400' : 'text-red-400'}`}>
                  {device.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="flex flex-col gap-2">
                {isAdmin ? (
                  <>
                    {/* Admin buttons */}
                    <div className="flex gap-2">
                      {device.is_active ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            disconnectIoTDevice(device.id)
                          }}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-orange-500/20 text-orange-400 rounded hover:bg-orange-500/30 transition-all text-sm"
                        >
                          <PowerOff className="w-4 h-4" />
                          Disconnect
                        </button>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            reconnectIoTDevice(device.id)
                          }}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 transition-all text-sm"
                        >
                          <Power className="w-4 h-4" />
                          Reconnect
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          adminDeleteIoTDevice(device.id)
                        }}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-all text-sm"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    {/* User buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          startEdit(device)
                        }}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-500/20 text-blue-400 rounded hover:bg-blue-500/30 transition-all text-sm"
                      >
                        <Edit2 className="w-4 h-4" />
                        Edit
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(device.id)
                        }}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-all text-sm"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8 max-w-md w-full mx-4">
            <h3 className="text-2xl font-bold text-white mb-6">
              {editingId ? 'Edit IoT Device' : 'Add New IoT Device'}
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Device Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full bg-dark-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-cyan outline-none"
                  placeholder="E.g., Room 1 Temperature"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Device Type</label>
                <select
                  value={formData.device_type}
                  onChange={(e) => setFormData({...formData, device_type: e.target.value})}
                  className="w-full bg-dark-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-cyan outline-none"
                >
                  <option value="temperature">🌡️  Temperature</option>
                  <option value="humidity">💧 Humidity</option>
                  <option value="soil_moisture">🌱 Soil Moisture</option>
                  <option value="light_intensity">☀️  Light Intensity</option>
                  <option value="pressure">📊 Pressure</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Source ID (Unique)</label>
                <input
                  type="text"
                  required
                  value={formData.source}
                  onChange={(e) => setFormData({...formData, source: e.target.value})}
                  className="w-full bg-dark-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-cyan outline-none font-mono"
                  placeholder="E.g., room1_temp_sensor"
                  disabled={!!editingId}
                  title="Cannot change source after creation"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Location (Optional)</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  className="w-full bg-dark-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-cyan outline-none"
                  placeholder="E.g., Living Room"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false)
                    setEditingId(null)
                  }}
                  className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 rounded-lg hover:border-neon-cyan transition-all disabled:opacity-50"
                >
                  {loading ? 'Saving...' : editingId ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Chart Modal */}
      {showChartModal && selectedDeviceForChart && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8 max-w-4xl w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold text-white mb-1">
                  {selectedDeviceForChart.name}
                </h3>
                <p className="text-sm text-gray-400">
                  Last 2 hours of {selectedDeviceForChart.device_type} data
                </p>
                {deviceOwners[selectedDeviceForChart.id] && (
                  <p className="text-xs text-gray-500 mt-2">
                    Created by: {deviceOwners[selectedDeviceForChart.id]}
                  </p>
                )}
                {chartLastUpdated && (
                  <p className="text-xs text-gray-600 mt-1">
                    Updated: {chartLastUpdated.toLocaleTimeString()}
                  </p>
                )}
              </div>
              <button
                onClick={() => {
                  setShowChartModal(false)
                  setSelectedDeviceForChart(null)
                  setChartData([])
                  setChartStats({ average: 0, min: 0, max: 0 })
                }}
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
                {/* Statistics Cards */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-dark-900/50 border border-neon-cyan/30 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">Average</p>
                    <p className="text-2xl font-bold text-neon-cyan">
                      {chartStats.average}
                      <span className="text-sm text-gray-400 ml-1">{getMetricUnit(selectedDeviceForChart.device_type)}</span>
                    </p>
                  </div>
                  <div className="bg-dark-900/50 border border-neon-green/30 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">Minimum</p>
                    <p className="text-2xl font-bold text-neon-green">
                      {chartStats.min}
                      <span className="text-sm text-gray-400 ml-1">{getMetricUnit(selectedDeviceForChart.device_type)}</span>
                    </p>
                  </div>
                  <div className="bg-dark-900/50 border border-neon-orange/30 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">Maximum</p>
                    <p className="text-2xl font-bold text-neon-orange">
                      {chartStats.max}
                      <span className="text-sm text-gray-400 ml-1">{getMetricUnit(selectedDeviceForChart.device_type)}</span>
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
                        label={{ value: getMetricUnit(selectedDeviceForChart.device_type), angle: -90, position: 'insideLeft' }}
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
                        dataKey="value" 
                        stroke="#00d4ff" 
                        dot={false}
                        strokeWidth={2}
                        name={selectedDeviceForChart.device_type}
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
                onClick={() => {
                  setShowChartModal(false)
                  setSelectedDeviceForChart(null)
                  setChartData([])
                  setChartStats({ average: 0, min: 0, max: 0 })
                }}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
