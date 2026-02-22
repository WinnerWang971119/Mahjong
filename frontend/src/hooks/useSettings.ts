import { useEffect } from 'react'
import { useGameStore } from '../store/gameStore'
import type { GameSettings } from '../types/game'

const STORAGE_KEY = 'mahjong-settings'

export function useSettingsPersistence() {
  const settings = useGameStore((s) => s.settings)
  const updateSettings = useGameStore((s) => s.updateSettings)

  // Load on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed: Partial<GameSettings> = JSON.parse(saved)
        updateSettings(parsed)
      }
    } catch {
      // Ignore parse errors
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Save on change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    } catch {
      // Ignore storage errors
    }
  }, [settings])
}
