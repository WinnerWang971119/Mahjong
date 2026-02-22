import { describe, it, expect, beforeEach } from 'vitest'
import { useGameStore } from '../gameStore'
import type {
  GameState,
  ActionRequest,
  ReplayFrame,
  ScoringBreakdown,
} from '../../types/game'

// Default initial state used to reset the store between tests
const initialState = {
  connected: false,
  gameState: null,
  myPlayerIndex: 0,
  currentScreen: 'lobby' as const,
  actionRequest: null,
  selectedTileIndex: null,
  timerSeconds: 10,
  events: [],
  scoringResult: null,
  settings: {
    animationSpeed: 'normal' as const,
    language: 'zh-TW' as const,
    tableBackground: 'green' as const,
    soundEnabled: true,
  },
  replayFrames: null,
  replayIndex: 0,
  replayPlaying: false,
  replaySpeed: 1,
}

beforeEach(() => {
  useGameStore.setState(initialState)
})

describe('gameStore', () => {
  // ── Default initial state ───────────────────────────────────────────

  describe('initial state', () => {
    it('has correct default values', () => {
      const state = useGameStore.getState()

      expect(state.connected).toBe(false)
      expect(state.gameState).toBeNull()
      expect(state.myPlayerIndex).toBe(0)
      expect(state.currentScreen).toBe('lobby')
      expect(state.actionRequest).toBeNull()
      expect(state.selectedTileIndex).toBeNull()
      expect(state.timerSeconds).toBe(10)
      expect(state.events).toEqual([])
      expect(state.scoringResult).toBeNull()
      expect(state.settings).toEqual({
        animationSpeed: 'normal',
        language: 'zh-TW',
        tableBackground: 'green',
        soundEnabled: true,
      })
      expect(state.replayFrames).toBeNull()
      expect(state.replayIndex).toBe(0)
      expect(state.replayPlaying).toBe(false)
      expect(state.replaySpeed).toBe(1)
    })
  })

  // ── setConnected ────────────────────────────────────────────────────

  describe('setConnected', () => {
    it('sets connected to true', () => {
      useGameStore.getState().setConnected(true)
      expect(useGameStore.getState().connected).toBe(true)
    })

    it('sets connected to false', () => {
      useGameStore.getState().setConnected(true)
      useGameStore.getState().setConnected(false)
      expect(useGameStore.getState().connected).toBe(false)
    })
  })

  // ── setCurrentScreen ────────────────────────────────────────────────

  describe('setCurrentScreen', () => {
    it('changes screen to game', () => {
      useGameStore.getState().setCurrentScreen('game')
      expect(useGameStore.getState().currentScreen).toBe('game')
    })

    it('changes screen to scoring', () => {
      useGameStore.getState().setCurrentScreen('scoring')
      expect(useGameStore.getState().currentScreen).toBe('scoring')
    })

    it('changes screen to replay', () => {
      useGameStore.getState().setCurrentScreen('replay')
      expect(useGameStore.getState().currentScreen).toBe('replay')
    })

    it('changes screen to settings', () => {
      useGameStore.getState().setCurrentScreen('settings')
      expect(useGameStore.getState().currentScreen).toBe('settings')
    })

    it('changes screen to history', () => {
      useGameStore.getState().setCurrentScreen('history')
      expect(useGameStore.getState().currentScreen).toBe('history')
    })

    it('changes screen back to lobby', () => {
      useGameStore.getState().setCurrentScreen('game')
      useGameStore.getState().setCurrentScreen('lobby')
      expect(useGameStore.getState().currentScreen).toBe('lobby')
    })
  })

  // ── setSelectedTile ─────────────────────────────────────────────────

  describe('setSelectedTileIndex', () => {
    it('selects a tile by index', () => {
      useGameStore.getState().setSelectedTileIndex(3)
      expect(useGameStore.getState().selectedTileIndex).toBe(3)
    })

    it('deselects a tile by setting null', () => {
      useGameStore.getState().setSelectedTileIndex(3)
      useGameStore.getState().setSelectedTileIndex(null)
      expect(useGameStore.getState().selectedTileIndex).toBeNull()
    })

    it('replaces one selection with another', () => {
      useGameStore.getState().setSelectedTileIndex(1)
      useGameStore.getState().setSelectedTileIndex(5)
      expect(useGameStore.getState().selectedTileIndex).toBe(5)
    })
  })

  // ── addEvent / clearEvents ──────────────────────────────────────────

  describe('addEvent / clearEvents', () => {
    it('adds a single event', () => {
      useGameStore.getState().addEvent({ event: 'discard', player: 0, tile: 'B1' })
      expect(useGameStore.getState().events).toEqual([
        { event: 'discard', player: 0, tile: 'B1' },
      ])
    })

    it('adds multiple events in order', () => {
      const { addEvent } = useGameStore.getState()
      addEvent({ event: 'draw', player: 0 })
      useGameStore.getState().addEvent({ event: 'discard', player: 0, tile: 'C3' })
      useGameStore.getState().addEvent({ event: 'pong', player: 1, tile: 'C3' })

      const events = useGameStore.getState().events
      expect(events).toHaveLength(3)
      expect(events[0]).toEqual({ event: 'draw', player: 0 })
      expect(events[1]).toEqual({ event: 'discard', player: 0, tile: 'C3' })
      expect(events[2]).toEqual({ event: 'pong', player: 1, tile: 'C3' })
    })

    it('adds event with only event field (no player/tile)', () => {
      useGameStore.getState().addEvent({ event: 'game_start' })
      expect(useGameStore.getState().events).toEqual([{ event: 'game_start' }])
    })

    it('clears all events', () => {
      useGameStore.getState().addEvent({ event: 'draw', player: 0 })
      useGameStore.getState().addEvent({ event: 'discard', player: 0, tile: 'B2' })
      useGameStore.getState().clearEvents()
      expect(useGameStore.getState().events).toEqual([])
    })

    it('clearEvents is idempotent on empty list', () => {
      useGameStore.getState().clearEvents()
      expect(useGameStore.getState().events).toEqual([])
    })
  })

  // ── updateSettings ──────────────────────────────────────────────────

  describe('updateSettings', () => {
    it('merges a single setting', () => {
      useGameStore.getState().updateSettings({ soundEnabled: false })
      const settings = useGameStore.getState().settings
      expect(settings.soundEnabled).toBe(false)
      // Other settings remain unchanged
      expect(settings.animationSpeed).toBe('normal')
      expect(settings.language).toBe('zh-TW')
      expect(settings.tableBackground).toBe('green')
    })

    it('merges multiple settings at once', () => {
      useGameStore.getState().updateSettings({
        animationSpeed: 'fast',
        language: 'en',
      })
      const settings = useGameStore.getState().settings
      expect(settings.animationSpeed).toBe('fast')
      expect(settings.language).toBe('en')
      expect(settings.tableBackground).toBe('green')
      expect(settings.soundEnabled).toBe(true)
    })

    it('overwrites previously changed settings', () => {
      useGameStore.getState().updateSettings({ tableBackground: 'blue' })
      useGameStore.getState().updateSettings({ tableBackground: 'wood' })
      expect(useGameStore.getState().settings.tableBackground).toBe('wood')
    })

    it('handles empty patch without changing settings', () => {
      const before = useGameStore.getState().settings
      useGameStore.getState().updateSettings({})
      const after = useGameStore.getState().settings
      expect(after).toEqual(before)
    })
  })

  // ── setGameState ────────────────────────────────────────────────────

  describe('setGameState', () => {
    const mockGameState: GameState = {
      players: [
        {
          seat: 0,
          hand: ['B1', 'B2', 'B3'],
          hand_count: 3,
          melds: [],
          flowers: [],
          discards: [],
          is_dealer: true,
        },
      ],
      discard_pool: [],
      current_player: 0,
      round_wind: 'E',
      round_number: 1,
      dealer_index: 0,
      wall_remaining: 56,
      last_discard: null,
      phase: 'play',
    }

    it('stores game state', () => {
      useGameStore.getState().setGameState(mockGameState)
      expect(useGameStore.getState().gameState).toEqual(mockGameState)
    })

    it('replaces existing game state', () => {
      useGameStore.getState().setGameState(mockGameState)
      const updated: GameState = {
        ...mockGameState,
        current_player: 1,
        wall_remaining: 55,
        last_discard: 'B1',
      }
      useGameStore.getState().setGameState(updated)
      expect(useGameStore.getState().gameState).toEqual(updated)
      expect(useGameStore.getState().gameState!.current_player).toBe(1)
    })
  })

  // ── setScoringResult ────────────────────────────────────────────────

  describe('setScoringResult', () => {
    const mockScoring: ScoringBreakdown = {
      yaku: [
        ['All Pongs', 4],
        ['Self Draw', 1],
      ],
      subtotal: 5,
      total: 32,
      payments: { 0: 32, 1: -32 },
    }

    it('stores scoring result', () => {
      useGameStore.getState().setScoringResult(mockScoring)
      expect(useGameStore.getState().scoringResult).toEqual(mockScoring)
    })

    it('clears scoring result with null', () => {
      useGameStore.getState().setScoringResult(mockScoring)
      useGameStore.getState().setScoringResult(null)
      expect(useGameStore.getState().scoringResult).toBeNull()
    })
  })

  // ── setMyPlayerIndex ────────────────────────────────────────────────

  describe('setMyPlayerIndex', () => {
    it('sets player index', () => {
      useGameStore.getState().setMyPlayerIndex(2)
      expect(useGameStore.getState().myPlayerIndex).toBe(2)
    })

    it('sets player index to 0', () => {
      useGameStore.getState().setMyPlayerIndex(3)
      useGameStore.getState().setMyPlayerIndex(0)
      expect(useGameStore.getState().myPlayerIndex).toBe(0)
    })
  })

  // ── setTimerSeconds ─────────────────────────────────────────────────

  describe('setTimerSeconds', () => {
    it('sets timer to a new value', () => {
      useGameStore.getState().setTimerSeconds(30)
      expect(useGameStore.getState().timerSeconds).toBe(30)
    })

    it('sets timer to zero', () => {
      useGameStore.getState().setTimerSeconds(0)
      expect(useGameStore.getState().timerSeconds).toBe(0)
    })
  })

  // ── setActionRequest ────────────────────────────────────────────────

  describe('setActionRequest', () => {
    const mockRequest: ActionRequest = {
      player: 0,
      options: [
        { type: 'discard', tile: 'B1', combo: null },
        { type: 'pong', tile: 'C3', combo: ['C3', 'C3', 'C3'] },
      ],
      timeout: 15,
    }

    it('sets action request', () => {
      useGameStore.getState().setActionRequest(mockRequest)
      expect(useGameStore.getState().actionRequest).toEqual(mockRequest)
    })

    it('clears action request with null', () => {
      useGameStore.getState().setActionRequest(mockRequest)
      useGameStore.getState().setActionRequest(null)
      expect(useGameStore.getState().actionRequest).toBeNull()
    })
  })

  // ── Replay state ────────────────────────────────────────────────────

  describe('replay state', () => {
    const mockFrames: ReplayFrame[] = [
      { game_id: 'g1', turn_number: 0, action_json: '{"type":"draw"}', timestamp: '2026-01-01T00:00:00Z' },
      { game_id: 'g1', turn_number: 1, action_json: '{"type":"discard"}', timestamp: '2026-01-01T00:00:01Z' },
      { game_id: 'g1', turn_number: 2, action_json: '{"type":"pong"}', timestamp: '2026-01-01T00:00:02Z' },
    ]

    describe('setReplayFrames', () => {
      it('stores replay frames', () => {
        useGameStore.getState().setReplayFrames(mockFrames)
        expect(useGameStore.getState().replayFrames).toEqual(mockFrames)
        expect(useGameStore.getState().replayFrames).toHaveLength(3)
      })

      it('clears replay frames with null', () => {
        useGameStore.getState().setReplayFrames(mockFrames)
        useGameStore.getState().setReplayFrames(null)
        expect(useGameStore.getState().replayFrames).toBeNull()
      })
    })

    describe('setReplayIndex', () => {
      it('sets replay index', () => {
        useGameStore.getState().setReplayIndex(5)
        expect(useGameStore.getState().replayIndex).toBe(5)
      })

      it('sets replay index to zero', () => {
        useGameStore.getState().setReplayIndex(5)
        useGameStore.getState().setReplayIndex(0)
        expect(useGameStore.getState().replayIndex).toBe(0)
      })
    })

    describe('setReplayPlaying', () => {
      it('sets replay playing to true', () => {
        useGameStore.getState().setReplayPlaying(true)
        expect(useGameStore.getState().replayPlaying).toBe(true)
      })

      it('sets replay playing to false', () => {
        useGameStore.getState().setReplayPlaying(true)
        useGameStore.getState().setReplayPlaying(false)
        expect(useGameStore.getState().replayPlaying).toBe(false)
      })
    })

    describe('setReplaySpeed', () => {
      it('sets replay speed', () => {
        useGameStore.getState().setReplaySpeed(2)
        expect(useGameStore.getState().replaySpeed).toBe(2)
      })

      it('sets replay speed to fractional value', () => {
        useGameStore.getState().setReplaySpeed(0.5)
        expect(useGameStore.getState().replaySpeed).toBe(0.5)
      })
    })
  })

  // ── resetGame ───────────────────────────────────────────────────────

  describe('resetGame', () => {
    it('resets game-related state to defaults', () => {
      // Set up non-default game state
      const mockGameState: GameState = {
        players: [],
        discard_pool: [],
        current_player: 2,
        round_wind: 'S',
        round_number: 3,
        dealer_index: 2,
        wall_remaining: 20,
        last_discard: 'D1',
        phase: 'play',
      }
      useGameStore.getState().setGameState(mockGameState)
      useGameStore.getState().setActionRequest({
        player: 0,
        options: [{ type: 'discard', tile: 'B1', combo: null }],
        timeout: 10,
      })
      useGameStore.getState().setSelectedTileIndex(5)
      useGameStore.getState().setTimerSeconds(5)
      useGameStore.getState().addEvent({ event: 'draw', player: 0 })
      useGameStore.getState().setScoringResult({
        yaku: [['Self Draw', 1]],
        subtotal: 1,
        total: 2,
        payments: { 0: 2 },
      })
      useGameStore.getState().setCurrentScreen('game')

      // Reset
      useGameStore.getState().resetGame()

      // Verify game-related fields are reset
      const state = useGameStore.getState()
      expect(state.gameState).toBeNull()
      expect(state.actionRequest).toBeNull()
      expect(state.selectedTileIndex).toBeNull()
      expect(state.timerSeconds).toBe(10)
      expect(state.events).toEqual([])
      expect(state.scoringResult).toBeNull()
      expect(state.currentScreen).toBe('lobby')
    })

    it('does not reset non-game state (connected, myPlayerIndex, settings, replay)', () => {
      // Set up non-game state
      useGameStore.getState().setConnected(true)
      useGameStore.getState().setMyPlayerIndex(3)
      useGameStore.getState().updateSettings({ soundEnabled: false, language: 'en' })
      useGameStore.getState().setReplayFrames([
        { game_id: 'g1', turn_number: 0, action_json: '{}', timestamp: '2026-01-01T00:00:00Z' },
      ])
      useGameStore.getState().setReplayIndex(5)
      useGameStore.getState().setReplayPlaying(true)
      useGameStore.getState().setReplaySpeed(2)

      // Reset
      useGameStore.getState().resetGame()

      // Verify non-game fields are NOT reset
      const state = useGameStore.getState()
      expect(state.connected).toBe(true)
      expect(state.myPlayerIndex).toBe(3)
      expect(state.settings.soundEnabled).toBe(false)
      expect(state.settings.language).toBe('en')
      expect(state.replayFrames).toHaveLength(1)
      expect(state.replayIndex).toBe(5)
      expect(state.replayPlaying).toBe(true)
      expect(state.replaySpeed).toBe(2)
    })
  })
})
