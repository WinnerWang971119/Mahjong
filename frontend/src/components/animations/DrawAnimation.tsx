import { motion } from 'framer-motion'
import Tile from '../tiles/Tile'

interface DrawAnimationProps {
  tile: string
  onComplete: () => void
}

export default function DrawAnimation({ tile, onComplete }: DrawAnimationProps) {
  return (
    <motion.div
      initial={{ x: 200, y: -100, opacity: 0 }}
      animate={{ x: 0, y: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      onAnimationComplete={onComplete}
      className="fixed z-50"
    >
      <Tile code={tile} />
    </motion.div>
  )
}
