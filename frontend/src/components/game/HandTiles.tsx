import { useMemo } from 'react'
import Tile from '../tiles/Tile'

interface HandTilesProps {
  tiles: string[] | null
  tileCount: number
  isSelf: boolean
  selectedTileIndex: number | null
  onTileClick?: (index: number) => void
  position?: 'bottom' | 'right' | 'top' | 'left'
}

const SUIT_ORDER: Record<string, number> = { m: 0, p: 1, s: 2 }
const HONOR_ORDER: Record<string, number> = { E: 0, S: 1, W: 2, N: 3, C: 4, F: 5, B: 6 }

function tileSortKey(code: string): number {
  if (code.length === 2 && SUIT_ORDER[code[1]] !== undefined) {
    return SUIT_ORDER[code[1]] * 100 + parseInt(code[0], 10)
  }
  if (code.length === 1 && HONOR_ORDER[code] !== undefined) {
    return 300 + HONOR_ORDER[code]
  }
  return 999 // unknown tiles at end
}

export default function HandTiles({ tiles, tileCount, isSelf, selectedTileIndex, onTileClick, position }: HandTilesProps) {
  const isSide = position === 'left' || position === 'right'

  const sortedWithIndices = useMemo(() => {
    if (!tiles) return null
    return tiles
      .map((tile, originalIndex) => ({ tile, originalIndex }))
      .sort((a, b) => tileSortKey(a.tile) - tileSortKey(b.tile))
  }, [tiles])

  if (isSelf && sortedWithIndices) {
    return (
      <div className={isSide ? 'flex flex-col gap-0.5 items-center' : 'flex gap-0.5 justify-center flex-wrap'}>
        {sortedWithIndices.map((item) => (
          <div key={`${item.tile}-${item.originalIndex}`} className={isSide ? 'rotate-90' : ''}>
            <Tile
              code={item.tile}
              faceUp
              selected={selectedTileIndex === item.originalIndex}
              onClick={() => onTileClick?.(item.originalIndex)}
            />
          </div>
        ))}
      </div>
    )
  }

  // Opponents: face-down tiles
  return (
    <div className={isSide ? 'flex flex-col gap-0.5 items-center' : 'flex gap-0.5 justify-center flex-wrap'}>
      {Array.from({ length: tileCount }, (_, i) => (
        <div key={i} className={isSide ? 'rotate-90' : ''}>
          <Tile code="" faceUp={false} />
        </div>
      ))}
    </div>
  )
}
