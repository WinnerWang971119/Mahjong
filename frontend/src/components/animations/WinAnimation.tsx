import { motion } from 'framer-motion'
import Tile from '../tiles/Tile'

interface WinAnimationProps {
  tiles: string[]
  onComplete: () => void
}

export default function WinAnimation({ tiles, onComplete }: WinAnimationProps) {
  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ duration: 0.8, ease: 'easeOut' }}
      onAnimationComplete={onComplete}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
    >
      <div className="flex flex-col items-center gap-4">
        <motion.h2
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="text-4xl font-bold text-yellow-400"
          style={{ textShadow: '0 0 20px rgba(250, 204, 21, 0.5)' }}
        >
          {'\u80E1\u724C\uFF01'}
        </motion.h2>
        <div className="flex gap-1">
          {tiles.map((tile, i) => (
            <motion.div
              key={i}
              initial={{ y: 20, opacity: 0, rotate: -10 + Math.random() * 20 }}
              animate={{ y: 0, opacity: 1, rotate: (i - tiles.length / 2) * 3 }}
              transition={{ delay: 0.2 + i * 0.05, duration: 0.4 }}
            >
              <Tile code={tile} />
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
