import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Trash2, AlertCircle, DollarSign } from 'lucide-react'
import api from '../api'
import { useAuth } from '../context/AuthContext'

export default function AdminPanel() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('pending-users')
  const [pendingUsers, setPendingUsers] = useState([])
  const [allUsers, setAllUsers] = useState([])
  const [pendingRequests, setPendingRequests] = useState([])
  const [servers, setServers] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [processingRequest, setProcessingRequest] = useState(null)
  const [editingPrice, setEditingPrice] = useState({})
  const [updatingServer, setUpdatingServer] = useState(null)
  const [allIoTDevices, setAllIoTDevices] = useState([])
  const [userDeviceStats, setUserDeviceStats] = useState({})

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

  // Delete user
  const deleteUser = async (userId) => {
    if (!confirm('Delete this user? This action cannot be undone.')) return
    
    try {
      await api.delete(`/api/admin/users/${userId}`)
      setMessage('User deleted successfully')
      fetchAllUsers()
    } catch (error) {
      setMessage('Failed to delete user: ' + error.response?.data?.detail)
    }
  }

  // Fetch pending subscription requests
  const fetchPendingRequests = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/servers/admin/requests/pending')
      setPendingRequests(response.data.requests || [])
    } catch (error) {
      console.error('Failed to fetch pending requests:', error)
      setMessage('Failed to fetch requests: ' + error.response?.data?.detail)
    } finally {
      setLoading(false)
    }
  }

  // Fetch all servers
  const fetchAllServers = async () => {
    try {
      const response = await api.get('/api/servers/admin/servers')
      setServers(response.data.servers || [])
    } catch (error) {
      console.error('Failed to fetch servers:', error)
      setMessage('Failed to fetch servers: ' + error.response?.data?.detail)
    }
  }

  // Fetch IoT device statistics
  const fetchIoTDeviceStats = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/admin/iot-devices')
      const devices = response.data.devices || []
      setAllIoTDevices(devices)
      
      // Calculate statistics: group devices by user_id
      const stats = {}
      devices.forEach(device => {
        const userId = device.user_id
        if (!stats[userId]) {
          stats[userId] = {
            userId,
            username: device.username || `User ${userId}`,
            email: device.email || 'N/A',
            deviceCount: 0,
            devices: []
          }
        }
        stats[userId].deviceCount += 1
        stats[userId].devices.push(device)
      })
      setUserDeviceStats(stats)
    } catch (error) {
      console.error('Failed to fetch IoT device stats:', error)
      setMessage('Failed to fetch IoT device statistics: ' + error.response?.data?.detail)
    } finally {
      setLoading(false)
    }
  }

  // Update server price
  const updateServerPrice = async (serverId, newPrice) => {
    try {
      setUpdatingServer(serverId)
      const response = await api.put(`/api/servers/admin/servers/${serverId}/price`, {
        price_per_hour: parseFloat(newPrice)
      })
      setMessage(`Price updated to $${response.data.price_per_hour}/hour`)
      await fetchAllServers()
      setEditingPrice(prev => {
        const newState = { ...prev }
        delete newState[serverId]
        return newState
      })
    } catch (error) {
      setMessage('Failed to update price: ' + error.response?.data?.detail)
    } finally {
      setUpdatingServer(null)
    }
  }

  // Approve subscription request
  const approveRequest = async (requestId) => {
    try {
      setProcessingRequest(requestId)
      await api.put(`/api/servers/admin/requests/${requestId}/approve`)
      setMessage('Request approved successfully')
      fetchPendingRequests()
    } catch (error) {
      setMessage('Failed to approve request: ' + error.response?.data?.detail)
    } finally {
      setProcessingRequest(null)
    }
  }

  // Reject subscription request
  const rejectRequest = async (requestId) => {
    const reason = prompt('Enter rejection reason (optional):')
    if (reason === null) return

    try {
      setProcessingRequest(requestId)
      await api.put(`/api/servers/admin/requests/${requestId}/reject`, { reason })
      setMessage('Request rejected successfully')
      fetchPendingRequests()
    } catch (error) {
      setMessage('Failed to reject request: ' + error.response?.data?.detail)
    } finally {
      setProcessingRequest(null)
    }
  }


  // Load data on mount
  useEffect(() => {
    fetchPendingUsers()
    fetchAllUsers()
    fetchPendingRequests()
    fetchAllServers()
    fetchIoTDeviceStats()
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
        <p className="text-gray-400 mt-2">Manage users and IoT devices</p>
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
          onClick={() => setActiveTab('server-requests')}
          className={`px-4 py-2 font-semibold border-b-2 transition-all ${
            activeTab === 'server-requests'
              ? 'text-neon-cyan border-neon-cyan'
              : 'text-gray-400 border-transparent hover:text-gray-300'
          }`}
        >
          Server Requests {pendingRequests.length > 0 && `(${pendingRequests.length})`}
        </button>
        <button
          onClick={() => setActiveTab('server-management')}
          className={`px-4 py-2 font-semibold border-b-2 transition-all ${
            activeTab === 'server-management'
              ? 'text-neon-cyan border-neon-cyan'
              : 'text-gray-400 border-transparent hover:text-gray-300'
          }`}
        >
          Server Management
        </button>
        <button
          onClick={() => setActiveTab('iot-devices')}
          className={`px-4 py-2 font-semibold border-b-2 transition-all ${
            activeTab === 'iot-devices'
              ? 'text-neon-cyan border-neon-cyan'
              : 'text-gray-400 border-transparent hover:text-gray-300'
          }`}
        >
          IoT Devices ({allIoTDevices.length})
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
              className="card-border p-4 bg-dark-800 flex items-center justify-between"
            >
              <div className="flex-1">
                <p className="text-white font-semibold">{user.username}</p>
                <p className="text-sm text-gray-400">{user.email}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Role: <span className="text-neon-yellow">{user.role}</span>
                  {user.is_approved ? ' ✓ Approved' : ' ⏳ Pending'}
                </p>
              </div>
              {user.role !== 'admin' && (
                <button
                  onClick={() => deleteUser(user.id)}
                  className="ml-2 px-3 py-1 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-all"
                  title="Delete user"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Server Requests Tab */}
      {activeTab === 'server-requests' && (
        <div className="space-y-4">
          {pendingRequests.length === 0 ? (
            <p className="text-gray-400">No pending server subscription requests</p>
          ) : (
            pendingRequests.map((req) => (
              <div
                key={req.id}
                className="card-border p-4 bg-dark-800 rounded-lg border border-yellow-500/30"
              >
                <div className="mb-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-white font-semibold">
                        {req.user_name} (@{req.user_email})
                      </p>
                      <p className="text-sm text-gray-400 mt-1">
                        Requested: <strong>{req.server_name}</strong>
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Server: {req.server_specs}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Applied: {new Date(req.requested_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                      Pending
                    </span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => approveRequest(req.id)}
                    disabled={processingRequest === req.id}
                    className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 transition-all disabled:opacity-50"
                  >
                    <CheckCircle className="w-4 h-4" />
                    {processingRequest === req.id ? 'Approving...' : 'Approve'}
                  </button>
                  <button
                    onClick={() => rejectRequest(req.id)}
                    disabled={processingRequest === req.id}
                    className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-all disabled:opacity-50"
                  >
                    <XCircle className="w-4 h-4" />
                    {processingRequest === req.id ? 'Rejecting...' : 'Reject'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Server Management Tab */}
      {activeTab === 'server-management' && (
        <div className="space-y-4">
          {servers.length === 0 ? (
            <p className="text-gray-400">No servers available</p>
          ) : (
            servers.map((server) => (
              <div
                key={server.id}
                className="card-border p-4 bg-dark-800 rounded-lg border border-neon-cyan/30"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <p className="text-white font-semibold text-lg">{server.name}</p>
                    <p className="text-sm text-gray-400 mt-1">{server.specs}</p>
                    <div className="mt-3 grid grid-cols-3 gap-4">
                      <div>
                        <p className="text-xs text-gray-500">CPU Cores</p>
                        <p className="text-lg font-bold text-neon-yellow">{server.cpu_cores}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">RAM</p>
                        <p className="text-lg font-bold text-neon-cyan">{server.ram_gb}GB</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">OS</p>
                        <p className="text-lg font-bold text-neon-purple">{server.os_type}</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 ml-4">
                    <span className="text-xs bg-blue-500/20 text-blue-400 px-3 py-1 rounded">
                      {server.subscribers_count} subscriber{server.subscribers_count !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>

                {/* Price Setting */}
                <div className="border-t border-gray-700 pt-4">
                  <div className="flex items-end gap-3">
                    <div className="flex-1">
                      <label className="block text-xs text-gray-500 mb-2">Hourly Price (USD)</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={editingPrice[server.id] !== undefined ? editingPrice[server.id] : server.price_per_hour}
                        onChange={(e) =>
                          setEditingPrice(prev => ({ ...prev, [server.id]: e.target.value }))
                        }
                        className="w-full px-3 py-2 bg-dark-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-neon-cyan"
                      />
                    </div>
                    <button
                      onClick={() => updateServerPrice(server.id, editingPrice[server.id] || server.price_per_hour)}
                      disabled={updatingServer === server.id}
                      className="flex items-center gap-2 px-4 py-2 bg-neon-cyan/20 text-neon-cyan rounded hover:bg-neon-cyan/30 transition-all disabled:opacity-50 whitespace-nowrap"
                    >
                      <DollarSign className="w-4 h-4" />
                      {updatingServer === server.id ? 'Updating...' : 'Update Price'}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Current: <span className="text-neon-cyan font-semibold">${server.price_per_hour}/hour</span>
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* IoT Devices Tab */}
      {activeTab === 'iot-devices' && (
        <div className="space-y-6">
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card-border p-4 bg-dark-800 rounded-lg border border-neon-cyan/30">
              <p className="text-gray-500 text-sm uppercase tracking-widest">Total Devices</p>
              <p className="text-4xl font-bold text-neon-cyan mt-2">{allIoTDevices.length}</p>
            </div>
            <div className="card-border p-4 bg-dark-800 rounded-lg border border-neon-yellow/30">
              <p className="text-gray-500 text-sm uppercase tracking-widest">Active Users</p>
              <p className="text-4xl font-bold text-neon-yellow mt-2">{Object.keys(userDeviceStats).length}</p>
            </div>
            <div className="card-border p-4 bg-dark-800 rounded-lg border border-neon-purple/30">
              <p className="text-gray-500 text-sm uppercase tracking-widest">Avg per User</p>
              <p className="text-4xl font-bold text-neon-purple mt-2">
                {Object.keys(userDeviceStats).length > 0
                  ? (allIoTDevices.length / Object.keys(userDeviceStats).length).toFixed(1)
                  : 0}
              </p>
            </div>
          </div>

          {/* User Device Statistics Table */}
          <div className="card-border bg-dark-800 rounded-lg border border-gray-700 overflow-hidden">
            <div className="p-4 border-b border-gray-700 bg-dark-900">
              <h3 className="text-lg font-semibold text-white">Device Distribution by User</h3>
            </div>
            {Object.keys(userDeviceStats).length === 0 ? (
              <div className="p-6 text-center text-gray-400">
                <p>No IoT devices registered yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700 bg-dark-900/50">
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Username</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Email</th>
                      <th className="px-6 py-3 text-right text-xs font-semibold text-gray-400 uppercase">Device Count</th>
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Device List</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.values(userDeviceStats)
                      .sort((a, b) => b.deviceCount - a.deviceCount)
                      .map((stat) => (
                        <tr key={stat.userId} className="border-b border-gray-700 hover:bg-dark-900/50 transition-all">
                          <td className="px-6 py-3">
                            <p className="text-white font-semibold">{stat.username}</p>
                          </td>
                          <td className="px-6 py-3">
                            <p className="text-gray-400 text-sm">{stat.email}</p>
                          </td>
                          <td className="px-6 py-3 text-right">
                            <span className="inline-block px-3 py-1 bg-neon-cyan/20 text-neon-cyan rounded-full font-semibold">
                              {stat.deviceCount}
                            </span>
                          </td>
                          <td className="px-6 py-3">
                            <div className="flex gap-2 flex-wrap">
                              {stat.devices.map((device) => (
                                <span key={device.id} className="text-xs bg-gray-700/50 text-gray-300 px-2 py-1 rounded">
                                  {device.name}
                                </span>
                              ))}
                            </div>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
