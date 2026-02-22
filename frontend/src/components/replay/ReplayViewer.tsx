import { useEffect, useCallback } from 'react'
import { useGameStore } from '../../store/gameStore'
import GameHeader from '../game/GameHeader'
import GameTable from '../game/GameTable'

interface ReplayViewerProps {
  onBack: () => void
}

export default function ReplayViewer({ onBack }: ReplayViewerProps) {
  const replayFrames = useGameStore((s) => s.replayFrames)
  const replayIndex = useGameStore((s) => s.replayIndex)
  const setReplayIndex = useGameStore((s) => s.setReplayIndex)
  const replayPlaying = useGameStore((s) => s.replayPlaying)
  const setReplayPlaying = useGameStore((s) => s.setReplayPlaying)
  const replaySpeed = useGameStore((s) => s.replaySpeed)
  const setReplaySpeed = useGameStore((s) => s.setReplaySpeed)
  const gameState = useGameStore((s) => s.gameState)
  const setGameState = useGameStore((s) => s.setGameState)

  const totalFrames = replayFrames?.length ?? 0

  const applyFrame = useCallback((index: number) => {
    if (!replayFrames || index >= replayFrames.length) return
    try {
      const frame = JSON.parse(replayFrames[index].action_json)
      if (frame.state) {
        setGameState(frame.state)
      }
    } catch {
      // Skip malformed frames
    }
  }, [replayFrames, setGameState])

  // Auto-play
  useEffect(() => {
    if (!replayPlaying || replayIndex >= totalFrames - 1) {
      setReplayPlaying(false)
      return
    }
    const timer = setTimeout(() => {
      const next = replayIndex + 1
      setReplayIndex(next)
      applyFrame(next)
    }, 1000 / replaySpeed)
    return () => clearTimeout(timer)
  }, [replayPlaying, replayIndex, totalFrames, replaySpeed, setReplayIndex, setReplayPlaying, applyFrame])

  const stepForward = () => {
    if (replayIndex < totalFrames - 1) {
      const next = replayIndex + 1
      setReplayIndex(next)
      applyFrame(next)
    }
  }

  const stepBack = () => {
    if (replayIndex > 0) {
      const prev = replayIndex - 1
      setReplayIndex(prev)
      applyFrame(prev)
    }
  }

  return (
    <div className="min-h-screen bg-table-green flex flex-col">
      {gameState && (
        <>
          <GameHeader gameState={gameState} />
          <div className="flex-1">
            <GameTable gameState={gameState} myPlayerIndex={0} selectedTileIndex={null} onTileClick={() => {}} />
          </div>
        </>
      )}

      {/* Replay controls */}
      <div className="flex items-center justify-center gap-4 p-4 bg-black/60">
        <button onClick={onBack} className="px-3 py-1 bg-white/20 hover:bg-white/30 text-white rounded text-sm">
          返回
        </button>
        <button onClick={stepBack} disabled={replayIndex <= 0} className="px-3 py-1 bg-white/20 hover:bg-white/30 text-white rounded disabled:opacity-30">
          ◀ 上一步
        </button>
        <button
          onClick={() => setReplayPlaying(!replayPlaying)}
          className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-honor-dark font-bold rounded"
        >
          {replayPlaying ? '⏸ 暫停' : '▶ 播放'}
        </button>
        <button onClick={stepForward} disabled={replayIndex >= totalFrames - 1} className="px-3 py-1 bg-white/20 hover:bg-white/30 text-white rounded disabled:opacity-30">
          下一步 ▶
        </button>
        <span className="text-white text-sm">
          {replayIndex + 1} / {totalFrames}
        </span>
        <select
          value={replaySpeed}
          onChange={(e) => setReplaySpeed(Number(e.target.value))}
          className="bg-white/10 text-white border border-white/20 rounded px-2 py-1 text-sm"
        >
          <option value={0.5}>0.5x</option>
          <option value={1}>1x</option>
          <option value={2}>2x</option>
          <option value={4}>4x</option>
        </select>
      </div>
    </div>
  )
}
