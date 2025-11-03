import { format, parseISO, isValid } from 'date-fns'
import { zhCN } from 'date-fns/locale'

/**
 * 格式化日期
 * @param {string|Date} date - 日期
 * @param {string} formatStr - 格式字符串
 * @returns {string}
 */
export const formatDate = (date, formatStr = 'yyyy-MM-dd') => {
  if (!date) return ''
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    if (!isValid(dateObj)) return ''
    
    return format(dateObj, formatStr, { locale: zhCN })
  } catch (error) {
    console.error('Date format error:', error)
    return ''
  }
}

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期
 * @returns {string}
 */
export const formatDateTime = (date) => {
  return formatDate(date, 'yyyy-MM-dd HH:mm:ss')
}

/**
 * 格式化时间
 * @param {string|Date} date - 日期
 * @returns {string}
 */
export const formatTime = (date) => {
  return formatDate(date, 'HH:mm:ss')
}

/**
 * 获取相对时间描述
 * @param {string|Date} date - 日期
 * @returns {string}
 */
export const getRelativeTime = (date) => {
  if (!date) return ''
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    if (!isValid(dateObj)) return ''
    
    const now = new Date()
    const diff = now - dateObj
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    
    if (days > 0) {
      return `${days}天前`
    } else if (hours > 0) {
      return `${hours}小时前`
    } else if (minutes > 0) {
      return `${minutes}分钟前`
    } else {
      return '刚刚'
    }
  } catch (error) {
    console.error('Relative time error:', error)
    return ''
  }
}

/**
 * 获取今天的日期字符串
 * @returns {string}
 */
export const getTodayString = () => {
  return formatDate(new Date(), 'yyyy-MM-dd')
}

/**
 * 获取本周的开始和结束日期
 * @returns {Object}
 */
export const getThisWeek = () => {
  const now = new Date()
  const dayOfWeek = now.getDay()
  const startOfWeek = new Date(now)
  startOfWeek.setDate(now.getDate() - dayOfWeek + 1) // 周一
  
  const endOfWeek = new Date(startOfWeek)
  endOfWeek.setDate(startOfWeek.getDate() + 6) // 周日
  
  return {
    start: formatDate(startOfWeek),
    end: formatDate(endOfWeek)
  }
}

/**
 * 获取本月的开始和结束日期
 * @returns {Object}
 */
export const getThisMonth = () => {
  const now = new Date()
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
  const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  
  return {
    start: formatDate(startOfMonth),
    end: formatDate(endOfMonth)
  }
}

/**
 * 获取指定日期所在周的开始和结束日期
 * @param {Date} date - 指定日期
 * @returns {Array} [startDate, endDate]
 */
export const getWeekStartEnd = (date = new Date()) => {
  const dayOfWeek = date.getDay()
  const startOfWeek = new Date(date)
  startOfWeek.setDate(date.getDate() - dayOfWeek + 1) // 周一
  
  const endOfWeek = new Date(startOfWeek)
  endOfWeek.setDate(startOfWeek.getDate() + 6) // 周日
  
  return [
    formatDate(startOfWeek),
    formatDate(endOfWeek)
  ]
}

/**
 * 获取指定日期所在月的开始和结束日期
 * @param {Date} date - 指定日期
 * @returns {Array} [startDate, endDate]
 */
export const getMonthStartEnd = (date = new Date()) => {
  const startOfMonth = new Date(date.getFullYear(), date.getMonth(), 1)
  const endOfMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0)
  
  return [
    formatDate(startOfMonth),
    formatDate(endOfMonth)
  ]
}