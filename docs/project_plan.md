# Project Plan – Web Football Simulation (Django + DRF + React + Postgres)

## Milestones (stack fixed)
- Phase 0: Foundations
- Phase 1: League + Roster Core
- Phase 2: Season Lifecycle
- Phase 3: Simulation Engine v1
- Phase 4: Reporting + UX
- Phase 5: Hardening + Deploy Prep

## Phase 0 – Foundations (1–2 wks)
**Goals**: Project skeletons, environment, auth baseline, admin, CI.
- Django + DRF project; React app bootstrapped; shared Docker/dev env; Postgres config.
- User model with commish flag; email/password auth; TOTP option scaffold; rate limiting for auth endpoints.
- Django admin enabled for key entities (User, League, Team) to unblock commish controls.
- CI running pytest; formatting/linting baseline.
**Acceptance**:
- `docker-compose up` (or documented local script) runs API + DB + frontend dev server.
- Create users, leagues, teams via admin; JWT/session auth usable; TOTP flow stubbed or working.
- CI green on lint/tests.

## Phase 1 – League + Roster Core (2–3 wks)
**Status**: Implemented (UI + API); minor polish possible.
**Goals**: League creation, teams, rosters, contracts, trades, audit logs.
- League creation wizard (React) with commish settings: league size, divisions/conferences, FA mode, cap growth toggle, playoff expansion toggle, realignment enabled, schedule defaults. **Done (UI/API)**
- Team ownership assignment; stadium data; relocation/expansion stubs. **Team CRUD + delete + owner/stadium fields in UI/API; relocation/expansion stubs pending**
- Roster rules enforcement (size, positional mins/maxes), waivers. **Roster add/release/waive + cap check in UI**
- Contracts: salary + bonus; simple cap check; payouts on cut; rookie scale, extensions, franchise/transition tags framework. **Cap check enforced on add; contract edit UI**
- Trades: players/picks/future picks; commish reversal path. **Basic trade UI: move players both ways; auto-accept**
- Audit logging for commish/owner actions. **Expanded to delete actions**
- CSV export scaffolding for rosters/contracts. **Roster/Waiver CSV export in UI**
- Rename conferences/divisions. **Inline edit controls in UI; commish-only**
**Acceptance (met except noted)**:
- Create league → add teams/owners → enforce roster rules and cap on add/cut/trade. **Owners/stadium entry working; relocation/expansion stubs pending**
- Execute trades and reversals; waivers process runs; audit entries recorded.
- Exports produce CSV for rosters/contracts.

## Phase 2 – Season Lifecycle (3–4 wks)
**Goals**: Schedule, standings/playoffs, drafts, free agency modes, injuries, notifications.
- Schedule generator (NFL defaults) with commish override; bye weeks; season/ week entities. **Round-robin generator + UI to generate/load schedules and enter results is live**
- Standings computation; playoff seeding/bracket (NFL rules). **Standings + seeds endpoints/UI wired; bracket endpoint + UI preview in place; full NFL bracket logic still pending**
- Startup snake draft (or default rosters) and 4-round rookie draft with fixed order; draft room UI. **Rookie pool generate/list + draft picker UI; picks assign rookies to teams; rookie pool TBD for realism**
- Free agency: auction with end dates vs round-based bidding (4 rounds) selectable at league setup.
- Waiver claims; conflict resolution rules for FA/bids/waivers.
- Injury system (severity/duration, day-to-day vs IR) with return-to-play logic.
- Notifications: in-app + SMTP stub; user preferences for channels.
**Acceptance**:
- Generate full season schedule; edit games manually as commish.
- Run startup draft → populate rosters; run rookie draft; run FA session in chosen mode; waivers resolve.
- Injuries applied and enforced on availability; notifications fire for key events.
- Playoffs bracket forms from standings and advances per results (even if simulated with placeholder).

## Phase 3 – Simulation Engine v1 (4–6 wks)
**Goals**: Ratings-driven play-by-play sim, stats persistence, gameplans, bulk + live view.
- Player ratings model; coaching modifiers; gameplan tendencies applied (run/pass balance, depth of target, aggressiveness, 2-minute).
- Play-by-play simulator producing drives/plays, scores, clock, penalties/turnovers; probabilistic outcomes based on ratings and tendencies.
- Bulk sim for weeks/seasons; single-game “live” feed (play log + box score).
- Persist per-play, per-game, per-season, career stats; standings update; playoff progression.
- Progression/regression model and yearly training camp allocations.
**Acceptance**:
- Run week/season sims via UI; results saved; standings update; playoffs advance.
- Live view shows play-by-play log and box score for a single game.
- Stats tables populated (offense/defense/special teams) with advanced metrics baseline.
- Progression/regression executed at season turn with training camp inputs.

## Phase 4 – Reporting + UX (3–4 wks)
**Goals**: Dashboards, player/team views, trade console, exports, commish tools polish, mobile-friendly.
- League dashboard (standings, leaders, news feed); team dashboard (roster/contracts/cap snapshot).
- Player cards (bio, ratings history, stats, injuries); comparisons for trades.
- Trade console with multi-asset trades (players/picks/cash), valuation aids, conflict handling.
- Leaders and records views; season snapshots; CSV exports for stats.
- Commish tools for cap growth, playoff expansion, realignment, relocation/expansion workflows.
- Responsive layouts for priority screens.
**Acceptance**:
- Navigate dashboards and player/team views; comparisons work in trade console.
- CSV exports for stats/leaders; records/season snapshots viewable.
- Commish can adjust cap growth, playoff size, and realign teams; relocation/expansion flows update teams/stadiums/schedules.

## Phase 5 – Hardening + Deploy Prep (2–3 wks)
**Goals**: Quality, performance, security, deploy scripts.
- Load/perf tests for sim throughput; profiling and optimizations.
- Security pass: auth rate limits, TOTP hardened, RBAC checks, audit log review.
- Error logging/monitoring hooks; backup/restore docs for DB.
- Deployment scripts/config (env vars, migrations, static build) for local → hosted server.
**Acceptance**:
- Perf targets documented with test results; main hotspots optimized.
- Auth + RBAC + audit verified; error logging surfaced.
- Repeatable deploy documented; migrations + static assets handled; CI green.

## Ongoing Backlog / Future
- Owner-designed plays; interactive live play-calling; human head-to-head games.
- Public API and read-only league sharing.
- Advanced cap mechanics (dead money, restructures).
- Real-time websockets for live feed; richer analytics/visualizations.

## Testing Strategy
- Unit: models/rules (cap checks, trades, drafts, scheduling, injuries, progression, bidding resolution).
- Integration: season flows (startup draft, FA modes, rookie draft, playoffs), trade/waiver edge cases, notifications.
- Engine regression: golden-play or golden-game baselines for determinism; property tests on sim outputs.
- Load: bulk season sims; measure duration and DB load.
- CI: run pytest + lint on PRs; seed data fixtures for flows.

## Engineering Practices
- API-first with DRF; versioned endpoints; serializers for UI/API reuse.
- Config via environment; 12-factor ready.
- Migrations required for schema changes; seed commands for dev data.
- Audit logging on commish/owner actions; structured logs for sims.

## Risks / Mitigations
- Sim complexity creep → start simple ratings model; iterate with tests/benchmarks.
- Concurrency on bids/trades → transactional rules, row locking where needed, deterministic tie-breakers.
- Long-running sims → background jobs + progress tracking; chunked writes.
- Data bloat from play logs → partitioning/archival strategy after baseline is stable.
