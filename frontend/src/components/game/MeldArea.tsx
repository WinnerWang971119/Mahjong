import Tile from '../tiles/Tile'
import type { Meld } from '../../types/game'

interface MeldAreaProps {
  melds: Meld[]
}

export default function MeldArea({ melds }: MeldAreaProps) {
  if (melds.length === 0) return null

  return (
    <div className="flex gap-2">
      {melds.map((meld, i) => (
        <div key={i} className="flex gap-0.5">
          {meld.tiles.map((tile, j) => (
            <Tile key={j} code={tile} faceUp />
          ))}
        </div>
      ))}
    </div>
  )
}
