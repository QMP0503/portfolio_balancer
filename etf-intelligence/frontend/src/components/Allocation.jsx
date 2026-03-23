import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine,
  Cell, ResponsiveContainer,
} from 'recharts'
import { useTheme } from '../context/ThemeContext'

const TICKERS = ['HXQ.TO', 'VFV.TO', 'VCN.TO', 'ZEM.TO']

function buildChartData(holdings, allocations, quotes) {
  const priceMap = Object.fromEntries(quotes.map((q) => [q.ticker, q.price ?? 0]))
  const sharesMap = Object.fromEntries(holdings.map((h) => [h.ticker, h.shares]))
  const targetMap = Object.fromEntries(allocations.map((a) => [a.ticker, a.target_pct]))

  const totalValue = TICKERS.reduce((sum, t) => sum + (sharesMap[t] ?? 0) * (priceMap[t] ?? 0), 0)

  return TICKERS.map((ticker) => {
    const shares = sharesMap[ticker] ?? 0
    const price = priceMap[ticker] ?? 0
    const value = shares * price
    const currentPct = totalValue > 0 ? (value / totalValue) * 100 : 0
    const targetPct = targetMap[ticker] ?? 0
    const diff = currentPct - targetPct
    return { ticker, shares, price, currentPct: +currentPct.toFixed(1), targetPct, diff: +diff.toFixed(1), value }
  })
}

function StatusLabel({ diff }) {
  if (Math.abs(diff) < 1) return <span className="text-gray-400 text-xs">on target</span>
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

export default function Allocation({ holdings, allocations, quotes, onEdit }) {
  const { theme } = useTheme()
  if (!allocations.length) return null

  const data = buildChartData(holdings, allocations, quotes)
  const cursorFill = theme === 'dark' ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.06)'

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          Allocation
        </h2>
        <button onClick={onEdit} className="text-xs text-gray-400 hover:text-blue-500">Edit</button>
      </div>

      {/* Summary rows */}
      <div className="space-y-2 mb-4">
        {data.map(({ ticker, shares, price, currentPct, targetPct, diff, value }) => (
          <div key={ticker} className="flex items-center gap-3 text-sm">
            <span className="w-12 font-mono text-xs">{ticker.replace('.TO', '')}</span>
            <span className="w-28 tabular-nums text-gray-500 text-xs whitespace-nowrap">{shares} @ ${price.toFixed(2)}</span>
            <span className="w-20 tabular-nums text-gray-300">
              ${value.toLocaleString('en-CA', { maximumFractionDigits: 0 })}
            </span>
            <span className="w-12 text-right tabular-nums">{currentPct}%</span>
            <span className="text-gray-500">→</span>
            <span className="w-12 tabular-nums text-gray-400">{targetPct}%</span>
            <StatusLabel diff={diff} />
          </div>
        ))}
      </div>

      {/* Bar chart */}
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
          <XAxis type="number" domain={[0, 50]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="ticker"
            tickFormatter={(t) => t.replace('.TO', '')}
            tick={{ fontSize: 11, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: cursorFill }} />
          <Bar dataKey="currentPct" name="Current" barSize={10} radius={[0, 3, 3, 0]}>
            {data.map(({ ticker, diff }) => (
              <Cell
                key={ticker}
                fill={Math.abs(diff) < 1 ? '#374151' : diff > 0 ? '#7f3f3f' : '#2d5a8a'}
              />
            ))}
          </Bar>
          <Bar dataKey="targetPct" name="Target" barSize={4} fill="#2d3748" radius={[0, 2, 2, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  )
}
