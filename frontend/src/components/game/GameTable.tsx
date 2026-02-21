import PlayerArea from './PlayerArea'
import DiscardPool from './DiscardPool'
import WallIndicator from './WallIndicator'
import type { GameState } from '../../types/game'

interface GameTableProps {
  gameState: GameState
  myPlayerIndex: number
  selectedTile: string | null
  onTileClick: (tile: string) => void
}

// Map viewer's relative position: self=bottom, across=top, right=right, left=left
function getSeatPosition(seat: number, myIndex: number): 'bottom' | 'right' | 'top' | 'left' {
  const relative = (seat - myIndex + 4) % 4
  return (['bottom', 'right', 'top', 'left'] as const)[relative]
}

export default function GameTable({ gameState, myPlayerIndex, selectedTile, onTileClick }: GameTableProps) {
  return (
    <div className="grid grid-cols-[auto_1fr_auto] grid-rows-[auto_1fr_auto] w-full h-full gap-2 p-4">
      {/* Top player */}
      <div className="col-start-2 row-start-1 flex justify-center">
        {gameState.players.map((p) =>
          getSeatPosition(p.seat, myPlayerIndex) === 'top' ? (
            <PlayerArea key={p.seat} player={p} isSelf={false} isActive={p.seat === gameState.current_player} selectedTile={null} position="top" />
          ) : null,
        )}
      </div>

      {/* Left player */}
      <div className="col-start-1 row-start-2 flex items-center">
        {gameState.players.map((p) =>
          getSeatPosition(p.seat, myPlayerIndex) === 'left' ? (
            <PlayerArea key={p.seat} player={p} isSelf={false} isActive={p.seat === gameState.current_player} selectedTile={null} position="left" />
          ) : null,
        )}
      </div>

      {/* Center: discard pool + wall indicator */}
      <div className="col-start-2 row-start-2 flex flex-col items-center justify-center gap-2">
        <WallIndicator remaining={gameState.wall_remaining} />
        <DiscardPool discards={gameState.discard_pool} lastDiscard={gameState.last_discard} />
      </div>

      {/* Right player */}
      <div className="col-start-3 row-start-2 flex items-center">
        {gameState.players.map((p) =>
          getSeatPosition(p.seat, myPlayerIndex) === 'right' ? (
            <PlayerArea key={p.seat} player={p} isSelf={false} isActive={p.seat === gameState.current_player} selectedTile={null} position="right" />
          ) : null,
        )}
      </div>

      {/* Bottom player (self) */}
      <div className="col-start-2 row-start-3 flex justify-center">
        {gameState.players.map((p) =>
          getSeatPosition(p.seat, myPlayerIndex) === 'bottom' ? (
            <PlayerArea key={p.seat} player={p} isSelf isActive={p.seat === gameState.current_player} selectedTile={selectedTile} onTileClick={onTileClick} position="bottom" />
          ) : null,
        )}
      </div>
    </div>
  )
}
