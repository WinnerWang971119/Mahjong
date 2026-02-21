import { useGameStore } from './store/gameStore'
import { useGameSocket } from './hooks/useGameSocket'
import GameLobby from './components/lobby/GameLobby'
import GameView from './components/game/GameView'
import DevTileGallery from './pages/DevTileGallery'

export default function App() {
  const currentScreen = useGameStore((s) => s.currentScreen)
  const { sendNewGame, sendAction, connected } = useGameSocket()

  // Dev mode: show tile gallery with query param ?dev=tiles
  if (typeof window !== 'undefined' && window.location.search.includes('dev=tiles')) {
    return <DevTileGallery />
  }

  switch (currentScreen) {
    case 'lobby':
      return <GameLobby onStartGame={sendNewGame} connected={connected} />
    case 'game':
      return <GameView onAction={sendAction} />
    case 'scoring':
      // Reuse GameView for now, scoring modal will be added in Group 5
      return <GameView onAction={sendAction} />
    default:
      return <GameLobby onStartGame={sendNewGame} connected={connected} />
  }
}
