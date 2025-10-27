/**
 * Symbol to Company Name lookup utility
 * Caches the nasdaqlisted.json data for 1 day in localStorage
 */

const CACHE_KEY = 'nasdaqlisted_cache'
const CACHE_TIMESTAMP_KEY = 'nasdaqlisted_cache_timestamp'
const CACHE_DURATION = 24 * 60 * 60 * 1000 // 1 day in milliseconds

let symbolMap = null

/**
 * Load symbol data from cache or fetch from server
 * @returns {Promise<Map<string, string>>} Map of Symbol -> CompanyName
 */
async function loadSymbolData() {
  // Check if already loaded in memory
  if (symbolMap) {
    return symbolMap
  }

  // Check localStorage cache
  const cachedData = localStorage.getItem(CACHE_KEY)
  const cachedTimestamp = localStorage.getItem(CACHE_TIMESTAMP_KEY)

  if (cachedData && cachedTimestamp) {
    const timestamp = parseInt(cachedTimestamp, 10)
    const now = Date.now()

    // If cache is still valid (less than 1 day old)
    if (now - timestamp < CACHE_DURATION) {
      console.log('[SymbolLookup] Loading from cache')
      const data = JSON.parse(cachedData)
      symbolMap = new Map(data.map(item => [item.Symbol, item.CompanyName]))
      return symbolMap
    }
  }

  // Fetch from server
  console.log('[SymbolLookup] Fetching from server')
  try {
    const response = await fetch('/nasdaqlisted.json')
    if (!response.ok) {
      throw new Error(`Failed to fetch nasdaqlisted.json: ${response.status}`)
    }

    const data = await response.json()

    // Store in localStorage
    localStorage.setItem(CACHE_KEY, JSON.stringify(data))
    localStorage.setItem(CACHE_TIMESTAMP_KEY, Date.now().toString())

    // Create map
    symbolMap = new Map(data.map(item => [item.Symbol, item.CompanyName]))
    console.log(`[SymbolLookup] Loaded ${symbolMap.size} symbols`)

    return symbolMap
  } catch (error) {
    console.error('[SymbolLookup] Error loading symbol data:', error)
    // Return empty map on error
    symbolMap = new Map()
    return symbolMap
  }
}

/**
 * Get company name for a given symbol
 * @param {string} symbol - Stock symbol (e.g., 'AAPL', 'MSFT')
 * @returns {Promise<string>} Company name or symbol if not found
 */
export async function getCompanyName(symbol) {
  if (!symbol) return ''

  const map = await loadSymbolData()
  return map.get(symbol) || symbol
}

/**
 * Get company name synchronously (only works if data is already loaded)
 * @param {string} symbol - Stock symbol
 * @returns {string} Company name or symbol if not found or data not loaded
 */
export function getCompanyNameSync(symbol) {
  if (!symbol) return ''
  if (!symbolMap) return symbol

  return symbolMap.get(symbol) || symbol
}

/**
 * Preload symbol data (call this on app initialization)
 * @returns {Promise<void>}
 */
export async function preloadSymbolData() {
  await loadSymbolData()
}

/**
 * Clear the cache (useful for testing or manual refresh)
 */
export function clearSymbolCache() {
  localStorage.removeItem(CACHE_KEY)
  localStorage.removeItem(CACHE_TIMESTAMP_KEY)
  symbolMap = null
  console.log('[SymbolLookup] Cache cleared')
}

/**
 * Get cache info for debugging
 * @returns {object} Cache status information
 */
export function getCacheInfo() {
  const cachedTimestamp = localStorage.getItem(CACHE_TIMESTAMP_KEY)
  if (!cachedTimestamp) {
    return { cached: false }
  }

  const timestamp = parseInt(cachedTimestamp, 10)
  const now = Date.now()
  const age = now - timestamp
  const remaining = CACHE_DURATION - age

  return {
    cached: true,
    timestamp: new Date(timestamp).toISOString(),
    ageHours: (age / (60 * 60 * 1000)).toFixed(1),
    remainingHours: (remaining / (60 * 60 * 1000)).toFixed(1),
    valid: remaining > 0
  }
}
