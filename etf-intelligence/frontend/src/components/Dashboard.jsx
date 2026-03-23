import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getPortfolios, getAllocations, getHoldings,
  getLatestQuotes, getRecommendations, getTiming, logout,
} from '../api'
import { useTheme } from '../context/ThemeContext'
import Allocation from './Allocation'
import BuyRecommendation from './BuyRecommendation'
import ExecutionTiming from './ExecutionTiming'
import AddPortfolioModal from './AddPortfolioModal'
import EditAllocationsModal from './EditAllocationsModal'

export default function Dashboard({ onLogout }) {
  const { theme, toggleTheme } = useTheme()

  const [portfolios, setPortfolios] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [allocations, setAllocations] = useState([])
  const [holdings, setHoldings] = useState([])
  const [quotes, setQuotes] = useState([])
  const [timing, setTiming] = useState([])
  const [recommendations, setRecommendations] = useState(null)
  const [contributionCad, setContributionCad] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [showEditAlloc, setShowEditAlloc] = useState(false)
  const [banner, setBanner] = useState('')
  const [calcLoading, setCalcLoading] = useState(false)
  const [spentFromAdds, setSpentFromAdds] = useState(0)

  // Load portfolios once on mount
  useEffect(() => {
    getPortfolios()
      .then((ps) => {
        setPortfolios(ps)
        if (ps.length > 0) setSelectedId(ps[0].id)
      })
      .catch((err) => setBanner(err.message))
  }, [])

  // Reload portfolio data whenever selection changes
  useEffect(() => {
    if (!selectedId) return
    Promise.all([
      getAllocations(selectedId),
      getHoldings(selectedId),
      getLatestQuotes(),
      getTiming(),
    ])
      .then(([allocs, holds, qs, windows]) => {
        setAllocations(allocs)
        setHoldings(holds)
        setQuotes(qs)
        setTiming(windows)
        setRecommendations(null)
      })
      .catch((err) => setBanner(err.message))
  }, [selectedId])

  async function handleCalculate() {
    const amount = Number(contributionCad)
    if (!amount || amount <= 0) return
    setBanner('')
    setCalcLoading(true)
    setSpentFromAdds(0)
    try {
      const data = await getRecommendations(selectedId, amount)
      setRecommendations(data)
    } catch (err) {
      setBanner(err.message)
    } finally {
      setCalcLoading(false)
    }
  }

  async function handleHoldingAdded(ticker, sharesToAdd, costCad) {
    setHoldings((hs) => hs.map((h) => h.ticker === ticker ? { ...h, shares: h.shares + sharesToAdd } : h))
    const newSpent = spentFromAdds + costCad
    setSpentFromAdds(newSpent)
    const remaining = Number(contributionCad) - newSpent
    if (remaining > 0) {
      try {
        const data = await getRecommendations(selectedId, remaining)
        setRecommendations(data)
      } catch (err) {
        setBanner(err.message)
      }
    }
  }

  async function handleLogout() {
    await logout().catch(() => {})
    onLogout()
  }

  function handlePortfolioChange(e) {
    if (e.target.value === '__add__') {
      setShowModal(true)
    } else {
      setSelectedId(Number(e.target.value))
    }
  }

  function handlePortfolioCreated(portfolio) {
    setPortfolios((ps) => [...ps, portfolio])
    setSelectedId(portfolio.id)
    setShowModal(false)
  }

  // Compute total value: sum(shares × price) across all holdings
  const priceMap = Object.fromEntries(quotes.map((q) => [q.ticker, q.price ?? 0]))
  const totalValue = holdings.reduce((sum, h) => sum + h.shares * (priceMap[h.ticker] ?? 0), 0)

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">

      {/* Top bar */}
      <div className="flex items-center justify-between mb-6">
        <select
          value={selectedId ?? ''}
          onChange={handlePortfolioChange}
          className="px-3 py-1.5 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
        >
          {portfolios.map((p) => (
            <option key={p.id} value={p.id}>{p.account_name}</option>
          ))}
          <option value="__add__">+ Add Portfolio</option>
        </select>

        <div className="flex items-center gap-4">
          <button onClick={toggleTheme} aria-label="Toggle theme" className="text-lg leading-none">
            {theme === 'dark' ? '☀' : '☾'}
          </button>
          <Link to="/settings" className="text-sm text-gray-600 dark:text-gray-400 hover:underline">
            Settings
          </Link>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-600 dark:text-gray-400 hover:underline"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Error banner */}
      {banner && (
        <div className="mb-4 flex items-center justify-between px-4 py-3 rounded bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
          <span>{banner}</span>
          <button onClick={() => setBanner('')} className="ml-4 text-base font-bold leading-none">×</button>
        </div>
      )}

      {/* Empty state */}
      {portfolios.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-500 dark:text-gray-400 mb-4">No portfolios yet.</p>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-sm"
          >
            Add your first portfolio
          </button>
        </div>
      ) : (
        <>
          {/* Total value */}
          <p className="text-2xl font-semibold mb-6">
            ${totalValue.toLocaleString('en-CA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} CAD
          </p>

          <Allocation holdings={holdings} allocations={allocations} quotes={quotes} onEdit={() => setShowEditAlloc(true)} />

          <BuyRecommendation
            recommendations={recommendations}
            contributionCad={contributionCad}
            onContributionChange={setContributionCad}
            onCalculate={handleCalculate}
            loading={calcLoading}
            totalValue={totalValue}
            portfolioId={selectedId}
            holdings={holdings}
            onHoldingAdded={handleHoldingAdded}
          />

          <ExecutionTiming windows={timing} />
        </>
      )}

      {showEditAlloc && allocations.length > 0 && (
        <EditAllocationsModal
          portfolioId={selectedId}
          allocations={allocations}
          holdings={holdings}
          onClose={() => setShowEditAlloc(false)}
          onSaved={({ allocations: a, holdings: h }) => {
            setAllocations(a)
            setHoldings(h)
            setShowEditAlloc(false)
          }}
        />
      )}

      {showModal && (
        <AddPortfolioModal
          quotes={quotes}
          onClose={() => setShowModal(false)}
          onCreated={handlePortfolioCreated}
        />
      )}
    </div>
  )
}
