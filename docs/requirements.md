# Web-Based Professional Football Simulation – Requirements

## Product Goals
- Provide a multi-user NFL-style simulation league where owners manage all team operations and simulate multiple seasons.
- Preserve complete historical records (per play → career) with rich stats and visualizations.
- Offer flexible commissioner controls for league setup, rules, scheduling, and oversight.

## In-Scope (MVP unless noted)
- Multiple leagues; custom teams/divisions/conferences; expansion and relocation with stadium attributes (capacity, turf, weather profile, revenue impact).
- Play-by-play simulation engine with bulk week/season sims and a single-game live-view feed; initial ratings-based probabilistic model with room to deepen fidelity.
- Full season lifecycle: preseason, regular season, playoffs, offseason (re-signings, free agency, trades, draft, cap updates).
- Roster rules (size, positional mins/maxes), waivers, injury lists (IR, day-to-day), simple cap (salary + bonus) with payouts on cuts; rookie scale, extensions, franchise/transition tags; negotiation loop.
- Startup snake draft or default rosters; 4-round fixed rookie draft; free agency modes (auction with end dates vs round-based bidding for 4 rounds) chosen by commissioner.
- Trades of players/picks/future picks; no pre-approval but reversible by commissioner.
- Fictional player generation; progression for younger players, regression for older; yearly training camp allocations by position.
- Playbooks (formations) and gameplans (run/pass balance, deep vs quick, aggressiveness, 2-minute tendencies); future owner-designed plays.
- Coaching staff (HC/OC/DC/Scouting Director) affecting performance and scouting grades.
- Commissioner tools: schedule generation (NFL defaults) and overrides, tiebreakers/playoffs/overtime (NFL defaults), cap growth, playoff expansion, realignment, relocation/expansion controls.
- History and reporting: season snapshots, standings, awards, records, leaderboards, sortable stats, player cards with bio and year-by-year ratings, team dashboards, trade comparisons; CSV export.
- Multiplayer: multiple human owners per league; concurrent offseason actions with conflict resolution for bids/trades.
- Notifications: owner-selectable email (SMTP) and/or in-app for key events (offers, injuries, results).
- Auth: email/password with optional TOTP 2FA; roles: owner (GM/coach combined) and commissioner; audit logs for commish/owner actions and errors.
- UX: desktop-first, mobile-friendly; prioritized screens—league dashboard, roster/contracts, trade console with comparisons, draft room, free agency, game viewer/box scores/play feed, playbook/gameplan editor.

## Out of Scope (Near-Term)
- Human head-to-head gameplay (planned later).
- Public API and public read-only views (later).
- Advanced cap mechanics (dead money, restructures), complex bonus structures.
- External data imports (real players/teams).

## Non-Functional Requirements
- Performance: efficient multi-season sims; bulk sim should complete without noticeable delay for typical league sizes (target sizing set during perf testing).
- Reliability: protect against data loss during long sims; transactional integrity for roster moves/contracts/trades/drafts.
- Security: hashed passwords, TOTP 2FA option, rate limiting for auth; RBAC for commish vs owners; audit logs for admin/owner actions and system errors.
- Observability: structured logging for sims and league actions; metrics for sim throughput/duration; error monitoring hooks.
- Compliance: no specific GDPR/CCPA needs now; design for future data export/deletion if required.
- Testing: unit tests for rules/engine; integration tests for season flows; load tests for sim engine; CI running pytest.
- UX: responsive layouts; clear dashboards; accessible color/contrast where feasible.

## Data & Storage
- Database: PostgreSQL.
- Key entities: User (owner/commish), League, Conference/Division, Team, Stadium, Coach roles, Player, Contract, Draft (startup/rookie), DraftPick, FreeAgencySession/Bid, Trade, Waiver, Injury, Game, Play, Playbook/Formation/PlayDefinition (future), Gameplan/Tendency, Schedule/Week, Standing, Stat lines (play/game/season/career), AuditLog, NotificationPreference.
- Exports: CSV for key tables/stats; API exposure deferred.

## Integrations
- Email: SMTP (dev: local SMTP; prod: configurable service).
- 2FA: roll-your-own TOTP (e.g., pyotp).

## Constraints/Assumptions
- Must run locally (laptop) and be hostable on a server later.
- Owners can act on their team and as commish only if flagged; no separate GM/coach roles.
- Sim is authoritative; no interactive in-game controls in MVP.

## Acceptance Criteria (High-Level)
- Create/manage leagues with commish controls for rules, schedules, FA mode, cap growth, playoff expansion, realignment.
- Manage rosters/contracts/cap within configured limits; execute trades and reversals; run startup and rookie drafts; run FA modes and waivers.
- Simulate games and weeks with play-by-play output, gameplans applied, stats persisted, standings/playoffs updated.
- View dashboards, player cards, histories, leaderboards, trade comparisons; export CSV; receive chosen notifications.
- Auth with email/password and optional TOTP; audit logs persisted; admin console for commish actions (via Django admin and UI).
