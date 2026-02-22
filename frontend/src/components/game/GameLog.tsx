const WIND_LABELS = ['東', '南', '西', '北']
const ACTION_ZH: Record<string, string> = {
  discard: '打出',
  draw: '摸牌',
  chi: '吃',
  pong: '碰',
  open_kong: '明槓',
  added_kong: '加槓',
  concealed_kong: '暗槓',
  win: '胡牌',
  pass: '過',
}

interface GameLogProps {
  events: Array<{ event: string; player?: number; tile?: string }>
}

export default function GameLog({ events }: GameLogProps) {
  return (
    <div className="w-48 shrink-0 bg-black/30 p-2 overflow-y-auto">
      <h3 className="text-white text-sm font-bold mb-2">遊戲紀錄</h3>
      <div className="flex flex-col gap-1">
        {events.map((e, i) => {
          const wind = e.player !== undefined ? WIND_LABELS[e.player] : '?'
          const action = ACTION_ZH[e.event] || e.event
          return (
            <div key={i} className="text-white/80 text-xs">
              [{wind}家] {action} {e.tile || ''}
            </div>
          )
        })}
      </div>
    </div>
  )
}
