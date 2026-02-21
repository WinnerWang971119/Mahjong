import GameHeader from './GameHeader'
import GameTable from './GameTable'
import ActionPanel from './ActionPanel'
import GameLog from './GameLog'
import { useGameStore } from '../../store/gameStore'

interface GameViewProps {
  onAction: (action: string, tile?: string, combo?: string[]) => void
}

export default function GameView({ onAction }: GameViewProps) {
  const gameState = useGameStore((s) => s.gameState)
  const myPlayerIndex = useGameStore((s) => s.myPlayerIndex)
  const actionRequest = useGameStore((s) => s.actionRequest)
  const selectedTile = useGameStore((s) => s.selectedTile)
  const setSelectedTile = useGameStore((s) => s.setSelectedTile)
  const events = useGameStore((s) => s.events)

  if (!gameState) return null

  const handleTileClick = (tile: string) => {
    if (selectedTile === tile) {
      // Double-click effect: discard immediately
      onAction('discard', tile)
      setSelectedTile(null)
    } else {
      setSelectedTile(tile)
    }
  }

  return (
    <div className="min-h-screen bg-table-green flex flex-col">
      <GameHeader gameState={gameState} />
      <div className="flex-1 flex">
        <div className="flex-1">
          <GameTable
            gameState={gameState}
            myPlayerIndex={myPlayerIndex}
            selectedTile={selectedTile}
            onTileClick={handleTileClick}
          />
        </div>
        <GameLog events={events} />
      </div>
      {actionRequest && (
        <ActionPanel options={actionRequest.options} onAction={onAction} />
      )}
      {/* Discard button when tile is selected and it's our active turn */}
      {selectedTile && !actionRequest && gameState.current_player === myPlayerIndex && (
        <div className="flex justify-center p-2 bg-black/40">
          <button
            onClick={() => {
              onAction('discard', selectedTile)
              setSelectedTile(null)
            }}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold"
          >
            打出 {selectedTile} (Discard)
          </button>
        </div>
      )}
    </div>
  )
}
