import { useState, useEffect } from 'react'
import { Server, Check, ShoppingCart, Zap, Cpu, Activity, X, DollarSign, AlertCircle, CheckCircle, XCircle, Edit } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useDevices } from '../context/DeviceContext'
import { useAuth } from '../context/AuthContext'
import api from '../api'

export default function ServerStore() {
  const { user } = useAuth()
  const { availableServers, myServers, fetchAvailableServers, subscribeToServer, loading } = useDevices()
  const [subscribing, setSubscribing] = useState({})
  const [localhostMetrics, setLocalhostMetrics] = useState({ cpu: null, memory: null })
  const [loadingMetrics, setLoadingMetrics] = useState(false)
  const [showChartModal, setShowChartModal] = useState(false)
  const [chartData, setChartData] = useState([])
  const [chartLoading, setChartLoading] = useState(false)
  const [cpuStats, setCpuStats] = useState({ average: 0, min: 0, max: 0 })
  const [memoryStats, setMemoryStats] = useState({ average: 0, min: 0, max: 0 })
  const [userRequests, setUserRequests] = useState([])
  const [requestsLoading, setRequestsLoading] = useState(false)
  
  // Admin state
  const [allServers, setAllServers] = useState([])
  const [pendingRequests, setPendingRequests] = useState([])
  const [editingPrice, setEditingPrice] = useState({})
  const [updatingServer, setUpdatingServer] = useState(null)
  const [showRequestsModal, setShowRequestsModal] = useState(false)
  const [selectedServerForRequests, setSelectedServerForRequests] = useState(null)
  const [processingRequest, setProcessingRequest] = useState(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedServerForEdit, setSelectedServerForEdit] = useState(null)
  const [editFormData, setEditFormData] = useState({})
  const [creatingLocalhostServer, setCreatingLocalhostServer] = useState(false)
  const [systemInfo, setSystemInfo] = useState({ cpu_cores: 0, ram_gb: 0, os_type: '' })
  const [loadingSystemInfo, setLoadingSystemInfo] = useState(false)
  const [showServerChartModal, setShowServerChartModal] = useState(false)
  const [selectedServerForChart, setSelectedServerForChart] = useState(null)
  const [serverChartData, setServerChartData] = useState([])
  const [serverChartLoading, setServerChartLoading] = useState(false)
  const [serverCpuStats, setServerCpuStats] = useState({ average: 0, min: 0, max: 0 })
  const [serverMemoryStats, setServerMemoryStats] = useState({ average: 0, min: 0, max: 0 })

  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    if (isAdmin) {
      fetchAllServers()
      fetchPendingRequests()
      fetchSystemInfo() // Fetch system info when admin view loads
    } else {
      fetchAvailableServers()
      fetchUserRequests()
    }
  }, [isAdmin])

  useEffect(() => {
    if (!isAdmin) return

    const interval = setInterval(() => {
      fetchPendingRequests()
    }, 5000)

    return () => clearInterval(interval)
  }, [isAdmin])

  // Fetch localhost metrics every 5 seconds
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoadingMetrics(true)
        const response = await api.get('/api/metrics/latest')
        if (response.data) {
          setLocalhostMetrics({
            cpu: response.data.latest_cpu,
            memory: response.data.latest_memory
          })
        }
      } catch (err) {
        console.error('Failed to fetch metrics:', err)
      } finally {
        setLoadingMetrics(false)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000)
    return () => clearInterval(interval)
  }, [])

  // Fetch chart data for localhost (past 2 hours = 120 minutes)
  const handleOpenChart = async () => {
    setShowChartModal(true)
    setChartLoading(true)
    try {
      // Fetch both CPU and Memory history
      const [cpuRes, memoryRes] = await Promise.all([
        api.get('/api/metrics/history', { params: { metric_type: 'cpu', minutes: 120 } }),
        api.get('/api/metrics/history', { params: { metric_type: 'memory', minutes: 120 } })
      ])

      // Transform and merge data
      const cpuData = cpuRes.data.data || []
      const memoryData = memoryRes.data.data || []

      // Create map for quick lookup
      const cpuMap = {}
      cpuData.forEach(item => {
        const time = new Date(item.timestamp)
        const key = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        cpuMap[key] = item.value
      })

      const memoryMap = {}
      memoryData.forEach(item => {
        const time = new Date(item.timestamp)
        const key = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        memoryMap[key] = item.value
      })

      // Merge all timestamps and create chart data
      const allTimestamps = new Set([...Object.keys(cpuMap), ...Object.keys(memoryMap)])
      const mergedData = Array.from(allTimestamps)
        .sort()
        .map(time => ({
          time,
          cpu: cpuMap[time] || null,
          memory: memoryMap[time] || null
        }))

      // Calculate statistics for CPU
      const cpuValues = cpuData.map(d => d.value)
      if (cpuValues.length > 0) {
        const avgCpu = cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length
        setCpuStats({
          average: parseFloat(avgCpu.toFixed(2)),
          min: parseFloat(Math.min(...cpuValues).toFixed(2)),
          max: parseFloat(Math.max(...cpuValues).toFixed(2))
        })
      }

      // Calculate statistics for Memory
      const memoryValues = memoryData.map(d => d.value)
      if (memoryValues.length > 0) {
        const avgMemory = memoryValues.reduce((a, b) => a + b, 0) / memoryValues.length
        setMemoryStats({
          average: parseFloat(avgMemory.toFixed(2)),
          min: parseFloat(Math.min(...memoryValues).toFixed(2)),
          max: parseFloat(Math.max(...memoryValues).toFixed(2))
        })
      }

      setChartData(mergedData)
    } catch (err) {
      console.error('Failed to fetch chart data:', err)
      setChartData([])
      setCpuStats({ average: 0, min: 0, max: 0 })
      setMemoryStats({ average: 0, min: 0, max: 0 })
    } finally {
      setChartLoading(false)
    }
  }

  const handleCloseChart = () => {
    setShowChartModal(false)
    setChartData([])
    setCpuStats({ average: 0, min: 0, max: 0 })
    setMemoryStats({ average: 0, min: 0, max: 0 })
  }

  // ===== ADMIN FUNCTIONS =====
  const fetchAllServers = async () => {
    try {
      const response = await api.get('/api/servers/admin/servers')
      setAllServers(response.data.servers || [])
    } catch (err) {
      console.error('Failed to fetch servers:', err)
    }
  }

  const fetchPendingRequests = async () => {
    try {
      const response = await api.get('/api/servers/admin/requests/pending')
      setPendingRequests(response.data.requests || [])
    } catch (err) {
      console.error('Failed to fetch pending requests:', err)
    }
  }

  const getRequestsForServer = (serverId) => {
    return pendingRequests.filter(r => r.server_id === serverId)
  }

  const updateServerPrice = async (serverId, newPrice) => {
    try {
      setUpdatingServer(serverId)
      await api.put(`/api/servers/admin/servers/${serverId}/price`, {
        price_per_hour: parseFloat(newPrice)
      })
      await fetchAllServers()
      setEditingPrice(prev => {
        const newState = { ...prev }
        delete newState[serverId]
        return newState
      })
      alert(`Price updated to $${newPrice}/hour`)
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message))
    } finally {
      setUpdatingServer(null)
    }
  }

  const approveRequest = async (requestId) => {
    try {
      setProcessingRequest(requestId)
      await api.put(`/api/servers/admin/requests/${requestId}/approve`)
      await fetchPendingRequests()
      alert('Request approved!')
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message))
    } finally {
      setProcessingRequest(null)
    }
  }

  const rejectRequest = async (requestId) => {
    const reason = prompt('Enter rejection reason (optional):')
    if (reason === null) return

    try {
      setProcessingRequest(requestId)
      await api.put(`/api/servers/admin/requests/${requestId}/reject`, { reason })
      await fetchPendingRequests()
      alert('Request rejected!')
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message))
    } finally {
      setProcessingRequest(null)
    }
  }

  // ===== SERVER EDIT FUNCTIONS =====
  const fetchSystemInfo = async () => {
    try {
      setLoadingSystemInfo(true)
      const response = await api.get('/api/servers/admin/system-info')
      setSystemInfo(response.data)
    } catch (err) {
      console.error('Failed to fetch system info:', err)
      setSystemInfo({ cpu_cores: 0, ram_gb: 0, os_type: '' })
    } finally {
      setLoadingSystemInfo(false)
    }
  }

  const openEditModal = (server) => {
    setSelectedServerForEdit(server)
    setEditFormData({
      name: server.name,
      specs: server.specs,
      price_per_month: (server.price_per_hour || 0) * 730, // Convert hourly to monthly
      cpu_cores: server.cpu_cores || 0,
      ram_gb: server.ram_gb || 0,
      os_type: server.os_type || ''
    })
    setShowEditModal(true)
    // Fetch system info in background (no await)
    fetchSystemInfo()
  }

  const closeEditModal = () => {
    setShowEditModal(false)
    setSelectedServerForEdit(null)
    setEditFormData({})
    // Don't clear systemInfo - it's needed for server card display
  }

  const saveServerEdit = async () => {
    if (!selectedServerForEdit) return

    try {
      setUpdatingServer(selectedServerForEdit.id)

      // Convert monthly price back to hourly for API
      const monthlyPrice = Number(editFormData.price_per_month ?? 0)
      const pricePerHour = Number.isFinite(monthlyPrice) ? monthlyPrice / 730 : 0

      const dataToSend = {
        name: editFormData.name,
        specs: editFormData.specs,
        price_per_hour: pricePerHour
      }

      await api.patch(`/api/servers/admin/servers/${selectedServerForEdit.id}`, dataToSend)
      alert('Server updated successfully!')
      await fetchAllServers()
      closeEditModal()
    } catch (err) {
      console.error('Update error:', err)
      alert('Error: ' + (err.response?.data?.detail || err.message))
    } finally {
      setUpdatingServer(null)
    }
  }

  // ===== SERVER CHART FUNCTIONS =====
  const fetchServerChart = async (serverId, serverName) => {
    setShowServerChartModal(true)
    setServerChartLoading(true)
    try {
      const [cpuRes, memoryRes] = await Promise.all([
        api.get('/api/metrics/history', { params: { metric_type: 'cpu', minutes: 120, server_id: serverId } }),
        api.get('/api/metrics/history', { params: { metric_type: 'memory', minutes: 120, server_id: serverId } })
      ])

      const cpuData = cpuRes.data.data || []
      const memoryData = memoryRes.data.data || []

      const cpuMap = {}
      cpuData.forEach(item => {
        const time = new Date(item.timestamp)
        const key = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        cpuMap[key] = item.value
      })

      const memoryMap = {}
      memoryData.forEach(item => {
        const time = new Date(item.timestamp)
        const key = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        memoryMap[key] = item.value
      })

      const allTimestamps = new Set([...Object.keys(cpuMap), ...Object.keys(memoryMap)])
      const mergedData = Array.from(allTimestamps)
        .sort()
        .map(time => ({
          time,
          cpu: cpuMap[time] || null,
          memory: memoryMap[time] || null
        }))

      const cpuValues = cpuData.map(d => d.value)
      if (cpuValues.length > 0) {
        const avgCpu = cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length
        setServerCpuStats({
          average: parseFloat(avgCpu.toFixed(2)),
          min: parseFloat(Math.min(...cpuValues).toFixed(2)),
          max: parseFloat(Math.max(...cpuValues).toFixed(2))
        })
      }

      const memoryValues = memoryData.map(d => d.value)
      if (memoryValues.length > 0) {
        const avgMemory = memoryValues.reduce((a, b) => a + b, 0) / memoryValues.length
        setServerMemoryStats({
          average: parseFloat(avgMemory.toFixed(2)),
          min: parseFloat(Math.min(...memoryValues).toFixed(2)),
          max: parseFloat(Math.max(...memoryValues).toFixed(2))
        })
      }

      setServerChartData(mergedData)
      setSelectedServerForChart(serverName)
    } catch (err) {
      console.error('Failed to fetch chart data:', err)
      setServerChartData([])
      setServerCpuStats({ average: 0, min: 0, max: 0 })
      setServerMemoryStats({ average: 0, min: 0, max: 0 })
    } finally {
      setServerChartLoading(false)
    }
  }

  const closeServerChartModal = () => {
    setShowServerChartModal(false)
    setSelectedServerForChart(null)
    setServerChartData([])
    setServerCpuStats({ average: 0, min: 0, max: 0 })
    setServerMemoryStats({ average: 0, min: 0, max: 0 })
  }

  // ===== USER FUNCTIONS =====
  const fetchUserRequests = async () => {
    try {
      setRequestsLoading(true)
      const response = await api.get('/api/servers/requests')
      if (response.data && response.data.requests) {
        setUserRequests(response.data.requests)
      }
    } catch (err) {
      console.error('Failed to fetch user requests:', err)
    } finally {
      setRequestsLoading(false)
    }
  }

  const handleRequestSubscription = async (serverId) => {
    try {
      setSubscribing(prev => ({ ...prev, [serverId]: true }))
      const response = await api.post('/api/servers/requests', null, {
        params: { server_id: serverId }
      })
      if (response.data) {
        alert('Subscription request sent! Please wait for admin approval.')
        await fetchUserRequests()
      }
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSubscribing(prev => ({ ...prev, [serverId]: false }))
    }
  }

  const getRequestStatus = (serverId) => {
    const request = userRequests.find(r => r.server_id === serverId)
    return request
  }

  const isSubscribed = (serverId) => {
    return myServers.some(s => s.id === serverId)
  }

  const handleSubscribe = async (serverId) => {
    try {
      setSubscribing(prev => ({ ...prev, [serverId]: true }))
      await handleRequestSubscription(serverId)
    } catch (err) {
      alert('Error: ' + err.message)
    } finally {
      setSubscribing(prev => ({ ...prev, [serverId]: false }))
    }
  }

  const getServerColor = (index) => {
    const colors = ['neon-cyan', 'neon-green', 'neon-purple', 'neon-orange']
    return colors[index % colors.length]
  }

  const ServerCard = ({ server, index }) => {
    const color = getServerColor(index)
    const subscribed = isSubscribed(server.id)
    const request = getRequestStatus(server.id)

    const getButtonState = () => {
      if (subscribed) {
        return { disabled: true, text: 'Subscribed', status: 'subscribed', icon: Check }
      }
      if (request) {
        if (request.status === 'pending') {
          return { disabled: true, text: 'Request Pending', status: 'pending', icon: Activity }
        }
        if (request.status === 'approved') {
          return { disabled: true, text: 'Approved', status: 'approved', icon: Check }
        }
        if (request.status === 'rejected') {
          return { disabled: false, text: 'Resubmit Request', status: 'rejected', icon: ShoppingCart }
        }
      }
      return { disabled: subscribing[server.id] || loading, text: 'Request Subscription', status: 'idle', icon: ShoppingCart }
    }

    const buttonState = getButtonState()
    const ButtonIcon = buttonState.icon

    return (
      <div className={`bg-dark-800 border border-${color}/30 rounded-xl p-6 hover:border-${color}/60 transition-all flex flex-col`}>
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className={`text-xl font-bold text-${color} mb-2`}>{server.name}</h3>
            <p className="text-gray-400 text-sm">{server.specs}</p>
          </div>
          {subscribed && (
            <span className="flex items-center gap-1 text-xs bg-green-500/20 text-green-400 px-3 py-1 rounded-full">
              <Check className="w-3 h-3" />
              Subscribed
            </span>
          )}
          {request && request.status === 'pending' && (
            <span className="flex items-center gap-1 text-xs bg-yellow-500/20 text-yellow-400 px-3 py-1 rounded-full">
              <Activity className="w-3 h-3" />
              Pending
            </span>
          )}
          {request && request.status === 'rejected' && (
            <span className="flex items-center gap-1 text-xs bg-red-500/20 text-red-400 px-3 py-1 rounded-full">
              <X className="w-3 h-3" />
              Rejected
            </span>
          )}
        </div>

        {/* Show rejection reason if exists */}
        {request && request.status === 'rejected' && request.rejection_reason && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4">
            <p className="text-xs text-red-300"><strong>Reason:</strong> {request.rejection_reason}</p>
          </div>
        )}

        {/* Specs */}
        <div className="space-y-3 mb-6 flex-1">
          {server.cpu_cores && (
            <div className="flex items-center gap-3 p-3 bg-dark-900 rounded-lg">
              <Zap className="w-5 h-5 text-neon-yellow opacity-70" />
              <div>
                <p className="text-xs text-gray-500">CPU Cores</p>
                <p className="text-lg font-bold text-white">{server.cpu_cores}</p>
              </div>
            </div>
          )}

          {server.ram_gb && (
            <div className="flex items-center gap-3 p-3 bg-dark-900 rounded-lg">
              <Server className="w-5 h-5 text-neon-cyan opacity-70" />
              <div>
                <p className="text-xs text-gray-500">Memory</p>
                <p className="text-lg font-bold text-white">{server.ram_gb}GB RAM</p>
              </div>
            </div>
          )}

          {server.os_type && (
            <div className="flex items-center gap-3 p-3 bg-dark-900 rounded-lg">
              <Server className="w-5 h-5 text-neon-purple opacity-70" />
              <div>
                <p className="text-xs text-gray-500">Operating System</p>
                <p className="text-lg font-bold text-white">{server.os_type}</p>
              </div>
            </div>
          )}
        </div>

        {/* Pricing & Button */}
        <div className="border-t border-gray-700 pt-4">
          {server.price_per_hour ? (
            <div className="mb-4">
              <p className="text-sm text-gray-500 mb-1">Monthly Price</p>
              <p className="text-2xl font-bold text-white">
                ${(server.price_per_hour * 730).toFixed(2)}
                <span className="text-sm text-gray-400 font-normal">/month</span>
              </p>
            </div>
          ) : (
            <div className="mb-4">
              <p className="text-sm text-gray-500 mb-1">Status</p>
              <p className={`text-lg font-bold text-${color}`}>Free to Monitor</p>
            </div>
          )}

          <button
            onClick={() => handleSubscribe(server.id)}
            disabled={buttonState.disabled}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-all font-semibold ${
              buttonState.status === 'subscribed'
                ? 'bg-green-500/20 text-green-400 border border-green-500/40 cursor-not-allowed'
                : buttonState.status === 'pending'
                ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40 cursor-not-allowed'
                : buttonState.status === 'rejected'
                ? `bg-${color}/20 text-${color} border border-${color}/40 hover:border-${color}`
                : `bg-${color}/20 text-${color} border border-${color}/40 hover:border-${color} disabled:opacity-50`
            }`}
          >
            <ButtonIcon className="w-5 h-5" />
            {subscribing[server.id] ? 'Processing...' : buttonState.text}
          </button>
        </div>
      </div>
    )
  }

  const matchedLocalhostServer = allServers.find((server) => {
    const name = (server.name || '').toLowerCase()
    const specs = (server.specs || '').toLowerCase()
    return (
      specs.includes('system server') ||
      specs.includes('metrics only') ||
      name === 'server 1' ||
      name.includes('localhost') ||
      name.includes('local')
    )
  })

  const matchedBySystemFingerprint = allServers.find((server) => {
    if (!systemInfo.cpu_cores || !systemInfo.ram_gb || !systemInfo.os_type) {
      return false
    }

    const sameCpu = Number(server.cpu_cores || 0) === Number(systemInfo.cpu_cores || 0)
    const sameOs = (server.os_type || '').toLowerCase() === (systemInfo.os_type || '').toLowerCase()
    const ramDiff = Math.abs(Number(server.ram_gb || 0) - Number(systemInfo.ram_gb || 0))

    return sameCpu && sameOs && ramDiff <= 1
  })

  const firstServerById = [...allServers].sort((a, b) => a.id - b.id)[0] || null
  const localhostServer = matchedLocalhostServer || matchedBySystemFingerprint || firstServerById

  const nonLocalServers = localhostServer
    ? allServers.filter((server) => server.id !== localhostServer.id)
    : allServers

  const localhostRequests = localhostServer ? getRequestsForServer(localhostServer.id) : []

  const handleLocalhostEdit = async (e) => {
    e.stopPropagation()

    if (localhostServer) {
      openEditModal(localhostServer)
      return
    }

    try {
      setCreatingLocalhostServer(true)

      const response = await api.post('/api/servers/admin/servers', null, {
        params: {
          name: 'Server 1',
          specs: 'System Server - Metrics Only',
          cpu_cores: Number(systemInfo.cpu_cores) || 1,
          ram_gb: Math.max(1, Math.round(Number(systemInfo.ram_gb) || 1)),
          os_type: systemInfo.os_type || 'Localhost',
          price_per_hour: 0
        }
      })

      const createdServer = response.data
      await fetchAllServers()
      openEditModal(createdServer)
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message))
    } finally {
      setCreatingLocalhostServer(false)
    }
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">
          {isAdmin ? 'Server Management' : 'Server Store'}
        </h1>
        <p className="text-gray-400">
          {isAdmin ? 'Manage servers, set prices, and review subscription requests' : 'Browse and subscribe to available servers for monitoring'}
        </p>
      </div>

      {/* ADMIN VIEW */}
      {isAdmin ? (
        <>
          {/* Admin Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-6">
              <p className="text-gray-400 text-sm mb-2">Total Servers</p>
              <p className="text-3xl font-bold text-neon-cyan">{allServers.length}</p>
            </div>
            <div className="bg-dark-800 border border-neon-green/20 rounded-xl p-6">
              <p className="text-gray-400 text-sm mb-2">Pending Requests</p>
              <p className="text-3xl font-bold text-neon-green">{pendingRequests.length}</p>
            </div>
            <div className="bg-dark-800 border border-neon-purple/20 rounded-xl p-6">
              <p className="text-gray-400 text-sm mb-2">Total Subscribers</p>
              <p className="text-3xl font-bold text-neon-purple">
                {allServers.reduce((sum, s) => sum + (s.subscribers_count || 0), 0)}
              </p>
            </div>
          </div>

          {/* Servers Grid - Admin */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Your Servers</h2>
            
            {/* Localhost Server Card for Admin */}
            <div 
              onClick={() => fetchServerChart(localhostServer?.id || 1, localhostServer?.name || 'Server 1')}
              className="mb-6 bg-dark-800 border border-neon-cyan/30 rounded-xl p-6 hover:border-neon-cyan/60 hover:cursor-pointer transition-all hover:bg-dark-700 relative"
            >
              {/* Edit Button - Top Right Corner */}
              <button
                onClick={handleLocalhostEdit}
                disabled={creatingLocalhostServer}
                className="absolute top-6 right-6 flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 text-blue-400 border border-blue-500/40 rounded-lg hover:bg-blue-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Edit className="w-4 h-4" />
                {creatingLocalhostServer ? 'Creating...' : 'Edit'}
              </button>

              <div className="flex items-start justify-between mb-4 pr-24">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-white">{localhostServer?.name || 'Server 1'}</h3>
                    <span className="text-xs text-neon-cyan bg-neon-cyan/20 px-2 py-1 rounded">
                      Localhost
                    </span>
                  </div>
                  <p className="text-sm text-gray-400 mb-3">{localhostServer?.specs || 'System Server - Metrics Only'}</p>

                  {/* System Info Display */}
                  <div className="grid grid-cols-3 gap-3 mb-4">
                    <div>
                      <p className="text-xs text-gray-500">CPU Cores</p>
                      <p className="text-lg font-bold text-neon-yellow">{systemInfo.cpu_cores || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">RAM</p>
                      <p className="text-lg font-bold text-neon-cyan">{systemInfo.ram_gb}GB</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">OS</p>
                      <p className="text-lg font-bold text-neon-purple">{systemInfo.os_type}</p>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500 mb-1">Monthly Price</p>
                  <p className="text-xl font-bold text-neon-yellow">
                    ${localhostServer ? (localhostServer.price_per_hour * 730).toFixed(2) : '0.00'}
                  </p>
                </div>
              </div>

              {/* Localhost Metrics Display */}
              <div className="bg-dark-900/50 rounded-lg p-4 mb-4 border border-neon-cyan/20 space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs text-gray-400">CPU Usage</p>
                    <span className="text-sm font-bold text-neon-yellow">
                      {localhostMetrics.cpu !== null ? `${localhostMetrics.cpu.toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-dark-800 rounded-full h-1.5">
                    <div
                      className="bg-neon-yellow h-1.5 rounded-full transition-all"
                      style={{ width: `${localhostMetrics.cpu || 0}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs text-gray-400">Memory Usage</p>
                    <span className="text-sm font-bold text-neon-cyan">
                      {localhostMetrics.memory !== null ? `${localhostMetrics.memory.toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-dark-800 rounded-full h-1.5">
                    <div
                      className="bg-neon-cyan h-1.5 rounded-full transition-all"
                      style={{ width: `${localhostMetrics.memory || 0}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {localhostRequests.length > 0 && localhostServer && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedServerForRequests(localhostServer)
                    setShowRequestsModal(true)
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 text-yellow-400 border border-yellow-500/40 rounded-lg hover:bg-yellow-500/30 transition-all whitespace-nowrap"
                >
                  <AlertCircle className="w-5 h-5" />
                  {localhostRequests.length} Request{localhostRequests.length !== 1 ? 's' : ''}
                </button>
              )}
            </div>

            {nonLocalServers.length === 0 ? (
              <p className="text-gray-400">No other servers available</p>
            ) : (
              <div className="space-y-4">
                {nonLocalServers.map((server) => {
                  const serverRequests = getRequestsForServer(server.id)

                  return (
                    <div
                      key={server.id}
                      onClick={() => fetchServerChart(server.id, server.name)}
                      className="bg-dark-800 border border-neon-cyan/30 rounded-xl p-6 hover:border-neon-cyan/60 hover:cursor-pointer transition-all hover:bg-dark-700 relative"
                    >
                      {/* Edit Button - Top Right Corner */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          openEditModal(server)
                        }}
                        className="absolute top-6 right-6 flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 text-blue-400 border border-blue-500/40 rounded-lg hover:bg-blue-500/30 transition-all"
                      >
                        <Edit className="w-4 h-4" />
                        Edit
                      </button>

                      <div className="flex items-start justify-between mb-4 pr-24">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-bold text-white">{server.name}</h3>
                          </div>
                          <p className="text-sm text-gray-400 mb-3">{server.specs}</p>

                          {/* Server Info Grid */}
                          <div className="grid grid-cols-4 gap-3 mb-4">
                            <div>
                              <p className="text-xs text-gray-500">CPU Cores</p>
                              <p className="text-lg font-bold text-neon-yellow">{systemInfo.cpu_cores || 0}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">RAM</p>
                              <p className="text-lg font-bold text-neon-cyan">{systemInfo.ram_gb}GB</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">OS</p>
                              <p className="text-lg font-bold text-neon-purple">{systemInfo.os_type}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">Subscribers</p>
                              <p className="text-lg font-bold text-neon-green">{server.subscribers_count}</p>
                            </div>
                          </div>
                        </div>

                        {/* Price Display on Right */}
                        <div className="text-right">
                          <p className="text-xs text-gray-500 mb-1">Monthly Price</p>
                          <p className="text-xl font-bold text-neon-yellow">${(server.price_per_hour * 730).toFixed(2)}</p>
                        </div>
                      </div>

                      {/* Request Badge */}
                      {serverRequests.length > 0 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedServerForRequests(server)
                            setShowRequestsModal(true)
                          }}
                          className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 text-yellow-400 border border-yellow-500/40 rounded-lg hover:bg-yellow-500/30 transition-all whitespace-nowrap"
                        >
                          <AlertCircle className="w-5 h-5" />
                          {serverRequests.length} Request{serverRequests.length !== 1 ? 's' : ''}
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Requests Modal */}
          {showRequestsModal && selectedServerForRequests && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
              <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8 max-w-2xl w-full">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">
                      Requests for {selectedServerForRequests.name}
                    </h3>
                    <p className="text-sm text-gray-400">
                      {getRequestsForServer(selectedServerForRequests.id).length} pending request(s)
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setShowRequestsModal(false)
                      setSelectedServerForRequests(null)
                    }}
                    className="p-2 hover:bg-dark-700 rounded-lg transition-all"
                  >
                    <X className="w-6 h-6 text-gray-400" />
                  </button>
                </div>

                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {getRequestsForServer(selectedServerForRequests.id).map((req) => (
                    <div
                      key={req.id}
                      className="bg-dark-900/50 border border-yellow-500/30 rounded-lg p-4"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <p className="text-white font-semibold">{req.user_name}</p>
                          <p className="text-xs text-gray-400">{req.user_email}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            Requested: {new Date(req.requested_at).toLocaleDateString()}
                          </p>
                        </div>
                        <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                          Pending
                        </span>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => approveRequest(req.id)}
                          disabled={processingRequest === req.id}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 transition-all disabled:opacity-50 text-sm"
                        >
                          <CheckCircle className="w-4 h-4" />
                          {processingRequest === req.id ? 'Approving...' : 'Approve'}
                        </button>
                        <button
                          onClick={() => rejectRequest(req.id)}
                          disabled={processingRequest === req.id}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-all disabled:opacity-50 text-sm"
                        >
                          <XCircle className="w-4 h-4" />
                          {processingRequest === req.id ? 'Rejecting...' : 'Reject'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex gap-3 pt-6 border-t border-gray-700">
                  <button
                    onClick={() => {
                      setShowRequestsModal(false)
                      setSelectedServerForRequests(null)
                    }}
                    className="flex-1 px-4 py-2 bg-gray-700/20 text-gray-300 rounded hover:bg-gray-700/40 transition-all"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Edit Server Modal */}
          {showEditModal && selectedServerForEdit && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
              <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8 max-w-2xl w-full">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-2xl font-bold text-white">Edit Server</h3>
                  <button
                    onClick={closeEditModal}
                    className="p-2 hover:bg-dark-700 rounded-lg transition-all"
                  >
                    <X className="w-6 h-6 text-gray-400" />
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Server Name</label>
                    <input
                      type="text"
                      value={editFormData.name || ''}
                      onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                      className="w-full px-4 py-2 bg-dark-900 border border-gray-700 rounded text-white focus:outline-none focus:border-neon-cyan"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Specifications</label>
                    <input
                      type="text"
                      value={editFormData.specs || ''}
                      onChange={(e) => setEditFormData({ ...editFormData, specs: e.target.value })}
                      className="w-full px-4 py-2 bg-dark-900 border border-gray-700 rounded text-white focus:outline-none focus:border-neon-cyan"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Price per Month (USD)</label>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={editFormData.price_per_month || 0}
                      onChange={(e) => setEditFormData({ ...editFormData, price_per_month: parseFloat(e.target.value) })}
                      className="w-full px-4 py-2 bg-dark-900 border border-gray-700 rounded text-white focus:outline-none focus:border-neon-cyan"
                    />
                  </div>

                  {loadingSystemInfo ? (
                    <div className="text-center py-4">
                      <p className="text-gray-400">Loading system information...</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-3 gap-4 bg-dark-900 p-4 rounded-lg border border-gray-700">
                      <div>
                        <label className="block text-xs text-gray-500 mb-2">CPU Cores</label>
                        <p className="text-xl font-bold text-neon-yellow">{systemInfo.cpu_cores}</p>
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-2">RAM (GB)</label>
                        <p className="text-xl font-bold text-neon-cyan">{systemInfo.ram_gb}</p>
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-2">OS Type</label>
                        <p className="text-xl font-bold text-neon-purple">{systemInfo.os_type}</p>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex gap-3 pt-6 border-t border-gray-700">
                  <button
                    onClick={closeEditModal}
                    className="flex-1 px-4 py-2 bg-gray-700/20 text-gray-300 rounded hover:bg-gray-700/40 transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveServerEdit}
                    disabled={updatingServer === selectedServerForEdit?.id}
                    className="flex-1 px-4 py-2 bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 rounded hover:bg-neon-cyan/30 transition-all disabled:opacity-50"
                  >
                    {updatingServer === selectedServerForEdit?.id ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Server Chart Modal */}
          {showServerChartModal && selectedServerForChart && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
              <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8 max-w-4xl w-full mx-4">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">{selectedServerForChart}</h3>
                    <p className="text-sm text-gray-400">Last 2 hours of system metrics</p>
                  </div>
                  <button
                    onClick={closeServerChartModal}
                    className="p-2 hover:bg-dark-700 rounded-lg transition-all"
                  >
                    <X className="w-6 h-6 text-gray-400" />
                  </button>
                </div>

                {serverChartLoading ? (
                  <div className="flex items-center justify-center h-96">
                    <p className="text-gray-400">Loading chart data...</p>
                  </div>
                ) : serverChartData.length > 0 ? (
                  <div className="space-y-6">
                    {/* CPU Statistics */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-dark-900/50 border border-neon-yellow/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">CPU Average</p>
                        <p className="text-2xl font-bold text-neon-yellow">
                          {serverCpuStats.average}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                      <div className="bg-dark-900/50 border border-neon-green/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">CPU Minimum</p>
                        <p className="text-2xl font-bold text-neon-green">
                          {serverCpuStats.min}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                      <div className="bg-dark-900/50 border border-neon-orange/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">CPU Maximum</p>
                        <p className="text-2xl font-bold text-neon-orange">
                          {serverCpuStats.max}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                    </div>

                    {/* Memory Statistics */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-dark-900/50 border border-neon-cyan/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">Memory Average</p>
                        <p className="text-2xl font-bold text-neon-cyan">
                          {serverMemoryStats.average}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                      <div className="bg-dark-900/50 border border-neon-green/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">Memory Minimum</p>
                        <p className="text-2xl font-bold text-neon-green">
                          {serverMemoryStats.min}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                      <div className="bg-dark-900/50 border border-neon-orange/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">Memory Maximum</p>
                        <p className="text-2xl font-bold text-neon-orange">
                          {serverMemoryStats.max}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                    </div>

                    {/* Chart */}
                    <div className="bg-dark-900/50 rounded-lg p-6 border border-gray-700">
                      <ResponsiveContainer width="100%" height={400}>
                        <LineChart data={serverChartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                          <XAxis
                            dataKey="time"
                            stroke="#9CA3AF"
                            tick={{ fontSize: 12 }}
                          />
                          <YAxis
                            stroke="#9CA3AF"
                            tick={{ fontSize: 12 }}
                            label={{ value: '%', angle: -90, position: 'insideLeft' }}
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
                            dataKey="cpu"
                            stroke="#ffd700"
                            dot={false}
                            strokeWidth={2}
                            name="CPU %"
                          />
                          <Line
                            type="monotone"
                            dataKey="memory"
                            stroke="#00d4ff"
                            dot={false}
                            strokeWidth={2}
                            name="Memory %"
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
                    onClick={closeServerChartModal}
                    className="flex-1 px-4 py-2 bg-gray-700/20 text-gray-300 rounded hover:bg-gray-700/40 transition-all"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        /* USER VIEW */
        <>
          {/* User Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-6">
              <p className="text-gray-400 text-sm mb-2">Available Servers</p>
              <p className="text-3xl font-bold text-neon-cyan">{availableServers.length}</p>
            </div>
            <div className="bg-dark-800 border border-neon-green/20 rounded-xl p-6">
              <p className="text-gray-400 text-sm mb-2">My Subscriptions</p>
              <p className="text-3xl font-bold text-neon-green">{myServers.length}</p>
            </div>
            <div className="bg-dark-800 border border-neon-purple/20 rounded-xl p-6">
              <p className="text-gray-400 text-sm mb-2">Monthly Cost</p>
              <p className="text-3xl font-bold text-neon-purple">
                ${(myServers.reduce((sum, s) => sum + (s.price_per_hour || 0) * 730, 0)).toFixed(2)}
              </p>
            </div>
          </div>

          {/* Servers Grid */}
          {loading ? (
            <div className="text-center py-16">
              <p className="text-gray-400">Loading servers...</p>
            </div>
          ) : availableServers.length === 0 ? (
            <div className="text-center py-16">
              <Server className="w-16 h-16 text-gray-600 mx-auto mb-4 opacity-50" />
              <h3 className="text-xl font-semibold text-white mb-2">No Servers Available</h3>
              <p className="text-gray-400">Contact admin to add servers</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {availableServers.map((server, idx) => (
                <ServerCard key={server.id} server={server} index={idx} />
              ))}
            </div>
          )}

          {/* Chart Modal */}
          {showChartModal && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
              <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8 max-w-4xl w-full mx-4">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">Server 1</h3>
                    <p className="text-sm text-gray-400">Last 2 hours of system metrics</p>
                  </div>
                  <button
                    onClick={() => handleCloseChart()}
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
                    {/* CPU Statistics */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-dark-900/50 border border-neon-yellow/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">CPU Average</p>
                        <p className="text-2xl font-bold text-neon-yellow">
                          {cpuStats.average}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                      <div className="bg-dark-900/50 border border-neon-green/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">CPU Minimum</p>
                        <p className="text-2xl font-bold text-neon-green">
                          {cpuStats.min}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                      <div className="bg-dark-900/50 border border-neon-orange/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">CPU Maximum</p>
                        <p className="text-2xl font-bold text-neon-orange">
                          {cpuStats.max}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                    </div>

                    {/* Memory Statistics */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-dark-900/50 border border-neon-cyan/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">Memory Average</p>
                        <p className="text-2xl font-bold text-neon-cyan">
                          {memoryStats.average}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                      <div className="bg-dark-900/50 border border-neon-green/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">Memory Minimum</p>
                        <p className="text-2xl font-bold text-neon-green">
                          {memoryStats.min}
                          <span className="text-sm text-gray-400 ml-1">%</span>
                        </p>
                      </div>
                      <div className="bg-dark-900/50 border border-neon-orange/30 rounded-lg p-4">
                        <p className="text-xs text-gray-400 mb-2">Memory Maximum</p>
                        <p className="text-2xl font-bold text-neon-orange">
                          {memoryStats.max}
                          <span className="text-sm text-gray-400 ml-1">%</span>
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
                            label={{ value: '%', angle: -90, position: 'insideLeft' }}
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
                            dataKey="cpu"
                            stroke="#ffd700"
                            dot={false}
                            strokeWidth={2}
                            name="CPU %"
                          />
                          <Line
                            type="monotone"
                            dataKey="memory"
                            stroke="#00d4ff"
                            dot={false}
                            strokeWidth={2}
                            name="Memory %"
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
                    onClick={() => handleCloseChart()}
                    className="flex-1 px-4 py-2 bg-gray-700/20 text-gray-300 rounded hover:bg-gray-700/40 transition-all"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          {myServers.length > 0 && (
            <div className="mt-16 border-t border-gray-700 pt-8">
              <h2 className="text-2xl font-bold text-white mb-6">Your Active Subscriptions</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {myServers.map((server) => (
                  <div key={server.id} className="bg-green-500/10 border border-green-500/30 rounded-xl p-6">
                    <div className="flex items-start justify-between mb-4">
                      <h3 className="text-lg font-bold text-white">{server.name}</h3>
                      <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
                        Active
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm mb-4">{server.specs}</p>
                    <p className="text-sm text-gray-500">
                      Subscribed since: {new Date(server.subscribed_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Subscription Requests Section */}
          {userRequests.length > 0 && (
            <div className="mt-16 border-t border-gray-700 pt-8">
              <h2 className="text-2xl font-bold text-white mb-6">Your Subscription Requests</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {userRequests.map((req) => (
                  <div
                    key={req.id}
                    className={`rounded-xl p-6 border ${
                      req.status === 'pending'
                        ? 'bg-yellow-500/10 border-yellow-500/30'
                        : req.status === 'approved'
                        ? 'bg-green-500/10 border-green-500/30'
                        : 'bg-red-500/10 border-red-500/30'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-bold text-white">{req.server_name}</h3>
                        <p className="text-xs text-gray-400 mt-1">{req.server_specs}</p>
                      </div>
                      <span
                        className={`text-xs px-3 py-1 rounded-full font-semibold ${
                          req.status === 'pending'
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : req.status === 'approved'
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}
                      >
                        {req.status.charAt(0).toUpperCase() + req.status.slice(1)}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm text-gray-400">
                      <p>
                        <span className="text-gray-500">Requested:</span>{' '}
                        {new Date(req.requested_at).toLocaleDateString()}
                      </p>
                      {req.approved_at && (
                        <p>
                          <span className="text-gray-500">Approved:</span>{' '}
                          {new Date(req.approved_at).toLocaleDateString()}
                        </p>
                      )}
                      {req.rejection_reason && (
                        <p className="text-red-300">
                          <span className="text-red-400">Reason:</span> {req.rejection_reason}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
