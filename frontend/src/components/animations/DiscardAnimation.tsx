import { motion } from 'framer-motion'
import Tile from '../tiles/Tile'

interface DiscardAnimationProps {
  tile: string
  onComplete: () => void
}

export default function DiscardAnimation({ tile, onComplete }: DiscardAnimationProps) {
  return (
    <motion.div
      initial={{ scale: 1, y: 0 }}
      animate={{ scale: 0.8, y: 100, rotateY: 180 }}
      transition={{ duration: 0.4, ease: 'easeIn' }}
      onAnimationComplete={onComplete}
      className="fixed z-50"
    >
      <Tile code={tile} />
    </motion.div>
  )
}
