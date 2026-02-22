import { useState, useCallback, useRef, useEffect } from 'react'
import { useGameStore } from '../store/gameStore'

interface AnimationItem {
  id: string
  type: 'draw' | 'discard' | 'meld' | 'win'
  data: Record<string, unknown>
}

const SPEED_MULTIPLIERS: Record<string, number> = {
  slow: 2,
  normal: 1,
  fast: 0.5,
  instant: 0,
}

export function useAnimationQueue() {
  const [queue, setQueue] = useState<AnimationItem[]>([])
  const [currentAnimation, setCurrentAnimation] = useState<AnimationItem | null>(null)
  const processingRef = useRef(false)
  const animationSpeed = useGameStore((s) => s.settings.animationSpeed)
  const multiplier = SPEED_MULTIPLIERS[animationSpeed] ?? 1

  const enqueue = useCallback((item: AnimationItem) => {
    if (multiplier === 0) return // instant mode, skip all animations
    setQueue((q) => [...q, item])
  }, [multiplier])

  const completeCurrentAnimation = useCallback(() => {
    setCurrentAnimation(null)
    processingRef.current = false
  }, [])

  useEffect(() => {
    if (processingRef.current || queue.length === 0) return
    processingRef.current = true
    const next = queue[0]
    setQueue((q) => q.slice(1))
    setCurrentAnimation(next)
  }, [queue, currentAnimation])

  return { currentAnimation, enqueue, completeCurrentAnimation, multiplier }
}
