import { useEffect, useMemo, useState } from 'react'
import { AuthProvider, useAuth } from './auth'
import {
  addRosterPlayer,
  claimWaiver,
  createLeague,
  createTeam,
  getLeagueStructure,
  health,
  listLeagues,
  listRoster,
  listWaivers,
  listTeams,
  releaseRosterPlayer,
  createTrade,
  acceptTrade,
  releaseToWaivers,
  updateContract,
  deleteLeague,
  deleteTeam,
  renameConference,
  renameDivision,
  generateSeason,
  getSchedule,
  completeGame,
  getStandings,
  getPlayoffSeeds,
  getPlayoffBracket,
  createDraft,
  getDraft,
  selectDraftPick,
  generateRookies,
  listRookies,
  listFreeAgents,
  bidFreeAgent,
  resolveFreeAgency,
  listInjuries,
  createInjury,
  resolveInjury,
  listNotifications,
  markNotificationRead,
} from './api'

const Pill = ({ tone = 'neutral', children }) => (
  <span className={`pill pill-${tone}`}>{children}</span>
)

const Section = ({ title, subtitle, children, action }) => (
  <section className="card">
    <header className="card-header">
      <div>
        <p className="eyebrow">{subtitle}</p>
        <h3>{title}</h3>
      </div>
      {action}
    </header>
    {children}
  </section>
)

function AuthPanel({ apiStatus }) {
  const { user, loading, login, register, logout } = useAuth()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ email: '', password: '' })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (evt) => {
    evt.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
      } else {
        await register(form.email, form.password)
      }
      setForm({ email: '', password: '' })
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCreateDraft = async () => {
    if (!selected) return
    setApiError(null)
    setLoadingDraft(true)
    try {
      const data = await createDraft(selected)
      setDraft(data)
      setDraftIdInput(data.id)
      await loadRookies(selected)
    } catch (err) {
      setApiError(err.message)
      setDraft(null)
    } finally {
      setLoadingDraft(false)
    }
  }

  const handleLoadDraft = async () => {
    if (!draftIdInput) return
    setApiError(null)
    setLoadingDraft(true)
    try {
      const data = await getDraft(draftIdInput)
      setDraft(data)
      await loadRookies(selected)
    } catch (err) {
      setApiError(err.message)
      setDraft(null)
    } finally {
      setLoadingDraft(false)
    }
  }

  const handleSelectPick = async (evt) => {
    evt.preventDefault()
    if (!selectedPickId || !pickPlayerId) return
    setApiError(null)
    setLoadingDraft(true)
    try {
      await selectDraftPick(selectedPickId, Number(pickPlayerId))
      const updated = await getDraft(draftIdInput || draft?.id)
      setDraft(updated)
      setPickPlayerId('')
      setSelectedPickId(null)
      await loadRookies(selected)
    } catch (err) {
      setApiError(err.message)
    } finally {
      setLoadingDraft(false)
    }
  }

  const loadRookies = async (leagueIdParam) => {
    const leagueId = leagueIdParam || selected
    if (!leagueId) return
    setLoadingRookies(true)
    setApiError(null)
    try {
      const data = await listRookies(leagueId)
      setRookies(data)
    } catch (err) {
      setApiError(err.message)
      setRookies([])
    } finally {
      setLoadingRookies(false)
    }
  }

  const handleGenerateRookies = async () => {
    if (!selected) return
    setApiError(null)
    setLoadingRookies(true)
    try {
      await generateRookies(selected)
      await loadRookies(selected)
    } catch (err) {
      setApiError(err.message)
    } finally {
      setLoadingRookies(false)
    }
  }

  const loadFreeAgents = async () => {
    if (!selected) return
    setLoadingFA(true)
    setApiError(null)
    try {
      const data = await listFreeAgents(selected)
      setFreeAgents(data)
    } catch (err) {
      setApiError(err.message)
      setFreeAgents([])
    } finally {
      setLoadingFA(false)
    }
  }

  const handleBidFA = async (evt) => {
    evt.preventDefault()
    if (!selected || !faOffer.player || !faOffer.team) return
    setApiError(null)
    try {
      await bidFreeAgent(selected, { ...faOffer, amount: Number(faOffer.amount) })
      await loadFreeAgents()
      await loadRoster(faOffer.team)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleResolveFA = async () => {
    if (!selected) return
    setApiError(null)
    setResolvingFA(true)
    try {
      await resolveFreeAgency(selected)
      await loadFreeAgents()
      if (rosterTeam) await loadRoster(rosterTeam)
    } catch (err) {
      setApiError(err.message)
    } finally {
      setResolvingFA(false)
    }
  }

  const loadInjuries = async () => {
    if (!selected) return
    setLoadingInjuries(true)
    setApiError(null)
    try {
      const data = await listInjuries(selected)
      setInjuries(data)
    } catch (err) {
      setApiError(err.message)
      setInjuries([])
    } finally {
      setLoadingInjuries(false)
    }
  }

  const handleCreateInjury = async (evt) => {
    evt.preventDefault()
    if (!selected || !newInjury.player) return
    setApiError(null)
    try {
      await createInjury(selected, {
        player: Number(newInjury.player),
        severity: newInjury.severity,
        duration_weeks: Number(newInjury.duration_weeks),
      })
      setNewInjury({ player: '', severity: 'minor', duration_weeks: 1 })
      await loadInjuries()
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleResolveInjury = async (injuryId) => {
    setApiError(null)
    try {
      await resolveInjury(injuryId)
      await loadInjuries()
    } catch (err) {
      setApiError(err.message)
    }
  }

  const loadNotifications = async () => {
    setApiError(null)
    try {
      const data = await listNotifications()
      setNotifications(data)
    } catch (err) {
      setApiError(err.message)
      setNotifications([])
    }
  }

  const handleMarkNotification = async (id) => {
    setApiError(null)
    try {
      await markNotificationRead(id)
      await loadNotifications()
    } catch (err) {
      setApiError(err.message)
    }
  }

  if (loading) {
    return (
      <Section title="Session" subtitle="Checking">
        <p>Checking session…</p>
      </Section>
    )
  }

  if (user) {
    return (
      <Section
        title="Session"
        subtitle="Signed in"
        action={
          <button className="ghost" onClick={logout}>
            Logout
          </button>
        }
      >
        <div className="stack">
          <div className="row">
            <Pill tone="success">Ready</Pill>
            <Pill tone={apiStatus === 'ok' ? 'success' : 'warn'}>API {apiStatus}</Pill>
          </div>
          <p className="muted">
            Signed in as <strong>{user.email}</strong>. Use the forms below to spin up leagues and teams.
          </p>
        </div>
      </Section>
    )
  }

  return (
    <Section
      title="Session"
      subtitle={apiStatus === 'ok' ? 'Connect to start' : 'API needs attention'}
      action={
        <div className="toggle">
          <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>
            Login
          </button>
          <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>
            Register
          </button>
        </div>
      }
    >
      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          <span>Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
            placeholder="commish@example.com"
          />
        </label>
        <label>
          <span>Password</span>
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
            placeholder="********"
          />
        </label>
        <div className="row">
          <button className="primary" type="submit" disabled={submitting || apiStatus !== 'ok'}>
            {submitting ? 'Working…' : mode === 'login' ? 'Login' : 'Create account'}
          </button>
          <Pill tone={apiStatus === 'ok' ? 'success' : 'warn'}>API {apiStatus}</Pill>
        </div>
        {error && <p className="error">{error}</p>}
      </form>
    </Section>
  )
}

const defaultLeagueForm = {
  name: '',
  conference_count: 2,
  division_count_per_conference: 4,
  teams_per_division: 4,
  salary_cap: 200000000,
  roster_size_limit: 53,
  free_agency_mode: 'auction',
  allow_cap_growth: false,
  allow_playoff_expansion: false,
  enable_realignment: true,
}

const defaultTeamForm = {
  name: '',
  conference: '',
  division: '',
  city: '',
  nickname: '',
  abbreviation: '',
  primary_color: '#0f172a',
  secondary_color: '#fbbf24',
  owner_email: '',
  stadium_name: '',
  stadium_capacity: 60000,
  stadium_turf: 'grass',
  stadium_weather: 'temperate',
}

const defaultPlayerForm = {
  first_name: '',
  last_name: '',
  position: 'QB',
  age: 24,
  contract: { salary: 5000000, bonus: 0, years: 1, start_year: 2025 },
}

const defaultTradeState = {
  from_team: '',
  to_team: '',
  from_player_ids: [],
  to_player_ids: [],
}

const defaultContractForm = {
  salary: 5000000,
  bonus: 0,
  years: 1,
  start_year: 2025,
}

function LeagueManager() {
  const { user } = useAuth()
  const [apiError, setApiError] = useState(null)
  const [leagues, setLeagues] = useState([])
  const [selected, setSelected] = useState(null)
  const [structure, setStructure] = useState(null)
  const [loadingLeagues, setLoadingLeagues] = useState(false)
  const [loadingStructure, setLoadingStructure] = useState(false)
  const [leagueForm, setLeagueForm] = useState(defaultLeagueForm)
  const [teamForm, setTeamForm] = useState(defaultTeamForm)
  const [rosterTeam, setRosterTeam] = useState(null)
  const [roster, setRoster] = useState([])
  const [loadingRoster, setLoadingRoster] = useState(false)
  const [playerForm, setPlayerForm] = useState(defaultPlayerForm)
  const [tradeState, setTradeState] = useState(defaultTradeState)
  const [teamsFlat, setTeamsFlat] = useState([])
  const [tradeFromRoster, setTradeFromRoster] = useState([])
  const [tradeToRoster, setTradeToRoster] = useState([])
  const [waivers, setWaivers] = useState([])
  const [contractForm, setContractForm] = useState(defaultContractForm)
  const [contractPlayerId, setContractPlayerId] = useState('')
  const [deletingTeamId, setDeletingTeamId] = useState(null)
  const [editingConfId, setEditingConfId] = useState(null)
  const [confRename, setConfRename] = useState('')
  const [editingDivId, setEditingDivId] = useState(null)
  const [divRename, setDivRename] = useState('')
  const [scheduleYear, setScheduleYear] = useState(new Date().getFullYear())
  const [schedule, setSchedule] = useState(null)
  const [standings, setStandings] = useState([])
  const [loadingSchedule, setLoadingSchedule] = useState(false)
  const [loadingStandings, setLoadingStandings] = useState(false)
  const [scoreInputs, setScoreInputs] = useState({})
  const [seeds, setSeeds] = useState([])
  const [loadingSeeds, setLoadingSeeds] = useState(false)
  const [bracket, setBracket] = useState([])
  const [loadingBracket, setLoadingBracket] = useState(false)
  const [draft, setDraft] = useState(null)
  const [draftIdInput, setDraftIdInput] = useState('')
  const [pickPlayerId, setPickPlayerId] = useState('')
  const [selectedPickId, setSelectedPickId] = useState(null)
  const [loadingDraft, setLoadingDraft] = useState(false)
  const [rookies, setRookies] = useState([])
  const [loadingRookies, setLoadingRookies] = useState(false)
  const [freeAgents, setFreeAgents] = useState([])
  const [loadingFA, setLoadingFA] = useState(false)
  const [faOffer, setFaOffer] = useState({ player: '', team: '', amount: 1000000 })
  const [resolvingFA, setResolvingFA] = useState(false)
  const [injuries, setInjuries] = useState([])
  const [loadingInjuries, setLoadingInjuries] = useState(false)
  const [newInjury, setNewInjury] = useState({ player: '', severity: 'minor', duration_weeks: 1 })
  const [notifications, setNotifications] = useState([])

  const loadLeagues = async () => {
    setLoadingLeagues(true)
    setApiError(null)
    try {
      const data = await listLeagues()
      setLeagues(data)
      if (data.length && !selected) {
        setSelected(data[0].id)
      }
    } catch (err) {
      setApiError(err.message)
    } finally {
      setLoadingLeagues(false)
    }
  }

  const loadStructure = async (leagueId) => {
    if (!leagueId) return
    setLoadingStructure(true)
    setApiError(null)
    try {
      const data = await getLeagueStructure(leagueId)
      setStructure(data)
      const flattened =
        data.conferences?.flatMap((conf) =>
          conf.divisions.flatMap((div) =>
            div.teams.map((t) => ({
              ...t,
              conference: conf.name,
              division: div.name,
            })),
          ),
        ) || []
      setTeamsFlat(flattened)
      const firstConference = data.conferences?.[0]
      const firstDivision = firstConference?.divisions?.[0]
      setTeamForm((prev) => ({
        ...prev,
        conference: firstConference?.id || '',
        division: firstDivision?.id || '',
      }))
      setRosterTeam(null)
      setRoster([])
      setTradeState(defaultTradeState)
      setTradeFromRoster([])
      setTradeToRoster([])
      setWaivers([])
      setContractPlayerId('')
    } catch (err) {
      setApiError(err.message)
      setStructure(null)
      setTeamsFlat([])
    } finally {
      setLoadingStructure(false)
    }
  }

  useEffect(() => {
    if (!user) {
      setLeagues([])
      setStructure(null)
      return
    }
    loadLeagues()
  }, [user])

  useEffect(() => {
    loadStructure(selected)
  }, [selected])

  useEffect(() => {
    if (selected) {
      loadSchedule()
      loadStandings(selected, scheduleYear)
      loadSeeds(selected, scheduleYear)
      loadBracket(selected, scheduleYear)
      setDraft(null)
      setDraftIdInput('')
      loadRookies(selected)
      loadFreeAgents()
      loadInjuries()
      loadNotifications()
    } else {
      setSchedule(null)
      setStandings([])
      setSeeds([])
      setBracket([])
      setDraft(null)
      setDraftIdInput('')
      setRookies([])
      setFreeAgents([])
      setInjuries([])
      setNotifications([])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected])

  const loadRoster = async (teamId) => {
    if (!selected || !teamId) return
    setLoadingRoster(true)
    setApiError(null)
    try {
      const data = await listRoster(selected, teamId)
      setRosterTeam(teamId)
      setRoster(data)
    } catch (err) {
      setApiError(err.message)
    } finally {
      setLoadingRoster(false)
    }
  }

  const handleLeagueSubmit = async (evt) => {
    evt.preventDefault()
    setApiError(null)
    try {
      const payload = {
        ...leagueForm,
        conference_count: Number(leagueForm.conference_count),
        division_count_per_conference: Number(leagueForm.division_count_per_conference),
        teams_per_division: Number(leagueForm.teams_per_division),
        salary_cap: Number(leagueForm.salary_cap),
        roster_size_limit: Number(leagueForm.roster_size_limit),
      }
      const created = await createLeague(payload)
      setLeagueForm(defaultLeagueForm)
      setSelected(created.id)
      await loadLeagues()
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleDeleteLeague = async () => {
    if (!selected) return
    if (!window.confirm('Delete this league? This cannot be undone.')) return
    setApiError(null)
    try {
      await deleteLeague(selected)
      await loadLeagues()
      setSelected(null)
      setStructure(null)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleDeleteTeam = async (teamId) => {
    if (!selected || !teamId) return
    if (deletingTeamId === teamId) return
    if (!window.confirm('Delete this team?')) return
    setDeletingTeamId(teamId)
    setApiError(null)
    try {
      await deleteTeam(selected, teamId)
      await loadStructure(selected)
    } catch (err) {
      setApiError(err.message)
    } finally {
      setDeletingTeamId(null)
    }
  }

  const buildScoreInputs = (seasonData) => {
    const map = {}
    seasonData?.weeks?.forEach((week) => {
      week.games.forEach((g) => {
        map[g.id] = { home_score: g.home_score ?? 0, away_score: g.away_score ?? 0 }
      })
    })
    setScoreInputs(map)
  }

  const loadSchedule = async () => {
    if (!selected || !scheduleYear) return
    setLoadingSchedule(true)
    setApiError(null)
    try {
      const data = await getSchedule(selected, scheduleYear)
      setSchedule(data)
      buildScoreInputs(data)
    } catch (err) {
      setApiError(err.message)
      setSchedule(null)
    } finally {
      setLoadingSchedule(false)
    }
  }

  const handleGenerateSchedule = async (evt) => {
    evt.preventDefault()
    if (!selected || !scheduleYear) return
    setApiError(null)
    setLoadingSchedule(true)
    try {
      await generateSeason(selected, Number(scheduleYear))
      await loadSchedule()
      await loadStandings(selected, scheduleYear)
      await loadSeeds(selected, scheduleYear)
      await loadBracket(selected, scheduleYear)
    } catch (err) {
      setApiError(err.message)
    } finally {
      setLoadingSchedule(false)
    }
  }

  const handleCompleteGame = async (gameId) => {
    if (!selected || !scheduleYear) return
    const scores = scoreInputs[gameId] || {}
    if (scores.home_score === undefined || scores.away_score === undefined) {
      setApiError('Enter scores for both teams.')
      return
    }
    setApiError(null)
    try {
      await completeGame(gameId, Number(scores.home_score), Number(scores.away_score))
      await loadSchedule()
      await loadStandings(selected, scheduleYear)
      await loadSeeds(selected, scheduleYear)
      await loadBracket(selected, scheduleYear)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const updateScoreInput = (gameId, field, value) => {
    setScoreInputs((prev) => ({
      ...prev,
      [gameId]: {
        ...(prev[gameId] || {}),
        [field]: value,
      },
    }))
  }

  const loadStandings = async (leagueIdParam, yearParam) => {
    const leagueId = leagueIdParam || selected
    const yr = yearParam || scheduleYear
    if (!leagueId || !yr) return
    setLoadingStandings(true)
    setApiError(null)
    try {
      const data = await getStandings(leagueId, yr)
      setStandings(data)
    } catch (err) {
      setApiError(err.message)
      setStandings([])
    } finally {
      setLoadingStandings(false)
    }
  }

  const loadSeeds = async (leagueIdParam, yearParam) => {
    const leagueId = leagueIdParam || selected
    const yr = yearParam || scheduleYear
    if (!leagueId || !yr) return
    setLoadingSeeds(true)
    setApiError(null)
    try {
      const data = await getPlayoffSeeds(leagueId, yr)
      setSeeds(data)
    } catch (err) {
      setApiError(err.message)
      setSeeds([])
    } finally {
      setLoadingSeeds(false)
    }
  }

  const loadBracket = async (leagueIdParam, yearParam) => {
    const leagueId = leagueIdParam || selected
    const yr = yearParam || scheduleYear
    if (!leagueId || !yr) return
    setLoadingBracket(true)
    setApiError(null)
    try {
      const data = await getPlayoffBracket(leagueId, yr)
      setBracket(data)
    } catch (err) {
      setApiError(err.message)
      setBracket([])
    } finally {
      setLoadingBracket(false)
    }
  }

  const handleRenameConf = async (confId, name) => {
    if (!selected || !name.trim()) return
    setApiError(null)
    try {
      await renameConference(selected, confId, name.trim())
      setEditingConfId(null)
      setConfRename('')
      await loadStructure(selected)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleRenameDiv = async (divId, name) => {
    if (!selected || !name.trim()) return
    setApiError(null)
    try {
      await renameDivision(selected, divId, name.trim())
      setEditingDivId(null)
      setDivRename('')
      await loadStructure(selected)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleTeamSubmit = async (evt) => {
    evt.preventDefault()
    if (!selected) return
    if (!teamForm.conference || !teamForm.division) {
      setApiError('Select a conference and division for the team.')
      return
    }
    setApiError(null)
    try {
      const { owner_email, ...rest } = teamForm
      const payload = {
        ...rest,
        name: teamForm.name || `${teamForm.city} ${teamForm.nickname}`,
        conference: Number(teamForm.conference),
        division: Number(teamForm.division),
        abbreviation: teamForm.abbreviation.toUpperCase(),
        stadium_capacity: Number(teamForm.stadium_capacity) || 0,
        owner_email_input: owner_email,
      }
      await createTeam(selected, payload)
      setTeamForm(defaultTeamForm)
      await loadStructure(selected)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleAddPlayer = async (evt) => {
    evt.preventDefault()
    if (!selected || !rosterTeam) return
    setApiError(null)
    try {
      const payload = {
        first_name: playerForm.first_name,
        last_name: playerForm.last_name,
        position: playerForm.position,
        age: Number(playerForm.age),
        contract: {
          salary: Number(playerForm.contract.salary),
          bonus: Number(playerForm.contract.bonus),
          years: Number(playerForm.contract.years),
          start_year: Number(playerForm.contract.start_year),
        },
      }
      await addRosterPlayer(selected, rosterTeam, payload)
      setPlayerForm(defaultPlayerForm)
      await loadRoster(rosterTeam)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleReleasePlayer = async (playerId) => {
    if (!selected || !rosterTeam) return
    setApiError(null)
    try {
      await releaseRosterPlayer(selected, rosterTeam, playerId)
      await loadRoster(rosterTeam)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleReleaseToWaivers = async (playerId) => {
    if (!selected) return
    setApiError(null)
    try {
      await releaseToWaivers(selected, playerId)
      await loadWaivers(selected)
      if (rosterTeam) await loadRoster(rosterTeam)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleClaimWaiver = async (waiverId) => {
    setApiError(null)
    try {
      await claimWaiver(waiverId)
      await loadWaivers(selected)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const loadWaivers = async (leagueId) => {
    if (!leagueId) return
    setApiError(null)
    try {
      const data = await listWaivers(leagueId)
      setWaivers(data)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const loadTradeRosters = async (fromTeamId, toTeamId) => {
    if (!selected) return
    setApiError(null)
    try {
      if (fromTeamId) {
        const data = await listRoster(selected, fromTeamId)
        setTradeFromRoster(data)
      } else {
        setTradeFromRoster([])
      }
      if (toTeamId) {
        const data = await listRoster(selected, toTeamId)
        setTradeToRoster(data)
      } else {
        setTradeToRoster([])
      }
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleTradeSubmit = async (evt) => {
    evt.preventDefault()
    if (!selected || !tradeState.from_team || !tradeState.to_team) return
    if (tradeState.from_team === tradeState.to_team) {
      setApiError("From/To teams must differ.")
      return
    }
    setApiError(null)
    try {
      const items = [
        ...tradeState.from_player_ids.map((pid) => ({
          player: pid,
          from_team: tradeState.from_team,
          to_team: tradeState.to_team,
        })),
        ...tradeState.to_player_ids.map((pid) => ({
          player: pid,
          from_team: tradeState.to_team,
          to_team: tradeState.from_team,
        })),
      ]
      const trade = await createTrade(selected, {
        from_team: tradeState.from_team,
        to_team: tradeState.to_team,
        items,
      })
      await acceptTrade(trade.id)
      setTradeState(defaultTradeState)
      await loadStructure(selected)
      await loadTradeRosters(tradeState.from_team, tradeState.to_team)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const handleContractSave = async (evt) => {
    evt.preventDefault()
    if (!selected || !contractPlayerId) return
    setApiError(null)
    try {
      const payload = {
        salary: Number(contractForm.salary),
        bonus: Number(contractForm.bonus),
        years: Number(contractForm.years),
        start_year: Number(contractForm.start_year),
      }
      await updateContract(selected, contractPlayerId, payload)
      setContractForm(defaultContractForm)
      setContractPlayerId('')
      if (rosterTeam) await loadRoster(rosterTeam)
    } catch (err) {
      setApiError(err.message)
    }
  }

  const selectedConference = useMemo(() => {
    if (!structure || !teamForm.conference) return null
    return structure.conferences.find((c) => c.id === Number(teamForm.conference))
  }, [structure, teamForm.conference])

  const divisions = selectedConference?.divisions || []

  return (
    <Section
      title="League + team management"
      subtitle="Phase 1 focus"
      action={
        <div className="row gap">
          {loadingLeagues && <Pill tone="neutral">Loading leagues…</Pill>}
          {loadingStructure && <Pill tone="neutral">Loading structure…</Pill>}
        </div>
      }
    >
      {!user && <p className="muted">Sign in to create leagues and teams.</p>}
      {user && (
        <>
          <div className="card-grid">
            <div className="subcard">
              <div className="row space">
                <div>
                  <p className="eyebrow">Your leagues</p>
                  <h4>{leagues.length ? `${leagues.length} league(s)` : 'No leagues yet'}</h4>
                </div>
                <select
                  value={selected || ''}
                  onChange={(e) => setSelected(Number(e.target.value) || null)}
                  disabled={!leagues.length}
                >
                  <option value="">Select league</option>
                  {leagues.map((league) => (
                    <option key={league.id} value={league.id}>
                      {league.name}
                    </option>
                  ))}
                </select>
                <button type="button" className="ghost" onClick={handleDeleteLeague} disabled={!selected}>
                  Delete league
                </button>
              </div>
              {structure && (
                <div className="structure-meta">
                  <Pill tone="neutral">{structure.conference_count} conferences</Pill>
                  <Pill tone="neutral">
                    {structure.division_count_per_conference} divisions / conference
                  </Pill>
                  <Pill tone="neutral">{structure.teams_per_division} teams / division</Pill>
                  <Pill tone="success">Cap: ${Number(structure.salary_cap).toLocaleString()}</Pill>
                </div>
              )}
              {apiError && <p className="error">{apiError}</p>}
            </div>
            <div className="subcard">
              <p className="eyebrow">Create league</p>
              <form className="form-grid" onSubmit={handleLeagueSubmit}>
                <label>
                  <span>League name</span>
                  <input
                    value={leagueForm.name}
                    onChange={(e) => setLeagueForm({ ...leagueForm, name: e.target.value })}
                    required
                  />
                </label>
                <label>
                  <span>Conferences</span>
                  <input
                    type="number"
                    min="1"
                    value={leagueForm.conference_count}
                    onChange={(e) =>
                      setLeagueForm({ ...leagueForm, conference_count: e.target.value })
                    }
                    required
                  />
                </label>
                <label>
                  <span>Divisions per conference</span>
                  <input
                    type="number"
                    min="1"
                    value={leagueForm.division_count_per_conference}
                    onChange={(e) =>
                      setLeagueForm({
                        ...leagueForm,
                        division_count_per_conference: e.target.value,
                      })
                    }
                    required
                  />
                </label>
                <label>
                  <span>Teams per division</span>
                  <input
                    type="number"
                    min="1"
                    value={leagueForm.teams_per_division}
                    onChange={(e) =>
                      setLeagueForm({ ...leagueForm, teams_per_division: e.target.value })
                    }
                    required
                  />
                </label>
                <label>
                  <span>Salary cap (USD)</span>
                  <input
                    type="number"
                    min="0"
                    step="1000000"
                    value={leagueForm.salary_cap}
                    onChange={(e) => setLeagueForm({ ...leagueForm, salary_cap: e.target.value })}
                    required
                  />
                </label>
                <label>
                  <span>Roster size limit</span>
                  <input
                    type="number"
                    min="1"
                    value={leagueForm.roster_size_limit}
                    onChange={(e) =>
                      setLeagueForm({ ...leagueForm, roster_size_limit: e.target.value })
                    }
                    required
                  />
                </label>
                <label>
                  <span>Free agency mode</span>
                  <select
                    value={leagueForm.free_agency_mode}
                    onChange={(e) =>
                      setLeagueForm({ ...leagueForm, free_agency_mode: e.target.value })
                    }
                  >
                    <option value="auction">Auction with end dates</option>
                    <option value="rounds">Round-based bidding (4 rounds)</option>
                  </select>
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={leagueForm.allow_cap_growth}
                    onChange={(e) =>
                      setLeagueForm({ ...leagueForm, allow_cap_growth: e.target.checked })
                    }
                  />
                  <span>Allow cap growth year over year</span>
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={leagueForm.allow_playoff_expansion}
                    onChange={(e) =>
                      setLeagueForm({
                        ...leagueForm,
                        allow_playoff_expansion: e.target.checked,
                      })
                    }
                  />
                  <span>Allow playoff expansion toggle</span>
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={leagueForm.enable_realignment}
                    onChange={(e) =>
                      setLeagueForm({
                        ...leagueForm,
                        enable_realignment: e.target.checked,
                      })
                    }
                  />
                  <span>Enable realignment and relocation</span>
                </label>
                <button className="primary" type="submit" disabled={loadingLeagues}>
                  Create league
                </button>
              </form>
            </div>
          </div>

          <div className="card-grid">
            <div className="subcard">
              <p className="eyebrow">Add team</p>
              <form className="form-grid" onSubmit={handleTeamSubmit}>
                <label>
                  <span>Team name</span>
                  <input
                    value={teamForm.name}
                    onChange={(e) => setTeamForm({ ...teamForm, name: e.target.value })}
                    placeholder="e.g., City Nickname"
                  />
                </label>
                <label>
                  <span>Conference</span>
                  <select
                    value={teamForm.conference}
                    onChange={(e) => setTeamForm({ ...teamForm, conference: e.target.value })}
                    required
                  >
                    <option value="">Select conference</option>
                    {structure?.conferences.map((conf) => (
                      <option key={conf.id} value={conf.id}>
                        {conf.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Division</span>
                  <select
                    value={teamForm.division}
                    onChange={(e) => setTeamForm({ ...teamForm, division: e.target.value })}
                    required
                    disabled={!divisions.length}
                  >
                    <option value="">Select division</option>
                    {divisions.map((div) => (
                      <option key={div.id} value={div.id}>
                        {div.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>City</span>
                  <input
                    value={teamForm.city}
                    onChange={(e) => setTeamForm({ ...teamForm, city: e.target.value })}
                    required
                  />
                </label>
                <label>
                  <span>Owner email (optional)</span>
                  <input
                    type="email"
                    value={teamForm.owner_email}
                    onChange={(e) => setTeamForm({ ...teamForm, owner_email: e.target.value })}
                    placeholder="owner@example.com"
                  />
                </label>
                <label>
                  <span>Nickname</span>
                  <input
                    value={teamForm.nickname}
                    onChange={(e) => setTeamForm({ ...teamForm, nickname: e.target.value })}
                    required
                  />
                </label>
                <label>
                  <span>Abbreviation</span>
                  <input
                    maxLength={5}
                    value={teamForm.abbreviation}
                    onChange={(e) =>
                      setTeamForm({ ...teamForm, abbreviation: e.target.value.toUpperCase() })
                    }
                    required
                  />
                </label>
                <label>
                  <span>Primary color</span>
                  <input
                    type="color"
                    value={teamForm.primary_color}
                    onChange={(e) =>
                      setTeamForm({ ...teamForm, primary_color: e.target.value })
                    }
                  />
                </label>
                <label>
                  <span>Secondary color</span>
                  <input
                    type="color"
                    value={teamForm.secondary_color}
                    onChange={(e) =>
                      setTeamForm({ ...teamForm, secondary_color: e.target.value })
                    }
                  />
                </label>
                <label>
                  <span>Stadium name</span>
                  <input
                    value={teamForm.stadium_name}
                    onChange={(e) => setTeamForm({ ...teamForm, stadium_name: e.target.value })}
                    placeholder="e.g., Memorial Stadium"
                  />
                </label>
                <label>
                  <span>Stadium capacity</span>
                  <input
                    type="number"
                    min="10000"
                    value={teamForm.stadium_capacity}
                    onChange={(e) =>
                      setTeamForm({ ...teamForm, stadium_capacity: e.target.value })
                    }
                  />
                </label>
                <label>
                  <span>Turf type</span>
                  <select
                    value={teamForm.stadium_turf}
                    onChange={(e) => setTeamForm({ ...teamForm, stadium_turf: e.target.value })}
                  >
                    <option value="grass">Grass</option>
                    <option value="turf">Turf</option>
                    <option value="hybrid">Hybrid</option>
                  </select>
                </label>
                <label>
                  <span>Weather profile</span>
                  <select
                    value={teamForm.stadium_weather}
                    onChange={(e) =>
                      setTeamForm({ ...teamForm, stadium_weather: e.target.value })
                    }
                  >
                    <option value="temperate">Temperate</option>
                    <option value="cold">Cold / winter</option>
                    <option value="dome">Dome</option>
                    <option value="extreme">Extreme</option>
                  </select>
                </label>
                <button className="primary" type="submit" disabled={!selected}>
                  Add team
                </button>
              </form>
            </div>
            <div className="subcard">
              <p className="eyebrow">Structure + teams</p>
              {!structure && <p className="muted">Select a league to view its conferences and divisions.</p>}
              {structure && (
                <div className="structure-grid">
                  {structure.conferences.map((conf) => (
                    <div key={conf.id} className="panel">
                      <div className="panel-head">
                        <div>
                          <p className="eyebrow">Conference</p>
                          <h5>{conf.name}</h5>
                          {editingConfId === conf.id ? (
                            <div className="inline-form">
                              <input
                                className="inline-input"
                                value={confRename}
                                onChange={(e) => setConfRename(e.target.value)}
                                placeholder="New name"
                              />
                              <button
                                type="button"
                                className="ghost"
                                onClick={() => handleRenameConf(conf.id, confRename)}
                              >
                                Save
                              </button>
                              <button
                                type="button"
                                className="ghost"
                                onClick={() => {
                                  setEditingConfId(null)
                                  setConfRename('')
                                }}
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              type="button"
                              className="ghost tiny-button"
                              onClick={() => {
                                setEditingConfId(conf.id)
                                setConfRename(conf.name)
                              }}
                            >
                              Edit name
                            </button>
                          )}
                        </div>
                        <Pill tone="neutral">{conf.divisions.length} divisions</Pill>
                      </div>
                      <div className="division-grid">
                        {conf.divisions.map((div) => (
                          <div key={div.id} className="division-card">
                            <div className="panel-head">
                              <div>
                                <p className="eyebrow">Division</p>
                                <h6>{div.name}</h6>
                                {editingDivId === div.id ? (
                                  <div className="inline-form">
                                    <input
                                      className="inline-input"
                                      value={divRename}
                                      onChange={(e) => setDivRename(e.target.value)}
                                      placeholder="New name"
                                    />
                                    <button
                                      type="button"
                                      className="ghost"
                                      onClick={() => handleRenameDiv(div.id, divRename)}
                                    >
                                      Save
                                    </button>
                                    <button
                                      type="button"
                                      className="ghost"
                                      onClick={() => {
                                        setEditingDivId(null)
                                        setDivRename('')
                                      }}
                                    >
                                      Cancel
                                    </button>
                                  </div>
                                ) : (
                                  <button
                                    type="button"
                                    className="ghost tiny-button"
                                    onClick={() => {
                                      setEditingDivId(div.id)
                                      setDivRename(div.name)
                                    }}
                                  >
                                    Edit name
                                  </button>
                                )}
                              </div>
                              <Pill tone={div.teams.length ? 'success' : 'warn'}>
                                {div.teams.length} team(s)
                              </Pill>
                            </div>
                            <ul className="team-list">
                              {div.teams.length === 0 && <li className="muted">No teams yet</li>}
                              {div.teams.map((team) => (
                                <li key={team.id}>
                                  <span className="dot" style={{ background: team.primary_color }} />
                                  <strong>{team.abbreviation}</strong> {team.city} {team.nickname}
                                  {team.owner_email && (
                                    <span className="muted" style={{ marginLeft: '0.5rem' }}>
                                      Owner: {team.owner_email}
                                    </span>
                                  )}
                                  {(team.stadium_name || team.stadium_capacity) && (
                                    <span className="muted" style={{ marginLeft: '0.5rem' }}>
                                      {team.stadium_name || 'Stadium'} · {team.stadium_capacity?.toLocaleString?.() || team.stadium_capacity} ·{' '}
                                      {team.stadium_turf}
                                    </span>
                                  )}
                                  <button
                                    type="button"
                                    className="ghost"
                                    style={{ marginLeft: 'auto' }}
                                    onClick={() => loadRoster(team.id)}
                                  >
                                    View roster
                                  </button>
                                  <button
                                    type="button"
                                    className="ghost"
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      if (window.confirm('Delete this team?')) handleDeleteTeam(team.id)
                                    }}
                                  >
                                    Delete
                                  </button>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="card-grid">
            <div className="subcard">
              <div className="row space">
                <div>
                  <p className="eyebrow">Schedule</p>
                  <h4>Generate + record results</h4>
                </div>
                <form className="row gap" onSubmit={handleGenerateSchedule}>
                  <label className="row gap" style={{ alignItems: 'center' }}>
                    <span className="muted">Year</span>
                    <input
                      type="number"
                      value={scheduleYear}
                      onChange={(e) => setScheduleYear(Number(e.target.value))}
                      style={{ width: 90 }}
                      min="2024"
                    />
                  </label>
                  <button className="primary" type="submit" disabled={!selected || loadingSchedule}>
                    Generate schedule
                  </button>
                  <button
                    type="button"
                    className="ghost"
                    onClick={loadSchedule}
                    disabled={!selected || loadingSchedule}
                  >
                    Load schedule
                  </button>
                </form>
              </div>
              {loadingSchedule && <p className="muted">Loading schedule…</p>}
              {!loadingSchedule && !schedule && <p className="muted">Generate or load a schedule for this league.</p>}
              {!loadingSchedule && schedule && (
                <div className="scroll-card" style={{ maxHeight: 420 }}>
                  {schedule.weeks?.map((week) => (
                    <div key={week.id} className="division-card" style={{ marginBottom: '0.75rem' }}>
                      <div className="row space">
                        <h6>
                          Week {week.number} {week.is_playoffs ? '(Playoffs)' : ''}
                        </h6>
                      </div>
                      <table className="table">
                        <thead>
                          <tr>
                            <th>Matchup</th>
                            <th>Status</th>
                            <th className="actions">Score / action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {week.games.length === 0 && (
                            <tr>
                              <td colSpan={3} className="muted">
                                No games scheduled
                              </td>
                            </tr>
                          )}
                          {week.games.map((g) => (
                            <tr key={g.id}>
                              <td>
                                {g.away_team_abbr} @ {g.home_team_abbr}
                              </td>
                              <td>{g.status}</td>
                              <td className="actions">
                                {g.status === 'completed' ? (
                                  <span>
                                    {g.away_score} - {g.home_score}
                                  </span>
                                ) : (
                                  <div className="row gap">
                                    <input
                                      type="number"
                                      min="0"
                                      value={scoreInputs[g.id]?.away_score ?? ''}
                                      onChange={(e) => updateScoreInput(g.id, 'away_score', e.target.value)}
                                      style={{ width: 70 }}
                                      placeholder="Away"
                                    />
                                    <input
                                      type="number"
                                      min="0"
                                      value={scoreInputs[g.id]?.home_score ?? ''}
                                      onChange={(e) => updateScoreInput(g.id, 'home_score', e.target.value)}
                                      style={{ width: 70 }}
                                      placeholder="Home"
                                    />
                                    <button className="ghost" type="button" onClick={() => handleCompleteGame(g.id)}>
                                      Final
                                    </button>
                                  </div>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="subcard">
              <div className="row space">
                <div>
                  <p className="eyebrow">Standings</p>
                  <h4>Auto from completed games</h4>
                </div>
                <div className="row gap">
                  <button className="ghost" onClick={() => loadStandings(selected, scheduleYear)} disabled={!selected || loadingStandings}>
                    Refresh
                  </button>
                </div>
              </div>
              {loadingStandings && <p className="muted">Loading standings…</p>}
              {!loadingStandings && standings.length === 0 && <p className="muted">No results yet.</p>}
              {!loadingStandings && standings.length > 0 && (
                <div className="scroll-card" style={{ maxHeight: 420 }}>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Team</th>
                        <th>W</th>
                        <th>L</th>
                        <th>PF</th>
                        <th>PA</th>
                        <th>Conf / Div</th>
                      </tr>
                    </thead>
                    <tbody>
                      {standings.map((s) => (
                        <tr key={s.team_id}>
                          <td>{s.abbreviation}</td>
                          <td>{s.wins}</td>
                          <td>{s.losses}</td>
                          <td>{s.points_for}</td>
                          <td>{s.points_against}</td>
                          <td>
                            {s.conference} / {s.division}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="subcard">
              <div className="row space">
                <div>
                  <p className="eyebrow">Playoff seeds</p>
                  <h4>Top teams snapshot</h4>
                </div>
                <div className="row gap">
                  <button className="ghost" onClick={() => loadSeeds(selected, scheduleYear)} disabled={!selected || loadingSeeds}>
                    Refresh
                  </button>
                  <button className="ghost" onClick={() => loadBracket(selected, scheduleYear)} disabled={!selected || loadingBracket}>
                    Refresh bracket
                  </button>
                </div>
              </div>
              {loadingSeeds && <p className="muted">Loading seeds…</p>}
              {!loadingSeeds && seeds.length === 0 && <p className="muted">No seeds yet. Complete games to populate.</p>}
              {!loadingSeeds && seeds.length > 0 && (
                <div className="scroll-card" style={{ maxHeight: 300 }}>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Seed</th>
                        <th>Team</th>
                        <th>W</th>
                        <th>L</th>
                        <th>PF</th>
                        <th>PA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {seeds.map((s) => (
                        <tr key={s.team_id}>
                          <td>{s.seed}</td>
                          <td>{s.abbreviation}</td>
                          <td>{s.wins}</td>
                          <td>{s.losses}</td>
                          <td>{s.points_for}</td>
                          <td>{s.points_against}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {seeds.length > 0 && (
            <div className="card-grid">
              <div className="subcard">
                <div className="row space">
                  <div>
                    <p className="eyebrow">Bracket preview</p>
                    <h4>Auto-paired from seeds</h4>
                  </div>
                </div>
                <div className="division-card">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Matchup</th>
                        <th>Seed vs Seed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bracket.map((pair, idx) => (
                        <tr key={idx}>
                          <td>
                            {pair.higher_seed?.abbreviation || 'Bye'} vs {pair.lower_seed?.abbreviation || 'Bye'}
                          </td>
                          <td>
                            {pair.higher_seed?.seed ?? '-'} vs {pair.lower_seed?.seed ?? '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="muted" style={{ marginTop: '0.35rem' }}>
                    Placeholder pairing (1 vs last, 2 vs next, etc.). Final bracket rules can be applied later.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="card-grid">
            <div className="subcard">
              <div className="row space">
                <div>
                  <p className="eyebrow">Free agency</p>
                  <h4>{structure?.free_agency_mode === 'rounds' ? 'Round-based' : 'Auction'} mode</h4>
                </div>
                <div className="row gap">
                  <button className="ghost" type="button" onClick={loadFreeAgents} disabled={!selected || loadingFA}>
                    Refresh pool
                  </button>
                  <button className="ghost" type="button" onClick={handleResolveFA} disabled={!selected || resolvingFA}>
                    Resolve bids
                  </button>
                </div>
              </div>
              {loadingFA && <p className="muted">Loading free agents…</p>}
              {!loadingFA && (
                <div className="division-card">
                  <div className="row gap" style={{ marginBottom: '0.5rem' }}>
                    <span className="muted">Available: {freeAgents.length}</span>
                  </div>
                  <form className="row gap" onSubmit={handleBidFA} style={{ marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                    <select
                      value={faOffer.player}
                      onChange={(e) => setFaOffer({ ...faOffer, player: e.target.value })}
                      required
                      style={{ minWidth: 200 }}
                    >
                      <option value="">Choose player</option>
                      {freeAgents.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.first_name} {p.last_name} ({p.position}) · OVR {p.overall_rating}
                        </option>
                      ))}
                    </select>
                    <select
                      value={faOffer.team}
                      onChange={(e) => setFaOffer({ ...faOffer, team: e.target.value })}
                      required
                      style={{ minWidth: 180 }}
                    >
                      <option value="">Team</option>
                      {teamsFlat.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.abbreviation} · {t.city}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min="0"
                      step="100000"
                      value={faOffer.amount}
                      onChange={(e) => setFaOffer({ ...faOffer, amount: e.target.value })}
                      style={{ width: 140 }}
                    />
                    <button className="primary" type="submit">
                      {structure?.free_agency_mode === 'rounds' ? 'Submit claim' : 'Place bid'}
                    </button>
                  </form>
                  <div className="scroll-card" style={{ maxHeight: 260 }}>
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Player</th>
                          <th>Pos</th>
                          <th>OVR</th>
                        </tr>
                      </thead>
                      <tbody>
                        {freeAgents.length === 0 && (
                          <tr>
                            <td colSpan={3} className="muted">
                              No free agents available
                            </td>
                          </tr>
                        )}
                        {freeAgents.map((p) => (
                          <tr key={p.id}>
                            <td>
                              {p.first_name} {p.last_name}
                            </td>
                            <td>{p.position}</td>
                            <td>{p.overall_rating}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
            <div className="subcard">
              <div className="row space">
                <div>
                  <p className="eyebrow">Injuries</p>
                  <h4>Track availability</h4>
                </div>
                <div className="row gap">
                  <button className="ghost" type="button" onClick={loadInjuries} disabled={!selected || loadingInjuries}>
                    Refresh injuries
                  </button>
                </div>
              </div>
              {loadingInjuries && <p className="muted">Loading injuries…</p>}
              {!loadingInjuries && (
                <>
                  <form className="row gap" onSubmit={handleCreateInjury} style={{ marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                    <select
                      value={newInjury.player}
                      onChange={(e) => setNewInjury({ ...newInjury, player: e.target.value })}
                      style={{ minWidth: 200 }}
                      required
                    >
                      <option value="">Select roster player</option>
                      {roster.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.first_name} {p.last_name} ({p.position})
                        </option>
                      ))}
                    </select>
                    <select
                      value={newInjury.severity}
                      onChange={(e) => setNewInjury({ ...newInjury, severity: e.target.value })}
                    >
                      <option value="minor">Minor</option>
                      <option value="moderate">Moderate</option>
                      <option value="major">Major</option>
                    </select>
                    <input
                      type="number"
                      min="1"
                      value={newInjury.duration_weeks}
                      onChange={(e) => setNewInjury({ ...newInjury, duration_weeks: e.target.value })}
                      style={{ width: 120 }}
                    />
                    <button className="primary" type="submit">
                      Add injury
                    </button>
                  </form>
                  <div className="scroll-card" style={{ maxHeight: 260 }}>
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Player</th>
                          <th>Severity</th>
                          <th>Weeks</th>
                          <th>Status</th>
                          <th className="actions">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {injuries.length === 0 && (
                          <tr>
                            <td colSpan={5} className="muted">
                              No injuries recorded
                            </td>
                          </tr>
                        )}
                        {injuries.map((inj) => (
                          <tr key={inj.id}>
                            <td>{inj.player_name}</td>
                            <td>{inj.severity}</td>
                            <td>{inj.duration_weeks}</td>
                            <td>{inj.status}</td>
                            <td className="actions">
                              {inj.status === 'active' && (
                                <button className="ghost" onClick={() => handleResolveInjury(inj.id)}>
                                  Mark healed
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
            <div className="subcard">
              <div className="row space">
                <div>
                  <p className="eyebrow">Notifications</p>
                  <h4>Recent</h4>
                </div>
                <div className="row gap">
                  <button className="ghost" type="button" onClick={loadNotifications}>
                    Refresh
                  </button>
                </div>
              </div>
              <div className="scroll-card" style={{ maxHeight: 260 }}>
                <ul className="team-list">
                  {notifications.length === 0 && <li className="muted">No notifications</li>}
                  {notifications.map((n) => (
                    <li key={n.id}>
                      <span>{n.message}</span>
                      {!n.is_read && (
                        <button className="ghost tiny-button" style={{ marginLeft: 'auto' }} onClick={() => handleMarkNotification(n.id)}>
                          Mark read
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>


          <div className="card-grid">
            <div className="subcard">
              <div className="row space">
                <div>
                  <p className="eyebrow">Drafts</p>
                  <h4>Startup / rookie draft</h4>
                </div>
                <div className="row gap">
                  <button className="primary" type="button" onClick={handleCreateDraft} disabled={!selected || loadingDraft}>
                    Create draft
                  </button>
                  <input
                    type="number"
                    placeholder="Draft ID"
                    value={draftIdInput}
                    onChange={(e) => setDraftIdInput(e.target.value)}
                    style={{ width: 110 }}
                  />
                  <button className="ghost" type="button" onClick={handleLoadDraft} disabled={!draftIdInput || loadingDraft}>
                    Load draft
                  </button>
                  <button className="ghost" type="button" onClick={handleGenerateRookies} disabled={!selected || loadingRookies}>
                    Generate rookies
                  </button>
                  <button className="ghost" type="button" onClick={() => loadRookies(selected)} disabled={!selected || loadingRookies}>
                    Refresh pool
                  </button>
                </div>
              </div>
              {loadingDraft && <p className="muted">Working…</p>}
              {!loadingDraft && !draft && <p className="muted">Create or load a draft to view picks.</p>}
              {!loadingDraft && draft && (
                <div className="division-card">
                  <p className="eyebrow">
                    Draft #{draft.id} · {draft.draft_type} · {draft.rounds} rounds
                  </p>
                  <div className="row gap" style={{ marginBottom: '0.5rem' }}>
                    <span className="muted">Rookie pool: {rookies.length}</span>
                    {loadingRookies && <Pill tone="neutral">Loading rookies…</Pill>}
                  </div>
                  <div className="card-grid" style={{ gridTemplateColumns: "1.5fr 1fr" }}>
                    <div className="subcard" style={{ background: "#f8fafc" }}>
                      <p className="eyebrow">Picks</p>
                      <table className="table">
                        <thead>
                          <tr>
                            <th>Pick</th>
                            <th>Team</th>
                            <th>Player</th>
                            <th>Status</th>
                            <th className="actions">Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {draft.picks.map((p) => (
                            <tr key={p.id}>
                              <td>R{p.round_number} · #{p.overall_number}</td>
                              <td>{p.team_abbr}</td>
                              <td>{p.player_name || '—'}</td>
                              <td>{p.is_selected ? 'Selected' : 'Pending'}</td>
                              <td className="actions">
                                {!p.is_selected && (
                                  <button
                                    type="button"
                                    className={selectedPickId === p.id ? 'primary' : 'ghost'}
                                    onClick={() => {
                                      setSelectedPickId(p.id)
                                      setDraftIdInput(draft.id)
                                    }}
                                  >
                                    Select
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {selectedPickId && (
                        <form className="row gap" onSubmit={handleSelectPick} style={{ marginTop: '0.5rem' }}>
                          <select
                            value={pickPlayerId}
                            onChange={(e) => setPickPlayerId(e.target.value)}
                            style={{ minWidth: 200 }}
                            required
                          >
                            <option value="">Choose rookie</option>
                            {rookies.map((r) => (
                              <option key={r.id} value={r.id}>
                                {r.first_name} {r.last_name} ({r.position}) · OVR {r.overall_rating}
                              </option>
                            ))}
                          </select>
                          <button className="primary" type="submit" disabled={loadingDraft}>
                            Make pick
                          </button>
                          <button
                            type="button"
                            className="ghost"
                            onClick={() => {
                              setSelectedPickId(null)
                              setPickPlayerId('')
                            }}
                          >
                            Cancel
                          </button>
                        </form>
                      )}
                      <p className="muted" style={{ marginTop: '0.35rem' }}>
                        Rookie pool is generated per league; picks assign the player to the drafting team.
                      </p>
                    </div>
                    <div className="subcard" style={{ background: "#f8fafc" }}>
                      <p className="eyebrow">Rookie pool</p>
                      <div className="scroll-card" style={{ maxHeight: 240 }}>
                        <table className="table">
                          <thead>
                            <tr>
                              <th>Player</th>
                              <th>Pos</th>
                              <th>OVR</th>
                            </tr>
                          </thead>
                          <tbody>
                            {rookies.length === 0 && (
                              <tr>
                                <td colSpan={3} className="muted">
                                  No rookies yet
                                </td>
                              </tr>
                            )}
                            {rookies.map((r) => (
                              <tr key={r.id}>
                                <td>
                                  {r.first_name} {r.last_name}
                                </td>
                                <td>{r.position}</td>
                                <td>{r.overall_rating}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="card-grid">
            <div className="subcard">
              <p className="eyebrow">Roster</p>
              {!rosterTeam && <p className="muted">Select “View roster” on a team above to load players.</p>}
                  {rosterTeam && (
                    <div className="scroll-card">
                      {loadingRoster ? (
                        <p className="muted" style={{ padding: '0.75rem' }}>
                          Loading roster…
                        </p>
                      ) : (
                        <>
                          <div className="row space" style={{ padding: '0.5rem' }}>
                            <span className="muted">Roster size: {roster.length}</span>
                            <button
                              className="ghost"
                              onClick={() =>
                                downloadCsv(
                                  roster.map((p) => ({
                                    first_name: p.first_name,
                                    last_name: p.last_name,
                                    position: p.position,
                                    age: p.age,
                                    overall: p.overall_rating,
                                  })),
                                  'roster.csv',
                                )
                              }
                            >
                              Export CSV
                            </button>
                          </div>
                          <table className="table">
                            <thead>
                              <tr>
                                <th>Player</th>
                                <th>Pos</th>
                                <th>Age</th>
                                <th>Rating</th>
                                <th className="actions">Actions</th>
                              </tr>
                            </thead>
                            <tbody>
                              {roster.length === 0 && (
                                <tr>
                                  <td colSpan={5} className="muted">
                                    No players yet
                                  </td>
                                </tr>
                              )}
                              {roster.map((p) => (
                                <tr key={p.id}>
                                  <td>
                                    {p.first_name} {p.last_name}
                                  </td>
                                  <td>{p.position}</td>
                                  <td>{p.age}</td>
                                  <td>{p.overall_rating}</td>
                                  <td className="actions">
                                    <button className="ghost" onClick={() => handleReleasePlayer(p.id)}>
                                      Release
                                    </button>
                                    <button className="ghost" onClick={() => handleReleaseToWaivers(p.id)}>
                                      Waive
                                    </button>
                                    <button
                                      className="ghost"
                                      onClick={() => {
                                        setContractPlayerId(p.id)
                                        setContractForm(defaultContractForm)
                                      }}
                                    >
                                      Edit contract
                                    </button>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </>
                      )}
                    </div>
                  )}
                </div>

            <div className="subcard">
              <p className="eyebrow">Add player</p>
              {!rosterTeam && <p className="muted">Select a team roster first.</p>}
              {rosterTeam && (
                <form className="form-grid" onSubmit={handleAddPlayer}>
                  <label>
                    <span>First name</span>
                    <input
                      value={playerForm.first_name}
                      onChange={(e) => setPlayerForm({ ...playerForm, first_name: e.target.value })}
                      required
                    />
                  </label>
                  <label>
                    <span>Last name</span>
                    <input
                      value={playerForm.last_name}
                      onChange={(e) => setPlayerForm({ ...playerForm, last_name: e.target.value })}
                      required
                    />
                  </label>
                  <label>
                    <span>Position</span>
                    <select
                      value={playerForm.position}
                      onChange={(e) => setPlayerForm({ ...playerForm, position: e.target.value })}
                    >
                      {['QB','RB','WR','TE','OL','DL','LB','CB','S','K','P'].map((pos) => (
                        <option key={pos} value={pos}>{pos}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Age</span>
                    <input
                      type="number"
                      min="18"
                      value={playerForm.age}
                      onChange={(e) => setPlayerForm({ ...playerForm, age: e.target.value })}
                    />
                  </label>
                  <label>
                    <span>Salary (cap)</span>
                    <input
                      type="number"
                      min="0"
                      step="100000"
                      value={playerForm.contract.salary}
                      onChange={(e) =>
                        setPlayerForm({
                          ...playerForm,
                          contract: { ...playerForm.contract, salary: e.target.value },
                        })
                      }
                    />
                  </label>
                  <label>
                    <span>Bonus</span>
                    <input
                      type="number"
                      min="0"
                      step="100000"
                      value={playerForm.contract.bonus}
                      onChange={(e) =>
                        setPlayerForm({
                          ...playerForm,
                          contract: { ...playerForm.contract, bonus: e.target.value },
                        })
                      }
                    />
                  </label>
                  <label>
                    <span>Years</span>
                    <input
                      type="number"
                      min="1"
                      value={playerForm.contract.years}
                      onChange={(e) =>
                        setPlayerForm({
                          ...playerForm,
                          contract: { ...playerForm.contract, years: e.target.value },
                        })
                      }
                    />
                  </label>
                  <label>
                    <span>Start year</span>
                    <input
                      type="number"
                      min="2024"
                      value={playerForm.contract.start_year}
                      onChange={(e) =>
                        setPlayerForm({
                          ...playerForm,
                          contract: { ...playerForm.contract, start_year: e.target.value },
                        })
                      }
                    />
                  </label>
                  <button className="primary" type="submit">
                    Add to roster
                  </button>
                </form>
              )}
            </div>
          </div>

          <div className="card-grid">
            <div className="subcard">
              <p className="eyebrow">Trades</p>
              <form className="form-grid" onSubmit={handleTradeSubmit}>
                <label>
                  <span>From team</span>
                  <select
                    value={tradeState.from_team}
                    onChange={async (e) => {
                      const val = Number(e.target.value) || ''
                      setTradeState({ ...tradeState, from_team: val, from_player_ids: [] })
                      await loadTradeRosters(val, tradeState.to_team)
                    }}
                  >
                    <option value="">Select</option>
                    {teamsFlat.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.abbreviation} · {t.city} {t.nickname}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>To team</span>
                  <select
                    value={tradeState.to_team}
                    onChange={async (e) => {
                      const val = Number(e.target.value) || ''
                      setTradeState({ ...tradeState, to_team: val, to_player_ids: [] })
                      await loadTradeRosters(tradeState.from_team, val)
                    }}
                  >
                    <option value="">Select</option>
                    {teamsFlat.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.abbreviation} · {t.city} {t.nickname}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="subcard" style={{ gridColumn: "1 / -1" }}>
                  <p className="eyebrow">Players from “From team”</p>
                  {tradeFromRoster.length === 0 && <p className="muted">No roster loaded</p>}
                  <div className="team-list" style={{ maxHeight: 180, overflow: 'auto' }}>
                    {tradeFromRoster.map((p) => (
                      <label key={p.id} className="checkbox">
                        <input
                          type="checkbox"
                          checked={tradeState.from_player_ids.includes(p.id)}
                          onChange={(e) => {
                            const selected = tradeState.from_player_ids
                            const next = e.target.checked
                              ? [...selected, p.id]
                              : selected.filter((id) => id !== p.id)
                            setTradeState({ ...tradeState, from_player_ids: next })
                          }}
                        />
                        <span>
                          {p.first_name} {p.last_name} ({p.position})
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="subcard" style={{ gridColumn: "1 / -1" }}>
                  <p className="eyebrow">Players from “To team”</p>
                  {tradeToRoster.length === 0 && <p className="muted">No roster loaded</p>}
                  <div className="team-list" style={{ maxHeight: 180, overflow: 'auto' }}>
                    {tradeToRoster.map((p) => (
                      <label key={p.id} className="checkbox">
                        <input
                          type="checkbox"
                          checked={tradeState.to_player_ids.includes(p.id)}
                          onChange={(e) => {
                            const selected = tradeState.to_player_ids
                            const next = e.target.checked
                              ? [...selected, p.id]
                              : selected.filter((id) => id !== p.id)
                            setTradeState({ ...tradeState, to_player_ids: next })
                          }}
                        />
                        <span>
                          {p.first_name} {p.last_name} ({p.position})
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
                <button className="primary" type="submit" style={{ gridColumn: "1 / -1" }}>
                  Propose & accept trade
                </button>
              </form>
            </div>

            <div className="subcard">
              <p className="eyebrow">Waivers</p>
              {!selected && <p className="muted">Select a league to view waivers.</p>}
              {selected && (
                <>
                  <div className="row gap">
                    <button className="ghost" onClick={() => loadWaivers(selected)}>
                      Refresh waivers
                    </button>
                    <button
                      className="ghost"
                      onClick={() =>
                        downloadCsv(
                          waivers.map((w) => ({
                            player: w.player_name,
                            from_team: w.from_team_abbr,
                            status: w.status,
                            claimed_by: w.claimed_by_abbr || '',
                          })),
                          'waivers.csv',
                        )
                      }
                      disabled={!waivers.length}
                    >
                      Export CSV
                    </button>
                  </div>
                  <div className="scroll-card" style={{ marginTop: '0.5rem' }}>
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Player</th>
                          <th>From</th>
                          <th>Status</th>
                          <th className="actions">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {waivers.length === 0 && (
                          <tr>
                            <td colSpan={4} className="muted">
                              No waivers currently listed
                            </td>
                          </tr>
                        )}
                        {waivers.map((w) => (
                          <tr key={w.id}>
                            <td>{w.player_name}</td>
                            <td>{w.from_team_abbr}</td>
                            <td>{w.status}</td>
                            <td className="actions">
                              {w.status === 'open' && (
                                <button className="primary" onClick={() => handleClaimWaiver(w.id)}>
                                  Claim
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>

            <div className="subcard">
              <p className="eyebrow">Contract edit</p>
              {!contractPlayerId && <p className="muted">Select “Edit contract” on a roster player.</p>}
              {contractPlayerId && (
                <form className="form-grid" onSubmit={handleContractSave}>
                  <label>
                    <span>Salary</span>
                    <input
                      type="number"
                      min="0"
                      step="100000"
                      value={contractForm.salary}
                      onChange={(e) => setContractForm({ ...contractForm, salary: e.target.value })}
                    />
                  </label>
                  <label>
                    <span>Bonus</span>
                    <input
                      type="number"
                      min="0"
                      step="100000"
                      value={contractForm.bonus}
                      onChange={(e) => setContractForm({ ...contractForm, bonus: e.target.value })}
                    />
                  </label>
                  <label>
                    <span>Years</span>
                    <input
                      type="number"
                      min="1"
                      value={contractForm.years}
                      onChange={(e) => setContractForm({ ...contractForm, years: e.target.value })}
                    />
                  </label>
                  <label>
                    <span>Start year</span>
                    <input
                      type="number"
                      min="2024"
                      value={contractForm.start_year}
                      onChange={(e) =>
                        setContractForm({ ...contractForm, start_year: e.target.value })
                      }
                    />
                  </label>
                  <div className="row">
                    <button className="primary" type="submit">
                      Save contract
                    </button>
                    <button
                      className="ghost"
                      type="button"
                      onClick={() => {
                        setContractPlayerId('')
                        setContractForm(defaultContractForm)
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </>
      )}
    </Section>
  )
}

function AppShell() {
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    const check = async () => {
      try {
        await health()
        setApiStatus('ok')
      } catch (err) {
        setApiStatus('down')
      }
    }
    check()
  }, [])

  return (
    <main className="layout">
      <header className="hero">
        <div>
          <p className="eyebrow">WFL Simulator</p>
          <h1>Front-end kickoff</h1>
          <p className="lead">
            React + Django sessions with CSRF support. Create a league, wire up teams, and use this
            as the base for rosters, trades, drafts, and schedule tools in the next passes.
          </p>
          <div className="row gap">
            <Pill tone="neutral">Backend: Django + DRF</Pill>
            <Pill tone="neutral">Frontend: React (Vite)</Pill>
            <Pill tone={apiStatus === 'ok' ? 'success' : 'warn'}>API {apiStatus}</Pill>
          </div>
        </div>
      </header>

      <div className="grid">
        <AuthPanel apiStatus={apiStatus} />
      </div>

      <LeagueManager />
    </main>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  )
}

export default App
const downloadCsv = (rows, filename) => {
  if (!rows || rows.length === 0) return
  const headers = Object.keys(rows[0])
  const escape = (val) => {
    if (val == null) return ''
    const str = String(val)
    if (str.includes('"') || str.includes(',') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`
    }
    return str
  }
  const csv = [headers.join(',')]
  rows.forEach((row) => {
    csv.push(headers.map((h) => escape(row[h])).join(','))
  })
  const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
