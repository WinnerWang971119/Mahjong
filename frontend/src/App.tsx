import { useGameStore } from './store/gameStore'
import { useGameSocket } from './hooks/useGameSocket'
import { useSettingsPersistence } from './hooks/useSettings'
import GameLobby from './components/lobby/GameLobby'
import GameView from './components/game/GameView'
import ScoringScreen from './components/scoring/ScoringScreen'
import SettingsPanel from './components/settings/SettingsPanel'
import ReplayViewer from './components/replay/ReplayViewer'
import EloHistory from './components/history/EloHistory'
import DevTileGallery from './pages/DevTileGallery'

export default function App() {
  useSettingsPersistence()
  const currentScreen = useGameStore((s) => s.currentScreen)
  const setCurrentScreen = useGameStore((s) => s.setCurrentScreen)
  const scoringResult = useGameStore((s) => s.scoringResult)
  const resetGame = useGameStore((s) => s.resetGame)
  const { sendNewGame, sendAction, connected } = useGameSocket()

  // Dev mode: show tile gallery with query param ?dev=tiles
  if (typeof window !== 'undefined' && window.location.search.includes('dev=tiles')) {
    return <DevTileGallery />
  }

  switch (currentScreen) {
    case 'lobby':
      return (
        <GameLobby
          onStartGame={sendNewGame}
          connected={connected}
          onNavigate={setCurrentScreen}
        />
      )
    case 'game':
      return <GameView onAction={sendAction} />
    case 'scoring':
      return (
        <>
          <GameView onAction={sendAction} />
          <ScoringScreen
            scoring={scoringResult}
            onContinue={() => {
              resetGame()
              setCurrentScreen('lobby')
            }}
          />
        </>
      )
    case 'settings':
      return <SettingsPanel onBack={() => setCurrentScreen('lobby')} />
    case 'replay':
      return <ReplayViewer onBack={() => setCurrentScreen('lobby')} />
    case 'history':
      return <EloHistory onBack={() => setCurrentScreen('lobby')} />
    default:
      return <GameLobby onStartGame={sendNewGame} connected={connected} onNavigate={setCurrentScreen} />
  }
}
