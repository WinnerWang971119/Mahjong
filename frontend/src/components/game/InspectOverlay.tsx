interface AiThinkingData {
  player: number
  shanten: number
  top_discards?: string[]
  waiting_tiles?: string[]
}

interface InspectOverlayProps {
  thinkingData: AiThinkingData[]
}

const WIND_LABELS = ['東', '南', '西', '北']

export default function InspectOverlay({ thinkingData }: InspectOverlayProps) {
  if (thinkingData.length === 0) return null

  return (
    <div className="absolute top-16 right-4 flex flex-col gap-2 z-40">
      {thinkingData.map((data) => (
        <div key={data.player} className="bg-black/70 text-white rounded-lg p-3 text-xs w-48">
          <div className="font-bold mb-1">{WIND_LABELS[data.player]}家 AI</div>
          <div>向聽數: <span className="text-yellow-400">{data.shanten}</span></div>
          {data.top_discards && data.top_discards.length > 0 && (
            <div>候選: {data.top_discards.join(', ')}</div>
          )}
          {data.waiting_tiles && data.waiting_tiles.length > 0 && (
            <div>聽牌: {data.waiting_tiles.join(', ')}</div>
          )}
        </div>
      ))}
    </div>
  )
}
