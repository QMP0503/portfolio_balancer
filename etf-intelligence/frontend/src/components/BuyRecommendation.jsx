import { useState, useEffect } from 'react'
import { updateHolding } from '../api'

const fmt = (n) => n.toLocaleString('en-CA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function BuyRecommendation({
  recommendations,
  contributionCad,
  onContributionChange,
  onCalculate,
  loading,
  totalValue,
  portfolioId,
  holdings,
  onHoldingAdded,
}) {
  const [adding, setAdding] = useState(new Set())
  const [added, setAdded] = useState(new Set())


  const recs = recommendations?.recommendations ?? []
  const leftover = recommendations?.leftover_cad ?? null
  const totalSpent = recommendations?.total_cost ?? 0
  const newPortfolioTotal = totalValue + totalSpent

  const recNotes = recs.map((r) => {
    const currentValue = (r.current_pct / 100) * totalValue
    const postBuyPct = newPortfolioTotal > 0
      ? ((currentValue + r.total_cost) / newPortfolioTotal) * 100
      : r.target_pct
    return {
      fromPct: r.current_pct,
      toPct: +postBuyPct.toFixed(1),
      onTarget: Math.abs(postBuyPct - r.target_pct) <= 2,
    }
  })

  async function handleAdd(r) {
    if (adding.has(r.ticker) || added.has(r.ticker) || r.shares_to_buy === 0) return
    const currentShares = holdings.find((h) => h.ticker === r.ticker)?.shares ?? 0
    setAdding((s) => new Set(s).add(r.ticker))
    try {
      await updateHolding(portfolioId, r.ticker, currentShares + r.shares_to_buy)
      setAdded((s) => new Set(s).add(r.ticker))
      onHoldingAdded(r.ticker, r.shares_to_buy)
    } finally {
      setAdding((s) => { const n = new Set(s); n.delete(r.ticker); return n })
    }
  }

  function handleCalculate() {
    setAdded(new Set())
    onCalculate()
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') handleCalculate()
  }

  return (
    <section className="mb-8">
      {/* Contribution input */}
      <div className="flex items-center gap-3 mb-4">
        <label className="text-sm font-medium whitespace-nowrap">Contribute</label>
        <div className="flex items-center rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden">
          <span className="px-3 py-1.5 text-sm text-gray-400 border-r border-gray-300 dark:border-gray-700">$</span>
          <input
            type="number"
            min="0"
            step="50"
            value={contributionCad}
            onChange={(e) => onContributionChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="1200"
            className="px-3 py-1.5 text-sm bg-transparent w-28 focus:outline-none"
          />
        </div>
        <button
          onClick={handleCalculate}
          disabled={loading || !contributionCad || Number(contributionCad) <= 0}
          className="px-4 py-1.5 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm transition-colors"
        >
          {loading ? 'Calculating…' : 'Calculate →'}
        </button>
      </div>

      {/* Recommendations table */}
      {recs.length > 0 && (
        <>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">
            Recommended Buys
          </h2>
          <table className="w-full text-sm mb-3 table-fixed">
            <colgroup>
              <col style={{ width: '3.5rem' }} />
              <col style={{ width: '4.5rem' }} />
              <col style={{ width: '5.5rem' }} />
              <col style={{ width: '7rem' }} />
              <col />
              <col style={{ width: '3rem' }} />
            </colgroup>
            <thead>
              <tr className="text-left text-xs text-gray-400 border-b border-gray-200 dark:border-gray-800">
                <th className="pb-2 font-medium">Ticker</th>
                <th className="pb-2 font-medium">Shares</th>
                <th className="pb-2 font-medium">Price</th>
                <th className="pb-2 font-medium">Total</th>
                <th className="pb-2 font-medium">Note</th>
                <th className="pb-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {recs.map((r, i) => {
                const { fromPct, toPct, onTarget } = recNotes[i]
                const isAdded = added.has(r.ticker)
                const isAdding = adding.has(r.ticker)
                return (
                  <tr key={r.ticker} className={r.shares_to_buy === 0 ? 'opacity-50' : ''}>
                    <td className="py-2 font-mono text-xs">{r.ticker.replace('.TO', '')}</td>
                    <td className="py-2 tabular-nums">
                      {r.shares_to_buy === 0 ? '—' : r.shares_to_buy}
                    </td>
                    <td className="py-2 tabular-nums text-gray-400">${fmt(r.price)}</td>
                    <td className="py-2 tabular-nums font-medium">
                      {r.shares_to_buy === 0 ? '—' : `$${fmt(r.total_cost)}`}
                    </td>
                    <td className={`py-2 text-xs truncate ${onTarget ? 'text-green-400' : 'text-red-400'}`}>
                      {fromPct}% → {toPct}%
                    </td>
                    <td className="py-2 text-right">
                      {r.shares_to_buy > 0 && (
                        <button
                          onClick={() => handleAdd(r)}
                          disabled={isAdding || isAdded}
                          className="text-xs px-1.5 py-0.5 rounded border border-gray-600 text-gray-400 hover:border-green-500 hover:text-green-400 disabled:opacity-40 transition-colors"
                        >
                          {isAdded ? '✓' : isAdding ? '…' : '+'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {leftover !== null && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Leftover: <span className="tabular-nums">${fmt(leftover)}</span>
            </p>
          )}
        </>
      )}
    </section>
  )
}
