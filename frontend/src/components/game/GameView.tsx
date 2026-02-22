import { useEffect } from 'react'
import GameHeader from './GameHeader'
import GameTable from './GameTable'
import ActionPanel from './ActionPanel'
import GameLog from './GameLog'
import { useGameStore } from '../../store/gameStore'
import { useAnimationQueue } from '../../hooks/useAnimationQueue'
import DrawAnimation from '../animations/DrawAnimation'
import DiscardAnimation from '../animations/DiscardAnimation'
import MeldAnimation from '../animations/MeldAnimation'
import WinAnimation from '../animations/WinAnimation'

interface GameViewProps {
  onAction: (action: string, tile?: string, combo?: string[]) => void
}

export default function GameView({ onAction }: GameViewProps) {
  const gameState = useGameStore((s) => s.gameState)
  const myPlayerIndex = useGameStore((s) => s.myPlayerIndex)
  const actionRequest = useGameStore((s) => s.actionRequest)
  const selectedTileIndex = useGameStore((s) => s.selectedTileIndex)
  const setSelectedTileIndex = useGameStore((s) => s.setSelectedTileIndex)
  const events = useGameStore((s) => s.events)
  const { currentAnimation, enqueue, completeCurrentAnimation } = useAnimationQueue()
  const lastEvent = useGameStore((s) => s.lastEvent)

  useEffect(() => {
    if (!lastEvent) return
    const { event, tile } = lastEvent
    if (event === 'discard' && tile) {
      enqueue({ id: crypto.randomUUID(), type: 'discard', data: { tile } })
    }
    // Note: only animating discards for now — draw events from AI happen too fast
    // and meld animations need tile arrays not available in the event
    useGameStore.getState().setLastEvent(null)
  }, [lastEvent, enqueue])

  if (!gameState) return null

  const myHand = gameState.players[myPlayerIndex]?.hand ?? []
  const selectedTileCode = selectedTileIndex !== null ? myHand[selectedTileIndex] ?? null : null

  const handleTileClick = (index: number) => {
    if (selectedTileIndex === index) {
      // Double-click effect: discard immediately
      const tile = myHand[index]
      if (tile) onAction('discard', tile)
      setSelectedTileIndex(null)
    } else {
      setSelectedTileIndex(index)
    }
  }

  return (
    <div className="h-screen bg-table-green flex flex-col overflow-hidden">
      <GameHeader gameState={gameState} />
      <div className="flex-1 flex min-h-0">
        <div className="flex-1 min-w-0 overflow-hidden">
          <GameTable
            gameState={gameState}
            myPlayerIndex={myPlayerIndex}
            selectedTileIndex={selectedTileIndex}
            onTileClick={handleTileClick}
          />
        </div>
        <GameLog events={events} />
      </div>
      {actionRequest && (
        <ActionPanel options={actionRequest.options} onAction={onAction} />
      )}
      {/* Discard button when tile is selected and it's our active turn */}
      {selectedTileCode && !actionRequest && gameState.current_player === myPlayerIndex && (
        <div className="flex justify-center p-2 bg-black/40">
          <button
            onClick={() => {
              onAction('discard', selectedTileCode)
              setSelectedTileIndex(null)
            }}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold"
          >
            打出 {selectedTileCode} (Discard)
          </button>
        </div>
      )}
      {currentAnimation && (
        <div className="fixed inset-0 z-40 flex items-center justify-center pointer-events-none">
          {currentAnimation.type === 'discard' && (
            <DiscardAnimation
              tile={currentAnimation.data.tile as string}
              onComplete={completeCurrentAnimation}
            />
          )}
          {currentAnimation.type === 'draw' && (
            <DrawAnimation
              tile={currentAnimation.data.tile as string}
              onComplete={completeCurrentAnimation}
            />
          )}
          {currentAnimation.type === 'meld' && (
            <MeldAnimation
              tiles={currentAnimation.data.tiles as string[]}
              meldType={currentAnimation.data.meldType as string}
              onComplete={completeCurrentAnimation}
            />
          )}
          {currentAnimation.type === 'win' && (
            <WinAnimation
              tiles={currentAnimation.data.tiles as string[]}
              onComplete={completeCurrentAnimation}
            />
          )}
        </div>
      )}
    </div>
  )
}
