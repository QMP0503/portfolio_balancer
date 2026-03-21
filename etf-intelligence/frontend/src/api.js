/**
 * All API calls for the ETF Portfolio Intelligence System.
 * Uses the /api proxy (configured in vite.config.js → VITE_API_URL).
 * Cookies are sent automatically via credentials: 'include'.
 */

const BASE = '/api'

async function request(method, path, body = null) {
  const opts = {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : {},
  }
  if (body) opts.body = JSON.stringify(body)

  const res = await fetch(`${BASE}${path}`, opts)

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const error = new Error(err.detail || 'Request failed')
    error.status = res.status
    throw error
  }

  // 204 No Content
  if (res.status === 204) return null
  return res.json()
}

// --- Auth ---

export function login(email, password, rememberMe = false) {
  return request('POST', '/auth/login', { email, password, remember_me: rememberMe })
}

export function logout() {
  return request('POST', '/auth/logout')
}

// --- Portfolios ---

export function getPortfolios() {
  return request('GET', '/portfolios')
}

export function createPortfolio(accountName) {
  return request('POST', '/portfolios', { account_name: accountName })
}

// --- Allocations ---

export function getAllocations(portfolioId) {
  return request('GET', `/portfolios/${portfolioId}/allocations`)
}

export function setAllocation(portfolioId, ticker, targetPct, goal = '') {
  return request('PUT', `/portfolios/${portfolioId}/allocations/${ticker}`, {
    target_pct: targetPct,
    goal,
  })
}

// --- Holdings ---

export function getHoldings(portfolioId) {
  return request('GET', `/portfolios/${portfolioId}/holdings`)
}

export function updateHolding(portfolioId, ticker, shares) {
  return request('PUT', `/portfolios/${portfolioId}/holdings/${ticker}`, { shares })
}

// --- Quotes ---

export function getLatestQuotes() {
  return request('GET', '/quotes/latest')
}

// --- Rebalancer ---

export function getRecommendations(portfolioId, contributionCad) {
  return request('GET', `/rebalancer/${portfolioId}/recommend?contribution_cad=${contributionCad}`)
}

export function getTiming() {
  return request('GET', '/rebalancer/timing')
}
