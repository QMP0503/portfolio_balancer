import { useState } from 'react'
import { createPortfolio, setAllocation, updateHolding } from '../api'

const TICKERS = ['HXQ.TO', 'VFV.TO', 'VCN.TO', 'ZEM.TO']
const ACCOUNT_OPTIONS = ['TFSA', 'FHSA', 'RRSP', 'Non-registered', 'Other']
const DEFAULT_ALLOCS = { 'HXQ.TO': '40', 'VFV.TO': '35', 'VCN.TO': '15', 'ZEM.TO': '10' }

export default function AddPortfolioModal({ quotes, onClose, onCreated }) {
  const [step, setStep] = useState(1)
  const [accountType, setAccountType] = useState('TFSA')
  const [customName, setCustomName] = useState('')
  const [shares, setShares] = useState(Object.fromEntries(TICKERS.map((t) => [t, ''])))
  const [allocs, setAllocs] = useState(DEFAULT_ALLOCS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const priceMap = Object.fromEntries(quotes.map((q) => [q.ticker, q.price ?? 0]))
  const accountName = accountType === 'Other' ? customName.trim() : accountType
  const allocTotal = TICKERS.reduce((sum, t) => sum + (Number(allocs[t]) || 0), 0)

  async function handleSave() {
    setLoading(true)
    setError('')
    try {
      const portfolio = await createPortfolio(accountName)
      await Promise.all(TICKERS.map((t) => setAllocation(portfolio.id, t, Number(allocs[t]))))
      const filled = TICKERS.filter((t) => Number(shares[t]) > 0)
      await Promise.all(filled.map((t) => updateHolding(portfolio.id, t, Number(shares[t]))))
      onCreated(portfolio)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
      <div className="bg-white dark:bg-gray-900 rounded-lg w-full max-w-md p-6">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">Add Portfolio — Step {step} of 3</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        {error && (
          <div className="mb-4 px-3 py-2 rounded bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Step 1: Account type */}
        {step === 1 && (
          <div className="space-y-3">
            {ACCOUNT_OPTIONS.map((opt) => (
              <label key={opt} className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio" name="account" value={opt}
                  checked={accountType === opt}
                  onChange={() => setAccountType(opt)}
                  className="accent-blue-500"
                />
                <span className="text-sm">{opt}</span>
              </label>
            ))}
            {accountType === 'Other' && (
              <input
                type="text" value={customName} onChange={(e) => setCustomName(e.target.value)}
                placeholder="Account name"
                className="mt-2 w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            )}
          </div>
        )}

        {/* Step 2: Current holdings */}
        {step === 2 && (
          <div className="space-y-3">
            {TICKERS.map((ticker) => {
              const price = priceMap[ticker] ?? 0
              const value = (Number(shares[ticker]) || 0) * price
              return (
                <div key={ticker} className="flex items-center gap-3">
                  <span className="w-12 font-mono text-xs">{ticker.replace('.TO', '')}</span>
                  <input
                    type="number" min="0" value={shares[ticker]} placeholder="0"
                    onChange={(e) => setShares((s) => ({ ...s, [ticker]: e.target.value }))}
                    className="w-24 px-2 py-1.5 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-xs text-gray-400">@ ${price.toFixed(2)}</span>
                  <span className="text-xs text-gray-500 ml-auto tabular-nums">
                    {value > 0 ? `$${value.toFixed(0)}` : '—'}
                  </span>
                </div>
              )
            })}
            <p className="text-xs text-gray-500 pt-1">Leave blank if you don't hold this ETF yet.</p>
          </div>
        )}

        {/* Step 3: Target allocations */}
        {step === 3 && (
          <div className="space-y-3">
            {TICKERS.map((ticker) => (
              <div key={ticker} className="flex items-center gap-3">
                <span className="w-12 font-mono text-xs">{ticker.replace('.TO', '')}</span>
                <input
                  type="number" min="0" max="100" value={allocs[ticker]}
                  onChange={(e) => setAllocs((a) => ({ ...a, [ticker]: e.target.value }))}
                  className="w-20 px-2 py-1.5 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-400">%</span>
              </div>
            ))}
            <p className={`text-sm font-medium pt-2 ${allocTotal === 100 ? 'text-green-500' : 'text-red-400'}`}>
              Total: {allocTotal}%{allocTotal === 100 ? ' ✓' : ` — need ${100 - allocTotal > 0 ? '+' : ''}${100 - allocTotal}%`}
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-between mt-8">
          <button
            onClick={step === 1 ? onClose : () => setStep((s) => s - 1)}
            className="px-4 py-2 text-sm text-gray-500 hover:text-gray-300"
          >
            {step === 1 ? 'Cancel' : '← Back'}
          </button>
          {step < 3 ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              disabled={step === 1 && accountType === 'Other' && !customName.trim()}
              className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm"
            >
              Next →
            </button>
          ) : (
            <button
              onClick={handleSave}
              disabled={loading || allocTotal !== 100}
              className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm"
            >
              {loading ? 'Saving…' : 'Save'}
            </button>
          )}
        </div>

      </div>
    </div>
  )
}
