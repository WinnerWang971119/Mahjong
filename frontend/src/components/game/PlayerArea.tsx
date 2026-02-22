import HandTiles from './HandTiles'
import MeldArea from './MeldArea'
import FlowerArea from './FlowerArea'
import type { PlayerState } from '../../types/game'

interface PlayerAreaProps {
  player: PlayerState
  isSelf: boolean
  isActive: boolean
  selectedTileIndex: number | null
  onTileClick?: (index: number) => void
  position: 'bottom' | 'right' | 'top' | 'left'
}

const positionClasses: Record<string, string> = {
  bottom: 'flex flex-col items-center bg-black/15 rounded-lg backdrop-blur-sm',
  top: 'flex flex-col-reverse items-center bg-black/15 rounded-lg backdrop-blur-sm',
  left: 'flex flex-col items-center bg-black/15 rounded-lg backdrop-blur-sm',
  right: 'flex flex-col items-center bg-black/15 rounded-lg backdrop-blur-sm',
}

const WIND_LABELS: Record<number, string> = { 0: '東', 1: '南', 2: '西', 3: '北' }

export default function PlayerArea({ player, isSelf, isActive, selectedTileIndex, onTileClick, position }: PlayerAreaProps) {
  return (
    <div className={`${positionClasses[position]} ${isActive ? 'active-turn-glow p-2' : 'p-2'}`}>
      {isActive && isSelf && (
        <span className="text-xs font-bold text-yellow-400 animate-pulse tracking-wider uppercase mb-1">
          輪到你了！
        </span>
      )}
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs text-white font-bold">
          {WIND_LABELS[player.seat]}
          {player.is_dealer && ' 莊'}
        </span>
        <FlowerArea flowers={player.flowers} position={position} />
      </div>
      <MeldArea melds={player.melds} position={position} />
      <HandTiles
        tiles={player.hand}
        tileCount={player.hand_count}
        isSelf={isSelf}
        selectedTileIndex={selectedTileIndex}
        onTileClick={onTileClick}
        position={position}
      />
    </div>
  )
}
