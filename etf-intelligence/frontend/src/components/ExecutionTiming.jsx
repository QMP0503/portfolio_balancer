export default function ExecutionTiming({ windows }) {
  if (!windows?.length) return null

  return (
    <section className="mb-8">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">
        Execution Timing
      </h2>
      <div className="space-y-2">
        {windows.map((w) => (
          <div key={w.ticker} className="flex items-start gap-3 text-sm">
            <span className="w-16 font-mono text-xs shrink-0">{w.ticker.replace('.TO', '')}</span>
            <span className="tabular-nums text-gray-300">
              {w.best_start} – {w.best_end} EST
            </span>
            {w.note && (
              <span className="text-xs text-gray-500 dark:text-gray-500">{w.note}</span>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
