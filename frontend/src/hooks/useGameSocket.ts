import { useEffect, useRef, useCallback } from 'react'
import { useGameStore } from '../store/gameStore'
import type { ServerMessage, ClientMessage } from '../types/game'

const WS_URL = 'ws://127.0.0.1:9000/ws'
const RECONNECT_DELAY_MS = 2000
const MAX_RECONNECT_ATTEMPTS = 10

export function useGameSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const setConnected = useGameStore((s) => s.setConnected)
  const setGameState = useGameStore((s) => s.setGameState)
  const setActionRequest = useGameStore((s) => s.setActionRequest)
  const addEvent = useGameStore((s) => s.addEvent)
  const setCurrentScreen = useGameStore((s) => s.setCurrentScreen)

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      const msg: ServerMessage = JSON.parse(event.data) as ServerMessage

      switch (msg.type) {
        case 'game_state':
          setGameState(msg.state)
          setCurrentScreen('game')
          break
        case 'action_request':
          setActionRequest({
            player: msg.player,
            options: msg.options,
            timeout: msg.timeout,
          })
          break
        case 'event':
          addEvent({ event: msg.event, player: msg.player, tile: msg.tile })
          // Handle game end events — transition to scoring screen
          if (msg.event === 'win' || msg.event === 'draw') {
            if (msg.state) {
              setGameState(msg.state)
            }
            if (msg.scoring) {
              useGameStore.getState().setScoringResult(msg.scoring)
            }
            setActionRequest(null)
            setCurrentScreen('scoring')
          }
          break
        case 'replay_data':
          useGameStore.getState().setReplayFrames(msg.frames)
          setCurrentScreen('replay')
          break
        case 'error':
          console.error('[ws] Server error:', msg.message)
          break
      }
    },
    [setGameState, setActionRequest, addEvent, setCurrentScreen],
  )

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      setConnected(true)
      reconnectAttemptsRef.current = 0
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
      // Auto-reconnect with exponential backoff
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_DELAY_MS * Math.pow(1.5, reconnectAttemptsRef.current)
        reconnectTimerRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++
          connect()
        }, delay)
      }
    }

    ws.onerror = (err) => {
      console.error('[ws] Error:', err)
    }

    ws.onmessage = handleMessage
    wsRef.current = ws
  }, [handleMessage, setConnected])

  // Send a raw ClientMessage if the socket is open
  const send = useCallback((msg: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  const sendNewGame = useCallback(
    (mode: string, humanSeat = 0) => {
      send({ type: 'new_game', mode, human_seat: humanSeat })
    },
    [send],
  )

  const sendAction = useCallback(
    (action: string, tile?: string, combo?: string[]) => {
      const msg: ClientMessage = { type: 'action', action, tile, combo }
      send(msg)
      // Clear action request and tile selection immediately for UI responsiveness
      useGameStore.getState().setActionRequest(null)
      useGameStore.getState().setSelectedTileIndex(null)
    },
    [send],
  )

  const sendReplayLoad = useCallback(
    (gameId: string) => {
      send({ type: 'replay_load', game_id: gameId })
    },
    [send],
  )

  // Connect on mount; clean up timer and socket on unmount
  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  return {
    sendNewGame,
    sendAction,
    sendReplayLoad,
    connected: useGameStore((s) => s.connected),
  }
}
