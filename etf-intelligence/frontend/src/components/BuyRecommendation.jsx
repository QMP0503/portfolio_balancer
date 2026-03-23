const fmt = (n) => n.toLocaleString('en-CA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export default function BuyRecommendation({
  recommendations,
  contributionCad,
  onContributionChange,
  onCalculate,
  loading,
  totalValue,
}) {
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

  function handleKeyDown(e) {
    if (e.key === 'Enter') onCalculate()
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
          onClick={onCalculate}
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
            </colgroup>
            <thead>
              <tr className="text-left text-xs text-gray-400 border-b border-gray-200 dark:border-gray-800">
                <th className="pb-2 font-medium">Ticker</th>
                <th className="pb-2 font-medium">Shares</th>
                <th className="pb-2 font-medium">Price</th>
                <th className="pb-2 font-medium">Total</th>
                <th className="pb-2 font-medium">Note</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {recs.map((r, i) => {
                const { fromPct, toPct, onTarget } = recNotes[i]
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
