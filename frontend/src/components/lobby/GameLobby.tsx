interface GameLobbyProps {
  onStartGame: (mode: string) => void
  connected: boolean
}

export default function GameLobby({ onStartGame, connected }: GameLobbyProps) {
  return (
    <div className="min-h-screen bg-table-green flex flex-col items-center justify-center gap-8">
      <h1 className="text-5xl font-bold text-white">台灣16張麻將</h1>
      <p className="text-white/70 text-lg">Taiwan 16-Tile Mahjong</p>

      <div className="flex flex-col gap-4 w-64">
        <button
          onClick={() => onStartGame('easy')}
          disabled={!connected}
          className="px-6 py-3 bg-white text-table-green font-bold rounded-lg text-lg hover:bg-tile-cream transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          簡單模式 (Easy)
        </button>
        <button
          disabled
          className="px-6 py-3 bg-white/30 text-white/50 font-bold rounded-lg text-lg cursor-not-allowed"
        >
          困難模式 (Hard) — Phase 4
        </button>
        <button
          onClick={() => onStartGame('inspect')}
          disabled={!connected}
          className="px-6 py-3 bg-white/80 text-table-green font-bold rounded-lg text-lg hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          觀戰模式 (Inspect)
        </button>
      </div>

      {!connected && (
        <p className="text-red-300 text-sm">連線中... Connecting to server...</p>
      )}
    </div>
  )
}
