import { useState, useEffect } from 'react'
import type { GameHistoryEntry, EloHistoryEntry } from '../../types/game'

interface EloHistoryProps {
  onBack: () => void
}

export default function EloHistory({ onBack }: EloHistoryProps) {
  const [games, setGames] = useState<GameHistoryEntry[]>([])
  const [eloHistory, setEloHistory] = useState<EloHistoryEntry[]>([])

  useEffect(() => {
    // Fetch from REST endpoints
    fetch('http://127.0.0.1:9000/api/history')
      .then((r) => r.json())
      .then((data) => setGames(data.games || []))
      .catch(() => {})

    fetch('http://127.0.0.1:9000/api/elo')
      .then((r) => r.json())
      .then((data) => setEloHistory(data.history || []))
      .catch(() => {})
  }, [])

  // SVG line chart for ELO
  const eloPoints = eloHistory.map((e) => e.elo_after).reverse()
  const chartWidth = 400
  const chartHeight = 150
  const minElo = Math.min(...eloPoints, 800)
  const maxElo = Math.max(...eloPoints, 1600)
  const range = maxElo - minElo || 1

  const pathD = eloPoints
    .map((elo, i) => {
      const x = (i / Math.max(eloPoints.length - 1, 1)) * chartWidth
      const y = chartHeight - ((elo - minElo) / range) * chartHeight
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')

  return (
    <div className="min-h-screen bg-table-green flex flex-col items-center p-8">
      <div className="bg-honor-dark rounded-xl p-8 max-w-2xl w-full text-white">
        <h2 className="text-2xl font-bold mb-6">對戰紀錄 (Match History)</h2>

        {/* ELO Chart */}
        {eloPoints.length > 1 && (
          <div className="mb-6">
            <h3 className="text-sm text-white/60 mb-2">ELO 趨勢</h3>
            <svg viewBox={`-10 -10 ${chartWidth + 20} ${chartHeight + 20}`} className="w-full h-40 bg-white/5 rounded">
              <path d={pathD} fill="none" stroke="#facc15" strokeWidth="2" />
              {eloPoints.map((elo, i) => (
                <circle
                  key={i}
                  cx={(i / Math.max(eloPoints.length - 1, 1)) * chartWidth}
                  cy={chartHeight - ((elo - minElo) / range) * chartHeight}
                  r="3"
                  fill="#facc15"
                />
              ))}
            </svg>
          </div>
        )}

        {/* Match table */}
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/20">
              <th className="text-left py-2">日期</th>
              <th className="text-left py-2">模式</th>
              <th className="text-left py-2">結果</th>
            </tr>
          </thead>
          <tbody>
            {games.length === 0 ? (
              <tr><td colSpan={3} className="py-4 text-center text-white/40">尚無紀錄</td></tr>
            ) : (
              games.map((g, i) => (
                <tr key={i} className="border-b border-white/10">
                  <td className="py-2">{g.started_at ? new Date(g.started_at).toLocaleDateString() : '—'}</td>
                  <td className="py-2">{g.mode}</td>
                  <td className="py-2">
                    <span className={g.result === 'win' ? 'text-green-400' : g.result === 'draw' ? 'text-yellow-400' : 'text-red-400'}>
                      {g.result === 'win' ? '勝' : g.result === 'draw' ? '和' : g.result || '—'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        <button
          onClick={onBack}
          className="w-full mt-6 py-2 bg-white/20 hover:bg-white/30 rounded-lg font-bold transition-colors"
        >
          返回 (Back)
        </button>
      </div>
    </div>
  )
}
