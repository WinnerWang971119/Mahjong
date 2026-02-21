import HandTiles from './HandTiles'
import MeldArea from './MeldArea'
import FlowerArea from './FlowerArea'
import type { PlayerState } from '../../types/game'

interface PlayerAreaProps {
  player: PlayerState
  isSelf: boolean
  isActive: boolean
  selectedTile: string | null
  onTileClick?: (tile: string) => void
  position: 'bottom' | 'right' | 'top' | 'left'
}

const positionClasses: Record<string, string> = {
  bottom: 'flex flex-col items-center',
  top: 'flex flex-col-reverse items-center rotate-180',
  left: 'flex flex-row-reverse items-center -rotate-90',
  right: 'flex flex-row items-center rotate-90',
}

const WIND_LABELS: Record<number, string> = { 0: '東', 1: '南', 2: '西', 3: '北' }

export default function PlayerArea({ player, isSelf, isActive, selectedTile, onTileClick, position }: PlayerAreaProps) {
  return (
    <div className={`${positionClasses[position]} ${isActive ? 'ring-2 ring-yellow-400 rounded-lg p-1' : 'p-1'}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs text-white font-bold">
          {WIND_LABELS[player.seat]}
          {player.is_dealer && ' 莊'}
        </span>
        <FlowerArea flowers={player.flowers} />
      </div>
      <MeldArea melds={player.melds} />
      <HandTiles
        tiles={player.hand}
        tileCount={player.hand_count}
        isSelf={isSelf}
        selectedTile={selectedTile}
        onTileClick={onTileClick}
      />
    </div>
  )
}
