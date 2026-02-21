import type { GameState } from '../../types/game'

interface GameHeaderProps {
  gameState: GameState
}

const WIND_LABELS: Record<string, string> = { E: '東', S: '南', W: '西', N: '北' }

export default function GameHeader({ gameState }: GameHeaderProps) {
  const windChar = WIND_LABELS[gameState.round_wind] || gameState.round_wind
  const currentWindChar = WIND_LABELS[(['E', 'S', 'W', 'N'] as const)[gameState.current_player]] || ''

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-black/40 text-white rounded-lg">
      <div className="flex items-center gap-4">
        <span className="text-lg font-bold">{windChar}風 第{gameState.round_number + 1}局</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm">輪到: {currentWindChar}家</span>
        <span className="text-sm">剩餘: {gameState.wall_remaining}張</span>
      </div>
    </div>
  )
}
