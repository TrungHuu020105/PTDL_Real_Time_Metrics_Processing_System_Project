import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Calendar, Plus, Server, Thermometer, TrendingUp } from 'lucide-react'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useDevices } from '../context/DeviceContext'
import { useAuth } from '../context/AuthContext'
import AddDeviceModal from './AddDeviceModal'
import api from '../api'
import { getVNDateInputValue } from '../utils/vnTime'

const DAY_MS = 24 * 60 * 60 * 1000
const IOT_TYPES = new Set(['temperature', 'humidity', 'soil_moisture', 'light_intensity', 'pressure'])

const getMetricColor = (metricType) => ({
  temperature: '#fb7185',
  humidity: '#38bdf8',
  soil_moisture: '#34d399',
  light_intensity: '#facc15',
  pressure: '#a78bfa',
}[metricType] || '#00d4ff')

const formatDateHourLabel = (timestamp) => {
  const date = new Date(Number(timestamp))
  if (Number.isNaN(date.getTime())) return ''
  const dd = String(date.getDate()).padStart(2, '0')
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  return `${dd}/${mm} ${hh}:00`
}

const formatDateBucket = (date) => {
  const dd = String(date.getDate()).padStart(2, '0')
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const yyyy = date.getFullYear()
  return `${dd}/${mm}/${yyyy}`
}

const describeMethod = (method) => {
  if (method === 'open_meteo_location_forecast') return 'Location weather forecast'
  if (method === 'tft_checkpoint') return 'TFT checkpoint'
  if (method === 'tft_seasonal_baseline') return 'TFT seasonal baseline'
  return method || 'Unknown'
}

const describeSource = (source) => {
  const value = String(source || '').toLowerCase()
  if (value.includes('open_meteo')) return 'Open-Meteo hourly forecast'
  if (value.includes('meteostat') || value.includes('weather')) return 'Weather history'
  if (value.includes('metrics')) return 'Realtime metric history'
  return source || 'Unknown'
}

const isValidDateText = (value) => {
  if (!value) return false
  const date = new Date(value)
  return !Number.isNaN(date.getTime())
}

const getForecastRange = (fromDate, toDate) => {
  const from = new Date(fromDate)
  const to = new Date(toDate)
  if (Number.isNaN(from.getTime()) || Number.isNaN(to.getTime())) return null
  return Math.floor((to - from) / DAY_MS) + 1
}

const buildActualData = (metrics, daysDiff) => {
  const nowGuard = Date.now() + 5 * 60 * 1000
  const buckets = new Map()
  const isOneDay = daysDiff === 1

  for (const row of metrics || []) {
    const ts = new Date(row?.event_ts ?? row?.timestamp)
    const value = Number(row?.metric_value ?? row?.value)
    if (Number.isNaN(ts.getTime()) || Number.isNaN(value)) continue
    if (ts.getTime() > nowGuard) continue

    let bucketKey = ''
    let bucketTs = 0
    if (isOneDay) {
      const keyDate = new Date(ts)
      keyDate.setMinutes(0, 0, 0)
      bucketTs = keyDate.getTime()
      bucketKey = `${String(keyDate.getHours()).padStart(2, '0')}:00`
    } else {
      const keyDate = new Date(ts)
      keyDate.setHours(0, 0, 0, 0)
      bucketTs = keyDate.getTime()
      bucketKey = formatDateBucket(keyDate)
    }

    if (!buckets.has(bucketTs)) {
      buckets.set(bucketTs, { timestamp: bucketTs, label: bucketKey, values: [] })
    }
    buckets.get(bucketTs).values.push(value)
  }

  return Array.from(buckets.values())
    .sort((a, b) => a.timestamp - b.timestamp)
    .map((bucket) => ({
      timestamp: bucket.timestamp,
      label: bucket.label,
      value: Number((bucket.values.reduce((acc, cur) => acc + cur, 0) / bucket.values.length).toFixed(2)),
      predictedValue: null,
    }))
}

const mergeForecastData = (actualData, predictions) => {
  if (!actualData?.length) {
    return (predictions || [])
      .map((point) => {
        const ts = new Date(point?.timestamp)
        const value = Number(point?.predicted_value ?? point?.predictedValue)
        if (Number.isNaN(ts.getTime()) || Number.isNaN(value)) return null
        return {
          timestamp: ts.getTime(),
          label: formatDateHourLabel(ts.getTime()),
          value: null,
          predictedValue: Number(value.toFixed(2)),
        }
      })
      .filter(Boolean)
      .sort((a, b) => a.timestamp - b.timestamp)
  }

  const merged = actualData.map((item) => ({ ...item, predictedValue: null }))
  const lastActual = merged[merged.length - 1]
  const lastTs = lastActual.timestamp

  if (predictions?.length) {
    // Keep the forecast line visually connected without duplicating the final
    // actual timestamp, which causes Recharts to generate duplicate tick keys.
    merged.push({
      timestamp: lastTs + 1,
      label: lastActual.label,
      value: null,
      predictedValue: Number(lastActual.value),
    })
  }

  for (const point of predictions || []) {
    const ts = new Date(point?.timestamp)
    const value = Number(point?.predicted_value ?? point?.predictedValue)
    if (Number.isNaN(ts.getTime()) || Number.isNaN(value)) continue
    if (ts.getTime() <= lastTs) continue
    merged.push({
      timestamp: ts.getTime(),
      label: formatDateHourLabel(ts.getTime()),
      value: null,
      predictedValue: Number(value.toFixed(2)),
    })
  }

  return merged.sort((a, b) => a.timestamp - b.timestamp)
}

export default function UserDashboard() {
  const { iotDevices: devices, myServers: servers, createIoTDevice } = useDevices()
  const { user } = useAuth()
  const inactiveStatuses = new Set(['cancelled', 'canceled', 'terminated', 'expired', 'inactive'])
  const activeServers = (servers || []).filter((s) => !inactiveStatuses.has(String(s?.status || '').toLowerCase()))

  const [showAddDeviceModal, setShowAddDeviceModal] = useState(false)
  const [addingDevice, setAddingDevice] = useState(false)
  const [selectedDeviceId, setSelectedDeviceId] = useState(null)
  const [fromDate, setFromDate] = useState(() => getVNDateInputValue())
  const [toDate, setToDate] = useState(getVNDateInputValue())
  const [chartData, setChartData] = useState([])
  const [loading, setLoading] = useState(false)
  const [validationError, setValidationError] = useState('')
  const [fetchError, setFetchError] = useState('')
  const [forecastInfo, setForecastInfo] = useState(null)
  const [forecastRefreshKey, setForecastRefreshKey] = useState(0)
  const [datasetStatus, setDatasetStatus] = useState(null)
  const [datasetStatusLoading, setDatasetStatusLoading] = useState(false)
  const [trainLoading, setTrainLoading] = useState(false)
  const [trainMessage, setTrainMessage] = useState('')
  const [trainError, setTrainError] = useState('')

  const selectedDevice = devices?.find((d) => d.id === selectedDeviceId) || devices?.[0]

  useEffect(() => {
    if (devices?.length > 0 && !selectedDeviceId) setSelectedDeviceId(devices[0].id)
  }, [devices, selectedDeviceId])

  useEffect(() => {
    if (!selectedDevice) {
      setDatasetStatus(null)
      return
    }

    const fetchDatasetStatus = async () => {
      try {
        setDatasetStatusLoading(true)
        setTrainError('')
        const response = await api.get(`/api/model/tft-training/devices/${selectedDevice.id}/status`)
        setDatasetStatus(response?.data?.dataset || null)
      } catch (err) {
        const detail = err?.response?.data?.detail
        const message = typeof detail === 'string' ? detail : detail?.message || 'Dataset status unavailable.'
        setDatasetStatus({
          error: message,
        })
      } finally {
        setDatasetStatusLoading(false)
      }
    }

    fetchDatasetStatus()
  }, [selectedDevice])

  useEffect(() => {
    if (!selectedDevice) return
    if (!IOT_TYPES.has(selectedDevice.device_type)) {
      setValidationError('Thiết bị này không thuộc nhóm metric dự báo.')
      setChartData([])
      setForecastInfo(null)
      return
    }

    const range = getForecastRange(fromDate, toDate)
    if (!isValidDateText(fromDate) || !isValidDateText(toDate)) {
      setValidationError('Ngày không hợp lệ.')
      setChartData([])
      setForecastInfo(null)
      return
    }
    if (range === null || range < 1 || range > 14) {
      setValidationError('Khoảng ngày chỉ cho phép từ 1 đến 14 ngày.')
      setChartData([])
      setForecastInfo(null)
      return
    }
    if (new Date(toDate) < new Date(fromDate)) {
      setValidationError('To Date phải lớn hơn hoặc bằng From Date.')
      setChartData([])
      setForecastInfo(null)
      return
    }
    setValidationError('')

    const fetchData = async () => {
      try {
        setLoading(true)
        setFetchError('')

        const [historyRes, forecastRes] = await Promise.all([
          api.get('/api/metrics/history-by-date', {
            params: {
              metric_type: selectedDevice.device_type,
              source: selectedDevice.source,
              from_date: fromDate,
              to_date: toDate,
            },
          }),
          api.get('/api/dashboard/forecast', {
            params: {
              device_id: selectedDevice.id,
              horizon_days: range,
              history_days: Math.min(365, Math.max(30, range * 10)),
            },
          }),
        ])

        const historyMetrics = historyRes?.data?.data || []
        const forecastPayload = forecastRes?.data || {}
        const actualData = buildActualData(historyMetrics, range)
        const merged = mergeForecastData(actualData, forecastPayload?.predictions || [])

        setChartData(merged)
        setForecastInfo({
          method: forecastPayload.method,
          source: forecastPayload.data_source,
          historyPoints: forecastPayload.history_points,
          horizonDays: forecastPayload.horizon_days || range,
          confidenceScore: forecastPayload.confidence_score,
          qualityLabel: forecastPayload.quality_label,
          forecastMin: forecastPayload.forecast_min,
          forecastMax: forecastPayload.forecast_max,
          forecastDelta: forecastPayload.forecast_delta,
          nextPredictedValue: forecastPayload.next_predicted_value,
          fallbackReason: forecastPayload.fallback_reason,
        })
      } catch (err) {
        console.error('Failed to fetch forecast dashboard data:', err)
        setFetchError(err?.response?.data?.detail?.message || err?.response?.data?.detail || err.message || 'Không thể lấy dữ liệu forecast.')
        setChartData([])
        setForecastInfo(null)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [selectedDevice, fromDate, toDate, forecastRefreshKey])

  const trendIsUp = useMemo(() => {
    const delta = Number(forecastInfo?.forecastDelta)
    if (Number.isNaN(delta)) return false
    return delta > 0
  }, [forecastInfo])

  const handleTrainForecastModel = async () => {
    if (!selectedDevice) return

    try {
      setTrainLoading(true)
      setTrainError('')
      setTrainMessage('Syncing weather history...')

      await api.post(`/api/model/weather-pipeline/devices/${selectedDevice.id}/sync`, null, {
        timeout: 120000,
      })

      setTrainMessage('Refreshing dataset status...')
      const statusResponse = await api.get(`/api/model/tft-training/devices/${selectedDevice.id}/status`, {
        timeout: 60000,
      })
      setDatasetStatus(statusResponse?.data?.dataset || null)

      setTrainMessage('Training TFT forecast model...')
      const trainResponse = await api.post(`/api/model/tft-training/devices/${selectedDevice.id}/train`, null, {
        timeout: 600000,
      })

      const trainedTarget = trainResponse?.data?.target_column || statusResponse?.data?.dataset?.target_column || 'target'
      setTrainMessage(`Training complete for ${trainedTarget}. Refreshing forecast...`)

      const finalStatusResponse = await api.get(`/api/model/tft-training/devices/${selectedDevice.id}/status`, {
        timeout: 60000,
      })
      setDatasetStatus(finalStatusResponse?.data?.dataset || null)
      setTrainMessage(`Model trained successfully at ${trainResponse?.data?.created_at || 'just now'}.`)
      setForecastRefreshKey((value) => value + 1)
    } catch (err) {
      const detail = err?.response?.data?.detail
      const message = typeof detail === 'string' ? detail : detail?.message || err.message || 'Training failed.'
      setTrainError(message)
      setTrainMessage('')
    } finally {
      setTrainLoading(false)
    }
  }

  const handleAddDevice = async (deviceData) => {
    try {
      setAddingDevice(true)
      await createIoTDevice(deviceData)
      setShowAddDeviceModal(false)
    } finally {
      setAddingDevice(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 p-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-gray-400">Overview of your IoT devices and servers</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8 hover:border-neon-cyan/40 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">IoT Devices</h2>
            <Thermometer className="w-6 h-6 text-neon-cyan" />
          </div>
          <p className="text-5xl font-bold text-neon-cyan mb-4">{devices?.length || 0}</p>
          <button
            onClick={() => setShowAddDeviceModal(true)}
            className="w-full px-4 py-2 bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 rounded-lg hover:bg-neon-cyan/30 transition-all flex items-center justify-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Add Device
          </button>
        </div>

        <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8 hover:border-neon-cyan/40 transition-all">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Servers</h2>
            <Server className="w-6 h-6 text-neon-cyan" />
          </div>
          <p className="text-5xl font-bold text-neon-cyan mb-4">{activeServers.length}</p>
        </div>

        <div className="bg-dark-800 border border-yellow-400/20 rounded-xl p-8">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold text-white">Next Long Forecast</h2>
            <TrendingUp className={`w-6 h-6 ${trendIsUp ? 'text-green-400' : 'text-yellow-300'}`} />
          </div>
          <p className="text-3xl font-bold text-yellow-300 mb-1">
            {forecastInfo?.nextPredictedValue ?? '--'}
          </p>
          <p className="text-sm text-gray-400">
            Confidence: {forecastInfo?.confidenceScore !== undefined && forecastInfo?.confidenceScore !== null
              ? `${Math.round(Number(forecastInfo.confidenceScore) * 100)}%`
              : '--'}
          </p>
        </div>
      </div>

      {devices && devices.length > 0 && (
        <div className="bg-dark-800 border border-neon-cyan/20 rounded-xl p-8">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-neon-cyan" />
            Future Forecast
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Sensor</label>
              <select
                value={selectedDeviceId || ''}
                onChange={(e) => setSelectedDeviceId(parseInt(e.target.value, 10))}
                className="w-full bg-dark-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-cyan outline-none"
              >
                {devices.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.name} ({device.device_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">From Date</label>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-400" />
                <input
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  className="w-full bg-dark-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-cyan outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">To Date</label>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-400" />
                <input
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  className="w-full bg-dark-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-cyan outline-none"
                />
              </div>
            </div>
          </div>

          {validationError && (
            <div className="mb-4 p-3 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 text-sm">
              {validationError}
            </div>
          )}

          {fetchError && !validationError && (
            <div className="mb-4 p-3 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 text-sm">
              {fetchError}
            </div>
          )}

          {forecastInfo?.fallbackReason && (
            <div className="mb-4 p-3 rounded-lg border border-yellow-500/40 bg-yellow-500/10 text-yellow-200 text-sm flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>TFT checkpoint fallback is active: {forecastInfo.fallbackReason}</span>
            </div>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_0.8fr] gap-4 mb-6">
            <div className="bg-dark-900/70 border border-cyan-400/20 rounded-xl p-5">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-cyan-300/80 mb-2">Forecast Model</p>
                  <h3 className="text-xl font-semibold text-white">Temporal Fusion Transformer</h3>
                  <p className="text-sm text-gray-400 mt-1">
                    Train a dedicated multi-day forecast model for {selectedDevice?.name}.
                  </p>
                </div>
                <button
                  onClick={handleTrainForecastModel}
                  disabled={trainLoading || datasetStatusLoading}
                  className="px-4 py-2 rounded-lg border border-cyan-400/40 bg-cyan-400/10 text-cyan-200 hover:bg-cyan-400/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {trainLoading ? 'Training...' : 'Train Model'}
                </button>
              </div>

              {trainMessage && (
                <div className="mb-3 rounded-lg border border-cyan-400/30 bg-cyan-400/10 px-3 py-2 text-sm text-cyan-100">
                  {trainMessage}
                </div>
              )}

              {trainError && (
                <div className="mb-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                  {trainError}
                </div>
              )}

              {datasetStatus?.error ? (
                <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 px-3 py-3 text-sm text-yellow-100">
                  {datasetStatus.error}
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div className="rounded-lg bg-dark-800/80 border border-white/5 px-3 py-3">
                    <p className="text-xs text-gray-400 mb-1">Provider</p>
                    <p className="text-sm font-medium text-white">{datasetStatus?.data_provider || '--'}</p>
                  </div>
                  <div className="rounded-lg bg-dark-800/80 border border-white/5 px-3 py-3">
                    <p className="text-xs text-gray-400 mb-1">Target</p>
                    <p className="text-sm font-medium text-white">{datasetStatus?.target_column || '--'}</p>
                  </div>
                  <div className="rounded-lg bg-dark-800/80 border border-white/5 px-3 py-3">
                    <p className="text-xs text-gray-400 mb-1">Rows</p>
                    <p className="text-sm font-medium text-white">{datasetStatus?.rows ?? '--'}</p>
                  </div>
                  <div className="rounded-lg bg-dark-800/80 border border-white/5 px-3 py-3">
                    <p className="text-xs text-gray-400 mb-1">Missing Target</p>
                    <p className="text-sm font-medium text-white">{datasetStatus?.missing_target_rows ?? '--'}</p>
                  </div>
                  <div className="rounded-lg bg-dark-800/80 border border-white/5 px-3 py-3">
                    <p className="text-xs text-gray-400 mb-1">Encoder</p>
                    <p className="text-sm font-medium text-white">{datasetStatus?.recommended_encoder_length ?? '--'}h</p>
                  </div>
                  <div className="rounded-lg bg-dark-800/80 border border-white/5 px-3 py-3">
                    <p className="text-xs text-gray-400 mb-1">Prediction</p>
                    <p className="text-sm font-medium text-white">{datasetStatus?.recommended_prediction_length ?? '--'}h</p>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-dark-900/70 border border-white/10 rounded-xl p-5">
              <p className="text-xs uppercase tracking-[0.18em] text-white/60 mb-3">Training Notes</p>
              <div className="space-y-3 text-sm text-gray-300">
                <p>Long forecast first tries a trained TFT checkpoint.</p>
                <p>If no checkpoint exists, it falls back to weather forecast or a seasonal baseline from realtime metrics.</p>
                <p className="text-gray-400">
                  Owner: {user?.username || '--'} | Device ID: {selectedDevice?.id ?? '--'}
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-dark-900/60 border border-gray-700 rounded-lg p-4">
              <p className="text-xs text-gray-400 mb-2">Model</p>
              <p className="text-white font-semibold">{describeMethod(forecastInfo?.method)}</p>
              <p className="text-xs text-gray-400 mt-3 mb-2">Source</p>
              <p className="text-white">{describeSource(forecastInfo?.source)}</p>
              <p className="text-xs text-gray-400 mt-3">History: {forecastInfo?.historyPoints ?? '--'} points</p>
              <p className="text-xs text-gray-400">Horizon: {forecastInfo?.horizonDays ?? '--'} days</p>
            </div>

            <div className="bg-dark-900/60 border border-gray-700 rounded-lg p-4">
              <p className="text-xs text-gray-400 mb-2">Forecast Range</p>
              <p className="text-white font-semibold">
                {forecastInfo?.forecastMin ?? '--'} - {forecastInfo?.forecastMax ?? '--'}
              </p>
              <p className="text-xs text-gray-400 mt-3 mb-2">Expected Change</p>
              <p className={`font-semibold ${trendIsUp ? 'text-green-400' : 'text-yellow-300'}`}>
                {forecastInfo?.forecastDelta ?? '--'}
              </p>
              <p className="text-xs text-gray-400 mt-3">Quality: {forecastInfo?.qualityLabel || '--'}</p>
              <p className="text-xs text-gray-400">
                Confidence: {forecastInfo?.confidenceScore !== undefined && forecastInfo?.confidenceScore !== null
                  ? `${Math.round(Number(forecastInfo.confidenceScore) * 100)}%`
                  : '--'}
              </p>
            </div>
          </div>

          {loading ? (
            <div className="h-96 flex items-center justify-center text-gray-400">Loading forecast...</div>
          ) : chartData.length > 0 ? (
            <div className="h-96 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis
                    dataKey="timestamp"
                    type="number"
                    scale="time"
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={formatDateHourLabel}
                    stroke="#999"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis stroke="#999" tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #0f3460' }}
                    labelStyle={{ color: '#00d4ff' }}
                    labelFormatter={(value) => formatDateHourLabel(value)}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke={getMetricColor(selectedDevice?.device_type)}
                    strokeWidth={2}
                    dot={false}
                    name="Actual"
                    connectNulls={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="predictedValue"
                    stroke="#facc15"
                    strokeWidth={2}
                    dot={false}
                    strokeDasharray="7 6"
                    name="Forecast"
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-96 flex items-center justify-center text-gray-400">
              No data available for the selected date range
            </div>
          )}

          <div className="mt-4 p-3 bg-neon-cyan/10 border border-neon-cyan/30 rounded-lg">
            <p className="text-xs text-neon-cyan">
              Note: khi horizon &gt; 1 ngày, actual được gộp theo ngày còn forecast vẫn theo giờ.
            </p>
          </div>
        </div>
      )}

      <AddDeviceModal
        isOpen={showAddDeviceModal}
        onClose={() => setShowAddDeviceModal(false)}
        onAdd={handleAddDevice}
        isLoading={addingDevice}
      />
    </div>
  )
}
