import { motion } from 'framer-motion'
import Tile from '../tiles/Tile'

interface MeldAnimationProps {
  tiles: string[]
  meldType: string
  onComplete: () => void
}

export default function MeldAnimation({ tiles, meldType, onComplete }: MeldAnimationProps) {
  return (
    <motion.div
      initial={{ scale: 0.5, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      onAnimationComplete={onComplete}
      className="fixed z-50 flex gap-1 items-center"
    >
      <span className="text-white text-lg font-bold mr-2">
        {meldType === 'chi' ? '\u5403' : meldType === 'pong' ? '\u78B0' : '\u69D3'}
      </span>
      {tiles.map((tile, i) => (
        <motion.div
          key={i}
          initial={{ y: -30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: i * 0.1, duration: 0.3 }}
        >
          <Tile code={tile} />
        </motion.div>
      ))}
    </motion.div>
  )
}
