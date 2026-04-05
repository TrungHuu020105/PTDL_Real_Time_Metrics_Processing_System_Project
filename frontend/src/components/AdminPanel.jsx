import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Plus, Trash2, Copy } from 'lucide-react'
import api from '../api'
import { useAuth } from '../context/AuthContext'

export default function AdminPanel() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('pending-users')
  const [pendingUsers, setPendingUsers] = useState([])
  const [allUsers, setAllUsers] = useState([])
  const [devices, setDevices] = useState([])
  const [newDevice, setNewDevice] = useState({ name: '', device_type: '', source: '', location: '' })
  const [selectedUser, setSelectedUser] = useState(null)
  const [userDevices, setUserDevices] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  // Fetch pending users
  const fetchPendingUsers = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/admin/users/pending')
      setPendingUsers(response.data.users || [])
    } catch (error) {
      setMessage('Failed to fetch pending users: ' + error.response?.data?.detail)
    } finally {
      setLoading(false)
    }
  }

  // Fetch all users
  const fetchAllUsers = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/admin/users')
      setAllUsers(response.data.users || [])
    } catch (error) {
      setMessage('Failed to fetch users: ' + error.response?.data?.detail)
    } finally {
      setLoading(false)
    }
  }

  // Fetch devices
  const fetchDevices = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/admin/devices')
      setDevices(response.data.devices || [])
    } catch (error) {
      setMessage('Failed to fetch devices: ' + error.response?.data?.detail)
    } finally {
      setLoading(false)
    }
  }

  // Approve user
  const approveUser = async (userId) => {
    try {
      await api.post(`/api/admin/users/${userId}/approve`)
      setMessage('User approved successfully')
      fetchPendingUsers()
      fetchAllUsers()
    } catch (error) {
      setMessage('Failed to approve user: ' + error.response?.data?.detail)
    }
  }

  // Reject user
  const rejectUser = async (userId) => {
    try {
      await api.post(`/api/admin/users/${userId}/reject`)
      setMessage('User rejected successfully')
      fetchPendingUsers()
      fetchAllUsers()
    } catch (error) {
      setMessage('Failed to reject user: ' + error.response?.data?.detail)
    }
  }

  // Create device
  const createDevice = async () => {
    if (!newDevice.name || !newDevice.device_type || !newDevice.source) {
      setMessage('Please fill in required fields')
      return
    }

    try {
      await api.post('/api/admin/devices', newDevice)
      setMessage('Device created successfully')
      setNewDevice({ name: '', device_type: '', source: '', location: '' })
      fetchDevices()
    } catch (error) {
      setMessage('Failed to create device: ' + error.response?.data?.detail)
    }
  }

  // Delete device
  const deleteDevice = async (deviceId) => {
    if (!confirm('Delete this device?')) return
    
    try {
      await api.delete(`/api/admin/devices/${deviceId}`)
      setMessage('Device deleted successfully')
      fetchDevices()
    } catch (error) {
      setMessage('Failed to delete device: ' + error.response?.data?.detail)
    }
  }

  // Grant device permission
  const grantPermission = async (userId, deviceId) => {
    try {
      await api.post(`/api/admin/users/${userId}/devices/${deviceId}/grant`)
      setMessage('Permission granted successfully')
      fetchUserDevices(userId)
    } catch (error) {
      setMessage('Failed to grant permission: ' + error.response?.data?.detail)
    }
  }

  // Revoke device permission
  const revokePermission = async (userId, deviceId) => {
    try {
      await api.delete(`/api/admin/users/${userId}/devices/${deviceId}/revoke`)
      setMessage('Permission revoked successfully')
      fetchUserDevices(userId)
    } catch (error) {
      setMessage('Failed to revoke permission: ' + error.response?.data?.detail)
    }
  }

  // Fetch user devices
  const fetchUserDevices = async (userId) => {
    try {
      const response = await api.get(`/api/admin/users/${userId}/devices`)
      setUserDevices(response.data.devices || [])
    } catch (error) {
      setUserDevices([])
    }
  }

  // Load data on mount
  useEffect(() => {
    fetchPendingUsers()
    fetchAllUsers()
    fetchDevices()
  }, [])

  // Auto-clear message after 3 seconds
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(''), 3000)
      return () => clearTimeout(timer)
    }
  }, [message])

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Admin Panel</h1>
        <p className="text-gray-400 mt-2">Manage users, devices, and permissions</p>
      </div>

      {/* Message */}
      {message && (
        <div className="p-4 bg-blue-500/20 border border-blue-500/50 text-blue-400 rounded">
          {message}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-700">
        <button
          onClick={() => setActiveTab('pending-users')}
          className={`px-4 py-2 font-semibold border-b-2 transition-all ${
            activeTab === 'pending-users'
              ? 'text-neon-cyan border-neon-cyan'
              : 'text-gray-400 border-transparent hover:text-gray-300'
          }`}
        >
          Pending Users ({pendingUsers.length})
        </button>
        <button
          onClick={() => setActiveTab('all-users')}
          className={`px-4 py-2 font-semibold border-b-2 transition-all ${
            activeTab === 'all-users'
              ? 'text-neon-cyan border-neon-cyan'
              : 'text-gray-400 border-transparent hover:text-gray-300'
          }`}
        >
          All Users
        </button>
        <button
          onClick={() => setActiveTab('devices')}
          className={`px-4 py-2 font-semibold border-b-2 transition-all ${
            activeTab === 'devices'
              ? 'text-neon-cyan border-neon-cyan'
              : 'text-gray-400 border-transparent hover:text-gray-300'
          }`}
        >
          Devices
        </button>
      </div>

      {/* Pending Users Tab */}
      {activeTab === 'pending-users' && (
        <div className="space-y-4">
          {pendingUsers.length === 0 ? (
            <p className="text-gray-400">No pending users</p>
          ) : (
            pendingUsers.map((user) => (
              <div key={user.id} className="card-border p-4 bg-dark-800 flex items-center justify-between">
                <div>
                  <p className="text-white font-semibold">{user.username}</p>
                  <p className="text-sm text-gray-400">{user.email}</p>
                  <p className="text-xs text-gray-500 mt-1">Applied: {new Date(user.created_at).toLocaleDateString()}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => approveUser(user.id)}
                    className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 transition-all"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Approve
                  </button>
                  <button
                    onClick={() => rejectUser(user.id)}
                    className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-all"
                  >
                    <XCircle className="w-4 h-4" />
                    Reject
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* All Users Tab */}
      {activeTab === 'all-users' && (
        <div className="space-y-4">
          {allUsers.map((user) => (
            <div
              key={user.id}
              className={`card-border p-4 bg-dark-800 cursor-pointer transition-all ${
                selectedUser?.id === user.id ? 'border-neon-cyan/50' : ''
              }`}
              onClick={() => {
                setSelectedUser(user)
                fetchUserDevices(user.id)
              }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-semibold">{user.username}</p>
                  <p className="text-sm text-gray-400">{user.email}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Role: <span className="text-neon-yellow">{user.role}</span>
                    {user.is_approved ? ' ✓ Approved' : ' ⏳ Pending'}
                  </p>
                </div>
              </div>

              {/* Show devices when user is selected */}
              {selectedUser?.id === user.id && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <p className="text-xs text-gray-400 mb-3">Assigned Devices:</p>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {devices.map((device) => {
                      const hasAccess = userDevices.some((d) => d.id === device.id)
                      return (
                        <div key={device.id} className="flex items-center justify-between p-2 bg-dark-700 rounded">
                          <div>
                            <p className="text-sm text-gray-300">{device.name}</p>
                            <p className="text-xs text-gray-500">{device.source}</p>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              if (hasAccess) {
                                revokePermission(user.id, device.id)
                              } else {
                                grantPermission(user.id, device.id)
                              }
                            }}
                            className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                              hasAccess
                                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                            }`}
                          >
                            {hasAccess ? 'Revoke' : 'Grant'}
                          </button>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Devices Tab */}
      {activeTab === 'devices' && (
        <div className="space-y-6">
          {/* Create New Device */}
          <div className="card-border p-6 bg-dark-800 space-y-4">
            <h3 className="text-lg font-semibold text-white">Create New Device</h3>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Device Name (e.g., Server 1)"
                value={newDevice.name}
                onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })}
                className="bg-dark-700 border border-gray-600 rounded px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-neon-cyan"
              />
              <input
                type="text"
                placeholder="Type (cpu, memory, temperature, etc)"
                value={newDevice.device_type}
                onChange={(e) => setNewDevice({ ...newDevice, device_type: e.target.value })}
                className="bg-dark-700 border border-gray-600 rounded px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-neon-cyan"
              />
              <input
                type="text"
                placeholder="Source/ID (e.g., server_1)"
                value={newDevice.source}
                onChange={(e) => setNewDevice({ ...newDevice, source: e.target.value })}
                className="bg-dark-700 border border-gray-600 rounded px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-neon-cyan col-span-2"
              />
              <input
                type="text"
                placeholder="Location (optional)"
                value={newDevice.location}
                onChange={(e) => setNewDevice({ ...newDevice, location: e.target.value })}
                className="bg-dark-700 border border-gray-600 rounded px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-neon-cyan col-span-2"
              />
              <button
                onClick={createDevice}
                className="col-span-2 flex items-center justify-center gap-2 bg-neon-cyan text-dark-900 font-semibold py-2 rounded hover:bg-neon-cyan/80 transition-all"
              >
                <Plus className="w-4 h-4" />
                Create Device
              </button>
            </div>
          </div>

          {/* Devices List */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Existing Devices ({devices.length})</h3>
            {devices.length === 0 ? (
              <p className="text-gray-400">No devices created yet</p>
            ) : (
              devices.map((device) => (
                <div key={device.id} className="card-border p-4 bg-dark-800 flex items-center justify-between">
                  <div>
                    <p className="text-white font-semibold">{device.name}</p>
                    <p className="text-sm text-gray-400">{device.device_type}</p>
                    <p className="text-xs text-gray-500 mt-1">Source: {device.source}</p>
                    {device.location && <p className="text-xs text-gray-500">Location: {device.location}</p>}
                  </div>
                  <button
                    onClick={() => deleteDevice(device.id)}
                    className="px-4 py-2 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
