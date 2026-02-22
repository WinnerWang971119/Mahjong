import Tile from '../tiles/Tile'
import type { Meld } from '../../types/game'

interface MeldAreaProps {
  melds: Meld[]
  position?: 'bottom' | 'right' | 'top' | 'left'
}

export default function MeldArea({ melds, position }: MeldAreaProps) {
  if (melds.length === 0) return null

  const isSide = position === 'left' || position === 'right'

  return (
    <div className={isSide ? 'flex flex-col gap-1' : 'flex gap-2'}>
      {melds.map((meld, i) => (
        <div key={i} className={isSide ? 'flex flex-col gap-0.5' : 'flex gap-0.5'}>
          {meld.tiles.map((tile, j) => (
            <div key={j} className={isSide ? 'rotate-90' : ''}>
              <Tile code={tile} faceUp />
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
