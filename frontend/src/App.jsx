import './styles.css'

const priorities = [
  'League creation wizard (commish settings)',
  'Roster/cap/trades core',
  'Season lifecycle (schedule, drafts, FA)',
  'Play-by-play sim with live feed',
  'Dashboards and player cards',
]

const Phase = ({ title, items }) => (
  <div className="card">
    <h2>{title}</h2>
    <ul>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  </div>
)

function App() {
  return (
    <main className="layout">
      <header>
        <h1>WFL Simulator</h1>
        <p>Backend: Django + DRF + Postgres · Frontend: React</p>
      </header>

      <section className="grid">
        <Phase
          title="Phase 0 – Foundations"
          items={[
            'Django/DRF project + Postgres config',
            'Custom User (email login, commish flag)',
            'Django admin enabled',
            'React + Vite scaffold',
            'CI with pytest (pending)',
          ]}
        />
        <Phase title="Initial Priorities" items={priorities} />
      </section>
    </main>
  )
}

export default App
