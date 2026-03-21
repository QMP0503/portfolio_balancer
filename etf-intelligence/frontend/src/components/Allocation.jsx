import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine,
  Cell, ResponsiveContainer,
} from 'recharts'

const TICKERS = ['HXQ.TO', 'VFV.TO', 'VCN.TO', 'ZEM.TO']

function buildChartData(holdings, allocations, quotes) {
  const priceMap = Object.fromEntries(quotes.map((q) => [q.ticker, q.price ?? 0]))
  const sharesMap = Object.fromEntries(holdings.map((h) => [h.ticker, h.shares]))
  const targetMap = Object.fromEntries(allocations.map((a) => [a.ticker, a.target_pct]))

  const totalValue = TICKERS.reduce((sum, t) => sum + (sharesMap[t] ?? 0) * (priceMap[t] ?? 0), 0)

  return TICKERS.map((ticker) => {
    const value = (sharesMap[ticker] ?? 0) * (priceMap[ticker] ?? 0)
    const currentPct = totalValue > 0 ? (value / totalValue) * 100 : 0
    const targetPct = targetMap[ticker] ?? 0
    const diff = currentPct - targetPct
    return { ticker, currentPct: +currentPct.toFixed(1), targetPct, diff: +diff.toFixed(1) }
  })
}

function StatusLabel({ diff }) {
  if (Math.abs(diff) < 0.5) return <span className="text-gray-400 text-xs">on target</span>
  if (diff > 0) return <span className="text-red-400 text-xs">↓ overweight</span>
  return <span className="text-green-400 text-xs">↑ underweight</span>
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const current = payload.find((p) => p.dataKey === 'currentPct')?.value
  const target = payload.find((p) => p.dataKey === 'targetPct')?.value
  return (
    <div className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-xs text-white">
      <p className="font-medium mb-1">{label}</p>
      <p>Current: <span className="text-blue-400">{current}%</span></p>
      <p>Target: <span className="text-gray-400">{target}%</span></p>
    </div>
  )
}

export default function Allocation({ holdings, allocations, quotes }) {
  if (!allocations.length) return null

  const data = buildChartData(holdings, allocations, quotes)

  return (
    <section className="mb-8">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">
        Allocation
      </h2>

      {/* Summary rows */}
      <div className="space-y-2 mb-4">
        {data.map(({ ticker, currentPct, targetPct, diff }) => (
          <div key={ticker} className="flex items-center gap-3 text-sm">
            <span className="w-16 font-mono text-xs">{ticker.replace('.TO', '')}</span>
            <span className="w-12 text-right tabular-nums">{currentPct}%</span>
            <span className="text-gray-400">→</span>
            <span className="w-12 tabular-nums text-gray-400">{targetPct}%</span>
            <StatusLabel diff={diff} />
          </div>
        ))}
      </div>

      {/* Bar chart */}
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
          <XAxis type="number" domain={[0, 50]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="ticker"
            tickFormatter={(t) => t.replace('.TO', '')}
            tick={{ fontSize: 11 }}
            width={36}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="currentPct" name="Current" barSize={10} radius={[0, 3, 3, 0]}>
            {data.map(({ ticker, diff }) => (
              <Cell
                key={ticker}
                fill={Math.abs(diff) < 0.5 ? '#6b7280' : diff > 0 ? '#f87171' : '#60a5fa'}
              />
            ))}
          </Bar>
          <Bar dataKey="targetPct" name="Target" barSize={4} fill="#374151" radius={[0, 2, 2, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  )
}
