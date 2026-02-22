import { useEffect } from 'react'
import { useGameStore } from '../../store/gameStore'

interface TurnTimerProps {
  onTimeout: () => void
}

export default function TurnTimer({ onTimeout }: TurnTimerProps) {
  const timerSeconds = useGameStore((s) => s.timerSeconds)
  const setTimerSeconds = useGameStore((s) => s.setTimerSeconds)

  useEffect(() => {
    if (timerSeconds <= 0) {
      onTimeout()
      return
    }
    const interval = setInterval(() => {
      setTimerSeconds(timerSeconds - 1)
    }, 1000)
    return () => clearInterval(interval)
  }, [timerSeconds, setTimerSeconds, onTimeout])

  const radius = 20
  const circumference = 2 * Math.PI * radius
  const progress = timerSeconds / 10
  const dashOffset = circumference * (1 - progress)
  const color = timerSeconds <= 3 ? '#ef4444' : '#22c55e'

  return (
    <div className="flex items-center justify-center">
      <svg width="56" height="56" viewBox="0 0 56 56">
        <circle cx="28" cy="28" r={radius} fill="none" stroke="#ffffff20" strokeWidth="4" />
        <circle
          cx="28"
          cy="28"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform="rotate(-90 28 28)"
          className="transition-all duration-1000 ease-linear"
        />
        <text x="28" y="28" textAnchor="middle" dominantBaseline="central" fill="white" fontSize="16" fontWeight="bold">
          {timerSeconds}
        </text>
      </svg>
    </div>
  )
}
