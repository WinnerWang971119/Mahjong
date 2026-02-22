import { useState } from 'react'
import { motion } from 'framer-motion'
import type { ActionOption } from '../../types/game'

interface ActionPanelProps {
  options: ActionOption[]
  onAction: (action: string, tile?: string, combo?: string[]) => void
}

const ACTION_LABELS: Record<string, string> = {
  discard: '打',
  chi: '吃',
  pong: '碰',
  open_kong: '槓',
  added_kong: '槓',
  concealed_kong: '暗槓',
  win: '胡',
  pass: '過',
  draw: '摸',
}

const ACTION_COLORS: Record<string, string> = {
  win: 'bg-red-600 hover:bg-red-700',
  chi: 'bg-blue-600 hover:bg-blue-700',
  pong: 'bg-green-600 hover:bg-green-700',
  open_kong: 'bg-purple-600 hover:bg-purple-700',
  added_kong: 'bg-purple-600 hover:bg-purple-700',
  concealed_kong: 'bg-purple-600 hover:bg-purple-700',
  pass: 'bg-gray-600 hover:bg-gray-700',
}

export default function ActionPanel({ options, onAction }: ActionPanelProps) {
  const [showChiCombos, setShowChiCombos] = useState(false)

  // Group actions: separate chi combos, deduplicate others
  const chiOptions = options.filter((o) => o.type === 'chi')
  const otherOptions = options.filter((o) => o.type !== 'chi' && o.type !== 'discard')

  // Deduplicate by type (keep one per type)
  const seen = new Set<string>()
  const uniqueOthers = otherOptions.filter((o) => {
    if (seen.has(o.type)) return false
    seen.add(o.type)
    return true
  })

  // Build the display list (chi handled separately as one button)
  const displayActions = [...uniqueOthers]

  return (
    <div className="flex flex-col items-center gap-2 p-4 bg-black/60 rounded-t-lg">
      {showChiCombos ? (
        <div className="flex gap-2">
          <span className="text-white text-sm self-center mr-2">選擇吃牌組合:</span>
          {chiOptions.map((opt, i) => (
            <button
              key={i}
              onClick={() => {
                onAction('chi', opt.tile ?? undefined, opt.combo ?? undefined)
                setShowChiCombos(false)
              }}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white rounded-lg text-sm font-bold transition-all duration-100"
            >
              {opt.combo?.join(' ') || 'Chi'}
            </button>
          ))}
          <button
            onClick={() => setShowChiCombos(false)}
            className="px-3 py-2 bg-gray-600 hover:bg-gray-700 active:scale-95 text-white rounded-lg text-sm transition-all duration-100"
          >
            取消
          </button>
        </div>
      ) : (
        <motion.div
          initial={{ y: 16, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          className="flex gap-2"
        >
          {chiOptions.length > 0 && (
            <button
              onClick={() => {
                if (chiOptions.length === 1) {
                  const opt = chiOptions[0]
                  onAction('chi', opt.tile ?? undefined, opt.combo ?? undefined)
                } else {
                  setShowChiCombos(true)
                }
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white rounded-lg font-bold transition-all duration-100"
            >
              吃 (Chi)
            </button>
          )}
          {displayActions.map((opt) => (
            <button
              key={opt.type}
              onClick={() => onAction(opt.type, opt.tile ?? undefined, opt.combo ?? undefined)}
              className={`px-4 py-2 text-white rounded-lg font-bold active:scale-95 transition-all duration-100 ${ACTION_COLORS[opt.type] || 'bg-gray-600 hover:bg-gray-700'}`}
            >
              {ACTION_LABELS[opt.type] || opt.type} ({opt.type})
            </button>
          ))}
        </motion.div>
      )}
    </div>
  )
}
