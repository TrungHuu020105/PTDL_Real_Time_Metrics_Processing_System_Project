import { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from './AuthContext'
import api from '../api'

const DeviceContext = createContext()

export function DeviceProvider({ children }) {
  const { user, token } = useAuth()
  
  // IoT Devices (user-owned)
  const [iotDevices, setIotDevices] = useState([])
  const [selectedIoTDevice, setSelectedIoTDevice] = useState(null)
  
  // Admin view: all user IoT devices
  const [allIoTDevices, setAllIoTDevices] = useState([])
  
  // Servers (admin-created, user-subscribed)
  const [availableServers, setAvailableServers] = useState([])
  const [myServers, setMyServers] = useState([])
  const [selectedServer, setSelectedServer] = useState(null)
  
  // State
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Fetch IoT devices on mount
  useEffect(() => {
    if (user && token) {
      console.log('DeviceContext: User loaded, role:', user.role)
      if (user.role === 'admin') {
        console.log('User is admin, fetching ALL devices...')
        fetchAllIoTDevices()
      } else {
        console.log('User is regular user, fetching MY devices...')
        fetchIoTDevices()
      }
      fetchMyServers()
      fetchAvailableServers()
    }
  }, [user, token])

  // ============== IoT DEVICES ==============
  
  const fetchIoTDevices = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/iot-devices')
      setIotDevices(response.data.devices || [])
      
      // Auto-select first device
      if (response.data.devices?.length > 0 && !selectedIoTDevice) {
        setSelectedIoTDevice(response.data.devices[0].id)
      }
    } catch (err) {
      console.error('Failed to fetch IoT devices:', err)
    } finally {
      setLoading(false)
    }
  }

  const createIoTDevice = async (deviceData) => {
    try {
      const response = await api.post('/api/iot-devices', deviceData)
      setIotDevices([...iotDevices, response.data])
      return response.data
    } catch (err) {
      throw err
    }
  }

  const updateIoTDevice = async (deviceId, updates) => {
    try {
      const response = await api.put(`/api/iot-devices/${deviceId}`, updates)
      setIotDevices(iotDevices.map(d => d.id === deviceId ? response.data : d))
      return response.data
    } catch (err) {
      throw err
    }
  }

  const deleteIoTDevice = async (deviceId) => {
    try {
      await api.delete(`/api/iot-devices/${deviceId}`)
      setIotDevices(iotDevices.filter(d => d.id !== deviceId))
      if (selectedIoTDevice === deviceId) {
        setSelectedIoTDevice(iotDevices.length > 1 ? iotDevices[0].id : null)
      }
    } catch (err) {
      throw err
    }
  }

  // ============== ADMIN: IoT DEVICE MANAGEMENT ==============

  const fetchAllIoTDevices = async () => {
    try {
      setLoading(true)
      console.log('Fetching ALL IoT devices for admin...')
      const response = await api.get('/api/admin/iot-devices')
      console.log('API Response:', response.data)
      setAllIoTDevices(response.data.devices || [])
      console.log('AllIoTDevices updated:', response.data.devices || [])
    } catch (err) {
      console.error('Failed to fetch all IoT devices:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const deleteIoTDeviceAdmin = async (deviceId) => {
    try {
      await api.delete(`/api/admin/iot-devices/${deviceId}`)
      setAllIoTDevices(allIoTDevices.filter(d => d.id !== deviceId))
      return true
    } catch (err) {
      throw err
    }
  }

  const disconnectIoTDevice = async (deviceId) => {
    try {
      const response = await api.put(`/api/admin/iot-devices/${deviceId}/disconnect`)
      setAllIoTDevices(allIoTDevices.map(d => 
        d.id === deviceId ? { ...d, is_active: false } : d
      ))
      return response.data
    } catch (err) {
      throw err
    }
  }

  const reconnectIoTDevice = async (deviceId) => {
    try {
      const response = await api.put(`/api/admin/iot-devices/${deviceId}/reconnect`)
      setAllIoTDevices(allIoTDevices.map(d => 
        d.id === deviceId ? { ...d, is_active: true } : d
      ))
      return response.data
    } catch (err) {
      throw err
    }
  }

  // ============== SERVERS ==============
  
  const fetchAvailableServers = async () => {
    try {
      const response = await api.get('/api/servers')
      setAvailableServers(response.data.servers || [])
    } catch (err) {
      console.error('Failed to fetch available servers:', err)
    }
  }

  const fetchMyServers = async () => {
    try {
      const response = await api.get('/api/servers/my-subscriptions')
      setMyServers(response.data.servers || [])
      
      // Auto-select first server
      if (response.data.servers?.length > 0 && !selectedServer) {
        setSelectedServer(response.data.servers[0].id)
      }
    } catch (err) {
      console.error('Failed to fetch my servers:', err)
    }
  }

  const subscribeToServer = async (serverId) => {
    try {
      await api.post(`/api/servers/${serverId}/subscribe`)
      await fetchMyServers() // Refresh list
      return true
    } catch (err) {
      throw err
    }
  }

  const unsubscribeFromServer = async (serverId) => {
    try {
      await api.delete(`/api/servers/${serverId}/unsubscribe`)
      setMyServers(myServers.filter(s => s.id !== serverId))
      if (selectedServer === serverId) {
        setSelectedServer(myServers.length > 1 ? myServers[0].id : null)
      }
    } catch (err) {
      throw err
    }
  }

  // ============== ADMIN FUNCTIONS ==============
  
  const createServer = async (serverData) => {
    try {
      const response = await api.post('/api/servers/admin/servers', serverData)
      setAvailableServers([...availableServers, response.data])
      return response.data
    } catch (err) {
      throw err
    }
  }

  const deleteServer = async (serverId) => {
    try {
      await api.delete(`/api/servers/admin/servers/${serverId}`)
      setAvailableServers(availableServers.filter(s => s.id !== serverId))
      await fetchMyServers() // Refresh user's servers
    } catch (err) {
      throw err
    }
  }

  const value = {
    // IoT Devices
    iotDevices,
    selectedIoTDevice,
    setSelectedIoTDevice,
    createIoTDevice,
    updateIoTDevice,
    deleteIoTDevice,
    fetchIoTDevices,
    
    // Admin IoT Device Management
    allIoTDevices,
    fetchAllIoTDevices,
    deleteIoTDeviceAdmin,
    disconnectIoTDevice,
    reconnectIoTDevice,
    
    // Servers
    availableServers,
    myServers,
    selectedServer,
    setSelectedServer,
    subscribeToServer,
    unsubscribeFromServer,
    fetchMyServers,
    fetchAvailableServers,
    
    // Admin
    createServer,
    deleteServer,
    
    // State
    loading,
    error,
  }

  return (
    <DeviceContext.Provider value={value}>
      {children}
    </DeviceContext.Provider>
  )
}

export function useDevices() {
  const context = useContext(DeviceContext)
  if (!context) {
    throw new Error('useDevices must be used within DeviceProvider')
  }
  return context
}
