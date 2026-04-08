import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Trash2 } from 'lucide-react'
import api from '../api'
import { useAuth } from '../context/AuthContext'

export default function AdminPanel() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('pending-users')
  const [pendingUsers, setPendingUsers] = useState([])
  const [allUsers, setAllUsers] = useState([])
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


  // Load data on mount
  useEffect(() => {
    fetchPendingUsers()
    fetchAllUsers()
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
    </div>
  )
}
