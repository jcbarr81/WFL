const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

const CSRF_COOKIE_NAME = 'csrftoken'

const getCookie = (name) => {
  const match = document.cookie.match(new RegExp('(^|;)\\s*' + name + '=([^;]+)'))
  return match ? decodeURIComponent(match[2]) : null
}

const ensureCsrfToken = async () => {
  let token = getCookie(CSRF_COOKIE_NAME)
  if (!token) {
    try {
      await fetch(`${API_BASE_URL}/health/`, { credentials: 'include' })
      token = getCookie(CSRF_COOKIE_NAME)
    } catch (err) {
      console.warn('Could not fetch CSRF token', err)
    }
  }
  return token
}

const buildUrl = (path) => {
  if (!path.startsWith('/')) return `${API_BASE_URL}/${path}`
  return `${API_BASE_URL}${path}`
}

export const apiFetch = async (path, options = {}) => {
  const { method = 'GET', body, headers = {}, ...rest } = options
  const config = {
    method,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...headers,
    },
    ...rest,
  }

  if (body !== undefined) {
    if (!(body instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json'
      config.body = JSON.stringify(body)
    } else {
      config.body = body
    }
  }

  if (!['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase())) {
    const csrf = await ensureCsrfToken()
    if (csrf) {
      config.headers['X-CSRFToken'] = csrf
    }
  }

  const response = await fetch(buildUrl(path), config)
  const contentType = response.headers.get('content-type')
  const isJson = contentType && contentType.includes('application/json')
  const payload = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    let message = response.statusText
    if (typeof payload === 'string') {
      message = payload
    } else if (payload?.detail) {
      message = payload.detail
    } else if (payload?.non_field_errors?.length) {
      message = payload.non_field_errors[0]
    } else if (isJson) {
      // Attempt to flatten field errors
      const parts = Object.entries(payload || {}).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      if (parts.length) message = parts.join(' | ')
    }
    throw new Error(message || 'Request failed')
  }

  return payload
}

// Auth
export const health = () => apiFetch('/health/')
export const me = () => apiFetch('/auth/me/')
export const login = (email, password) => apiFetch('/auth/login/', { method: 'POST', body: { email, password } })
export const register = (email, password) => apiFetch('/auth/register/', { method: 'POST', body: { email, password } })
export const logout = () => apiFetch('/auth/logout/', { method: 'POST' })

// Leagues
export const listLeagues = () => apiFetch('/leagues/')
export const createLeague = (data) => apiFetch('/leagues/', { method: 'POST', body: data })
export const getLeagueStructure = (leagueId) => apiFetch(`/leagues/${leagueId}/structure/`)
export const listTeams = (leagueId) => apiFetch(`/leagues/${leagueId}/teams/`)
export const createTeam = (leagueId, data) => apiFetch(`/leagues/${leagueId}/teams/create/`, { method: 'POST', body: data })
export const renameConference = (leagueId, confId, name) =>
  apiFetch(`/leagues/${leagueId}/conferences/${confId}/rename/`, { method: 'PATCH', body: { name } })
export const renameDivision = (leagueId, divId, name) =>
  apiFetch(`/leagues/${leagueId}/divisions/${divId}/rename/`, { method: 'PATCH', body: { name } })

// Roster helpers (optional)
export const listRoster = (leagueId, teamId) => apiFetch(`/leagues/${leagueId}/teams/${teamId}/roster/`)
export const addRosterPlayer = (leagueId, teamId, data) =>
  apiFetch(`/leagues/${leagueId}/teams/${teamId}/roster/add/`, { method: 'POST', body: data })
export const releaseRosterPlayer = (leagueId, teamId, playerId) =>
  apiFetch(`/leagues/${leagueId}/teams/${teamId}/roster/${playerId}/release/`, { method: 'DELETE' })

// Trades
export const listTrades = (leagueId) => apiFetch(`/leagues/${leagueId}/trades/`)
export const createTrade = (leagueId, data) =>
  apiFetch(`/leagues/${leagueId}/trades/`, { method: 'POST', body: data })
export const acceptTrade = (tradeId) => apiFetch(`/trades/${tradeId}/accept/`, { method: 'PUT' })
export const reverseTrade = (tradeId) => apiFetch(`/trades/${tradeId}/reverse/`, { method: 'PUT' })

// Waivers
export const listWaivers = (leagueId) => apiFetch(`/leagues/${leagueId}/waivers/`)
export const releaseToWaivers = (leagueId, playerId) =>
  apiFetch(`/leagues/${leagueId}/waivers/release/`, { method: 'POST', body: { player: playerId } })
export const claimWaiver = (waiverId) => apiFetch(`/waivers/${waiverId}/claim/`, { method: 'POST' })

// Contracts
export const updateContract = (leagueId, playerId, data) =>
  apiFetch(`/leagues/${leagueId}/contracts/${playerId}/`, { method: 'PUT', body: data })

// Deletes
export const deleteLeague = (leagueId) => apiFetch(`/leagues/${leagueId}/delete/`, { method: 'DELETE' })
export const deleteTeam = (leagueId, teamId) => apiFetch(`/leagues/${leagueId}/teams/${teamId}/delete/`, { method: 'DELETE' })

// Schedule / standings
export const generateSeason = (leagueId, year) =>
  apiFetch(`/leagues/${leagueId}/seasons/generate/`, { method: 'POST', body: { year } })
export const getSchedule = (leagueId, year) => apiFetch(`/leagues/${leagueId}/seasons/${year}/schedule/`)
export const completeGame = (gameId, home_score, away_score) =>
  apiFetch(`/games/${gameId}/complete/`, { method: 'PUT', body: { home_score, away_score } })
export const getStandings = (leagueId, year) =>
  apiFetch(`/leagues/${leagueId}/seasons/${year}/standings/`)
export const getPlayoffSeeds = (leagueId, year) =>
  apiFetch(`/leagues/${leagueId}/seasons/${year}/seeds/`)
export const getPlayoffBracket = (leagueId, year) =>
  apiFetch(`/leagues/${leagueId}/seasons/${year}/bracket/`)

// Drafts
export const createDraft = (leagueId) => apiFetch(`/leagues/${leagueId}/drafts/`, { method: 'POST' })
export const getDraft = (draftId) => apiFetch(`/drafts/${draftId}/`)
export const selectDraftPick = (pickId, player_id) =>
  apiFetch(`/drafts/picks/${pickId}/select/`, { method: 'PUT', body: { player_id } })
export const generateRookies = (leagueId) =>
  apiFetch(`/leagues/${leagueId}/drafts/rookies/generate/`, { method: 'POST' })
export const listRookies = (leagueId) => apiFetch(`/leagues/${leagueId}/drafts/rookies/`)

// Free agency
export const listFreeAgents = (leagueId) => apiFetch(`/leagues/${leagueId}/free_agents/`)
export const bidFreeAgent = (leagueId, data) =>
  apiFetch(`/leagues/${leagueId}/free_agents/bids/`, { method: 'POST', body: data })
export const resolveFreeAgency = (leagueId) =>
  apiFetch(`/leagues/${leagueId}/free_agents/resolve/`, { method: 'POST' })

// Injuries / notifications
export const listInjuries = (leagueId) => apiFetch(`/leagues/${leagueId}/injuries/`)
export const createInjury = (leagueId, data) =>
  apiFetch(`/leagues/${leagueId}/injuries/`, { method: 'POST', body: data })
export const resolveInjury = (injuryId) =>
  apiFetch(`/injuries/${injuryId}/resolve/`, { method: 'PUT' })
export const listNotifications = () => apiFetch('/notifications/')
export const markNotificationRead = (id) => apiFetch(`/notifications/${id}/read/`, { method: 'PUT' })
