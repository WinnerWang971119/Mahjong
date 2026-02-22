// Wind and phase types
export type Wind = 'E' | 'S' | 'W' | 'N'
export type Phase = 'deal' | 'flower_replacement' | 'play' | 'win' | 'draw'
export type MeldType = 'chi' | 'pong' | 'open_kong' | 'added_kong' | 'concealed_kong'
export type ActionType = 'draw' | 'discard' | 'chi' | 'pong' | 'open_kong' | 'added_kong' | 'concealed_kong' | 'win' | 'pass'

// Core game state (mirrors server serializer output)
export interface GameState {
  players: PlayerState[]
  discard_pool: string[]
  current_player: number
  round_wind: Wind
  round_number: number
  dealer_index: number
  wall_remaining: number
  last_discard: string | null
  phase: Phase
}

export interface PlayerState {
  seat: number
  hand: string[] | null  // null for opponents (hidden)
  hand_count: number
  melds: Meld[]
  flowers: string[]
  discards: string[]
  is_dealer: boolean
}

export interface Meld {
  type: MeldType
  tiles: string[]
  from_player: number | null
}

// Action request from server
export interface ActionRequest {
  player: number
  options: ActionOption[]
  timeout: number
}

export interface ActionOption {
  type: ActionType
  tile: string | null
  combo: string[] | null
}

// Server → Client messages
export type ServerMessage =
  | { type: 'game_state'; state: GameState }
  | { type: 'action_request'; player: number; options: ActionOption[]; timeout: number }
  | { type: 'event'; event: string; player?: number; tile?: string; state?: GameState; scoring?: ScoringBreakdown }
  | { type: 'replay_data'; game_id: string; frames: ReplayFrame[] }
  | { type: 'error'; message: string }

// Client → Server messages
export type ClientMessage =
  | { type: 'new_game'; mode: string; human_seat?: number }
  | { type: 'action'; action: string; tile?: string; combo?: string[] }
  | { type: 'replay_load'; game_id: string }

// Replay
export interface ReplayFrame {
  game_id: string
  turn_number: number
  action_json: string
  timestamp: string
}

// Scoring
export interface ScoringBreakdown {
  yaku: [string, number][]
  subtotal: number
  total: number
  payments: Record<number, number>
}

// Game history
export interface GameHistoryEntry {
  game_id: string
  mode: string
  started_at: string
  ended_at: string | null
  human_seat: number
  result: string | null
}

// ELO history
export interface EloHistoryEntry {
  game_id: string
  elo_before: number
  elo_after: number
  recorded_at: string
}

// Settings
export interface GameSettings {
  animationSpeed: 'slow' | 'normal' | 'fast' | 'instant'
  language: 'zh-TW' | 'en'
  tableBackground: 'green' | 'blue' | 'wood'
  soundEnabled: boolean
}
