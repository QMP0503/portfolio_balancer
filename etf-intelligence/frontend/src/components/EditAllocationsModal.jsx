import { useState } from 'react'
import { setAllocation, updateHolding } from '../api'

export default function EditAllocationsModal({ portfolioId, allocations, holdings, onClose, onSaved }) {
  const [tab, setTab] = useState('Targets')
  const [allocDrafts, setAllocDrafts] = useState(
    Object.fromEntries(allocations.map((a) => [a.ticker, String(a.target_pct)]))
  )
  const [holdingDrafts, setHoldingDrafts] = useState(
    Object.fromEntries(holdings.map((h) => [h.ticker, String(h.shares)]))
  )
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const total = Object.values(allocDrafts).reduce((sum, v) => sum + (Number(v) || 0), 0)
  const allocValid = Math.abs(total - 100) < 0.01

  async function handleSave() {
    setError('')
    setSaving(true)
    try {
      if (tab === 'Targets') {
        if (!allocValid) return
        await Promise.all(
          allocations.map((a) =>
            setAllocation(portfolioId, a.ticker, Number(allocDrafts[a.ticker]), a.goal ?? '')
          )
        )
        onSaved({
          allocations: allocations.map((a) => ({ ...a, target_pct: Number(allocDrafts[a.ticker]) })),
          holdings,
        })
      } else {
        await Promise.all(
          holdings.map((h) => updateHolding(portfolioId, h.ticker, Number(holdingDrafts[h.ticker])))
        )
        onSaved({
          allocations,
          holdings: holdings.map((h) => ({ ...h, shares: Number(holdingDrafts[h.ticker]) })),
        })
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold">Edit Portfolio</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-200 text-lg leading-none">×</button>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 border-b border-gray-200 dark:border-gray-800 mb-4">
          {['Targets', 'Holdings'].map((t) => (
            <button
              key={t} onClick={() => setTab(t)}
              className={`pb-2 text-sm font-medium border-b-2 transition-colors ${tab === t ? 'border-blue-500 text-blue-500' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
            >
              {t}
            </button>
          ))}
        </div>

        {error && <p className="mb-3 text-xs text-red-400">{error}</p>}

        {tab === 'Targets' && (
          <>
            <div className="space-y-3 mb-3">
              {allocations.map((a) => (
                <div key={a.ticker} className="flex items-center gap-3">
                  <span className="w-12 font-mono text-sm">{a.ticker.replace('.TO', '')}</span>
                  <div className="flex items-center rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
                    <input
                      type="number" min="0" max="100" step="1"
                      value={allocDrafts[a.ticker]}
                      onChange={(e) => setAllocDrafts((d) => ({ ...d, [a.ticker]: e.target.value }))}
                      className="w-16 px-2 py-1.5 text-sm bg-transparent focus:outline-none tabular-nums"
                    />
                    <span className="pr-2 text-sm text-gray-400">%</span>
                  </div>
                </div>
              ))}
            </div>
            <p className={`text-xs mb-4 ${allocValid ? 'text-green-400' : 'text-red-400'}`}>
              Total: {total.toFixed(1)}% {allocValid ? '✓' : '(must equal 100%)'}
            </p>
          </>
        )}

        {tab === 'Holdings' && (
          <div className="space-y-3 mb-4">
            {holdings.map((h) => (
              <div key={h.ticker} className="flex items-center gap-3">
                <span className="w-12 font-mono text-sm">{h.ticker.replace('.TO', '')}</span>
                <div className="flex items-center rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
                  <input
                    type="number" min="0" step="1"
                    value={holdingDrafts[h.ticker]}
                    onChange={(e) => setHoldingDrafts((d) => ({ ...d, [h.ticker]: e.target.value }))}
                    className="w-20 px-2 py-1.5 text-sm bg-transparent focus:outline-none tabular-nums"
                  />
                  <span className="pr-2 text-xs text-gray-400">shares</span>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="px-4 py-2 rounded text-sm text-gray-400 hover:text-gray-200">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={(tab === 'Targets' && !allocValid) || saving}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm"
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
