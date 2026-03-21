import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPortfolios, getAllocations, getHoldings, updateHolding, setAllocation } from '../api'

const TABS = ['Holdings', 'Allocations']

function EditableRow({ label, value, unit = '', onSave }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(String(value))

  function handleSave() {
    onSave(Number(draft))
    setEditing(false)
  }

  if (editing) {
    return (
      <td className="py-2 flex items-center gap-2">
        <input
          type="number" min="0" value={draft} autoFocus
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSave(); if (e.key === 'Escape') setEditing(false) }}
          className="w-24 px-2 py-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <span className="text-xs text-gray-400">{unit}</span>
        <button onClick={handleSave} className="text-xs text-blue-500 hover:underline">Save</button>
        <button onClick={() => setEditing(false)} className="text-xs text-gray-400 hover:underline">Cancel</button>
      </td>
    )
  }

  return (
    <td className="py-2">
      <span className="tabular-nums">{value}{unit}</span>
      <button onClick={() => { setDraft(String(value)); setEditing(true) }} className="ml-3 text-xs text-gray-400 hover:text-blue-500">
        Edit
      </button>
    </td>
  )
}

export default function Settings() {
  const [portfolios, setPortfolios] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [holdings, setHoldings] = useState([])
  const [allocations, setAllocations] = useState([])
  const [tab, setTab] = useState('Holdings')
  const [error, setError] = useState('')

  useEffect(() => {
    getPortfolios()
      .then((ps) => { setPortfolios(ps); if (ps.length > 0) setSelectedId(ps[0].id) })
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    Promise.all([getHoldings(selectedId), getAllocations(selectedId)])
      .then(([h, a]) => { setHoldings(h); setAllocations(a) })
      .catch((err) => setError(err.message))
  }, [selectedId])

  async function saveHolding(ticker, shares) {
    try {
      await updateHolding(selectedId, ticker, shares)
      setHoldings((hs) => hs.map((h) => h.ticker === ticker ? { ...h, shares } : h))
    } catch (err) { setError(err.message) }
  }

  async function saveAllocation(ticker, targetPct) {
    try {
      const current = allocations.find((a) => a.ticker === ticker)
      await setAllocation(selectedId, ticker, targetPct, current?.goal ?? '')
      setAllocations((as) => as.map((a) => a.ticker === ticker ? { ...a, target_pct: targetPct } : a))
    } catch (err) { setError(err.message) }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Settings</h1>
        <Link to="/" className="text-sm text-gray-500 hover:underline">← Dashboard</Link>
      </div>

      {error && (
        <div className="mb-4 flex items-center justify-between px-4 py-3 rounded bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
          <span>{error}</span>
          <button onClick={() => setError('')} className="ml-4 font-bold">×</button>
        </div>
      )}

      {/* Portfolio selector */}
      <div className="mb-6">
        <select
          value={selectedId ?? ''}
          onChange={(e) => setSelectedId(Number(e.target.value))}
          className="px-3 py-1.5 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
        >
          {portfolios.map((p) => <option key={p.id} value={p.id}>{p.account_name}</option>)}
        </select>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200 dark:border-gray-800 mb-4">
        {TABS.map((t) => (
          <button
            key={t} onClick={() => setTab(t)}
            className={`pb-2 text-sm font-medium border-b-2 transition-colors ${tab === t ? 'border-blue-500 text-blue-500' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Holdings tab */}
      {tab === 'Holdings' && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-400 border-b border-gray-200 dark:border-gray-800">
              <th className="pb-2 font-medium">Ticker</th>
              <th className="pb-2 font-medium">Shares</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h) => (
              <tr key={h.ticker} className="border-b border-gray-100 dark:border-gray-800/50">
                <td className="py-2 font-mono text-xs w-20">{h.ticker.replace('.TO', '')}</td>
                <EditableRow value={h.shares} onSave={(v) => saveHolding(h.ticker, v)} />
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Allocations tab */}
      {tab === 'Allocations' && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-400 border-b border-gray-200 dark:border-gray-800">
              <th className="pb-2 font-medium">Ticker</th>
              <th className="pb-2 font-medium">Target %</th>
            </tr>
          </thead>
          <tbody>
            {allocations.map((a) => (
              <tr key={a.ticker} className="border-b border-gray-100 dark:border-gray-800/50">
                <td className="py-2 font-mono text-xs w-20">{a.ticker.replace('.TO', '')}</td>
                <EditableRow value={a.target_pct} unit="%" onSave={(v) => saveAllocation(a.ticker, v)} />
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
