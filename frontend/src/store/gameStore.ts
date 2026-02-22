import { create } from 'zustand'
import type {
  GameState,
  ActionRequest,
  ReplayFrame,
  ScoringBreakdown,
  GameSettings,
} from '../types/game'

export type ViewScreen = 'lobby' | 'game' | 'scoring' | 'replay' | 'settings' | 'history'

interface GameStore {
  // Connection
  connected: boolean
  setConnected: (connected: boolean) => void

  // Game state (mirrors server)
  gameState: GameState | null
  myPlayerIndex: number
  setGameState: (state: GameState) => void
  setMyPlayerIndex: (idx: number) => void

  // UI state
  currentScreen: ViewScreen
  setCurrentScreen: (screen: ViewScreen) => void
  actionRequest: ActionRequest | null
  setActionRequest: (req: ActionRequest | null) => void
  selectedTileIndex: number | null
  setSelectedTileIndex: (idx: number | null) => void
  timerSeconds: number
  setTimerSeconds: (seconds: number) => void

  // Game events log
  events: Array<{ event: string; player?: number; tile?: string }>
  addEvent: (event: { event: string; player?: number; tile?: string }) => void
  clearEvents: () => void

  // Scoring
  scoringResult: ScoringBreakdown | null
  setScoringResult: (result: ScoringBreakdown | null) => void

  // Settings
  settings: GameSettings
  updateSettings: (patch: Partial<GameSettings>) => void

  // Replay
  replayFrames: ReplayFrame[] | null
  replayIndex: number
  replayPlaying: boolean
  replaySpeed: number
  setReplayFrames: (frames: ReplayFrame[] | null) => void
  setReplayIndex: (index: number) => void
  setReplayPlaying: (playing: boolean) => void
  setReplaySpeed: (speed: number) => void

  // Reset
  resetGame: () => void
}

const defaultSettings: GameSettings = {
  animationSpeed: 'normal',
  language: 'zh-TW',
  tableBackground: 'green',
  soundEnabled: true,
}

export const useGameStore = create<GameStore>((set) => ({
  // Connection
  connected: false,
  setConnected: (connected) => set({ connected }),

  // Game state
  gameState: null,
  myPlayerIndex: 0,
  setGameState: (gameState) => set({ gameState }),
  setMyPlayerIndex: (myPlayerIndex) => set({ myPlayerIndex }),

  // UI state
  currentScreen: 'lobby',
  setCurrentScreen: (currentScreen) => set({ currentScreen }),
  actionRequest: null,
  setActionRequest: (actionRequest) => set({ actionRequest }),
  selectedTileIndex: null,
  setSelectedTileIndex: (selectedTileIndex) => set({ selectedTileIndex }),
  timerSeconds: 10,
  setTimerSeconds: (timerSeconds) => set({ timerSeconds }),

  // Events
  events: [],
  addEvent: (event) => set((s) => ({ events: [...s.events, event] })),
  clearEvents: () => set({ events: [] }),

  // Scoring
  scoringResult: null,
  setScoringResult: (scoringResult) => set({ scoringResult }),

  // Settings
  settings: defaultSettings,
  updateSettings: (patch) =>
    set((s) => ({ settings: { ...s.settings, ...patch } })),

  // Replay
  replayFrames: null,
  replayIndex: 0,
  replayPlaying: false,
  replaySpeed: 1,
  setReplayFrames: (replayFrames) => set({ replayFrames }),
  setReplayIndex: (replayIndex) => set({ replayIndex }),
  setReplayPlaying: (replayPlaying) => set({ replayPlaying }),
  setReplaySpeed: (replaySpeed) => set({ replaySpeed }),

  // Reset
  resetGame: () =>
    set({
      gameState: null,
      actionRequest: null,
      selectedTileIndex: null,
      timerSeconds: 10,
      events: [],
      scoringResult: null,
      currentScreen: 'lobby',
    }),
}))
