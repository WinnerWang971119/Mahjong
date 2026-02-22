import type { GameState } from '../../types/game'

interface GameHeaderProps {
  gameState: GameState
}

const WIND_LABELS: Record<string, string> = { E: '東', S: '南', W: '西', N: '北' }

export default function GameHeader({ gameState }: GameHeaderProps) {
  const windChar = WIND_LABELS[gameState.round_wind] || gameState.round_wind
  const currentWindChar = WIND_LABELS[(['E', 'S', 'W', 'N'] as const)[gameState.current_player]] || ''

  return (
    <div className="flex items-center justify-between px-6 py-3 bg-black/50 text-white border-b border-white/10">
      <div className="flex items-center gap-3">
        <span className="text-xl font-bold tracking-wide text-yellow-400/90">{windChar}風</span>
        <span className="text-white/40">|</span>
        <span className="text-base font-medium">第{gameState.round_number + 1}局</span>
      </div>
      <div className="flex items-center gap-4 text-sm text-white/70">
        <span>輪到: <span className="text-yellow-400 font-medium">{currentWindChar}家</span></span>
        <span>剩餘: <span className="text-white font-medium">{gameState.wall_remaining}</span>張</span>
      </div>
    </div>
  )
}
