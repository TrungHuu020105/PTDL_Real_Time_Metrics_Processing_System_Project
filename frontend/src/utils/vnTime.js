export const VN_TIMEZONE = 'Asia/Ho_Chi_Minh'

export const toDateSafe = (value) => {
  if (value instanceof Date) return value
  if (value === null || value === undefined) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export const formatVNTime = (value, withSeconds = false) => {
  const date = toDateSafe(value)
  if (!date) return 'N/A'
  return date.toLocaleTimeString('vi-VN', {
    timeZone: VN_TIMEZONE,
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    ...(withSeconds ? { second: '2-digit' } : {}),
  })
}

export const formatVNDate = (value) => {
  const date = toDateSafe(value)
  if (!date) return 'N/A'
  return date.toLocaleDateString('en-CA', { timeZone: VN_TIMEZONE }) // YYYY-MM-DD
}

export const formatVNDateTime = (value, withSeconds = true) => {
  const date = toDateSafe(value)
  if (!date) return 'N/A'
  return date.toLocaleString('vi-VN', {
    timeZone: VN_TIMEZONE,
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    ...(withSeconds ? { second: '2-digit' } : {}),
  })
}

export const getVNDateInputValue = () => formatVNDate(new Date())

