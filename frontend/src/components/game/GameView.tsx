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
    <div className="h-screen table-surface flex flex-col overflow-hidden">
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
        <div className="flex flex-col items-center gap-1 p-3 bg-black/50 backdrop-blur-sm rounded-t-lg">
          <span className="text-white/50 text-xs tracking-wide">再按一次出牌 · Click tile again to discard</span>
          <button
            onClick={() => {
              onAction('discard', selectedTileCode)
              setSelectedTileIndex(null)
            }}
            className="px-8 py-2.5 bg-red-600 hover:bg-red-500 active:scale-95 text-white rounded-lg font-bold transition-all duration-150 shadow-lg shadow-red-900/30"
          >
            打出 {selectedTileCode}
          </button>
        </div>
      )}
      {currentAnimation && currentAnimation.type === 'discard' && (
        <DiscardAnimation
          tile={currentAnimation.data.tile as string}
          onComplete={completeCurrentAnimation}
        />
      )}
      {currentAnimation && currentAnimation.type === 'draw' && (
        <DrawAnimation
          tile={currentAnimation.data.tile as string}
          onComplete={completeCurrentAnimation}
        />
      )}
      {currentAnimation && currentAnimation.type === 'meld' && (
        <MeldAnimation
          tiles={currentAnimation.data.tiles as string[]}
          meldType={currentAnimation.data.meldType as string}
          onComplete={completeCurrentAnimation}
        />
      )}
      {currentAnimation && currentAnimation.type === 'win' && (
        <WinAnimation
          tiles={currentAnimation.data.tiles as string[]}
          onComplete={completeCurrentAnimation}
        />
      )}
    </div>
  )
}
