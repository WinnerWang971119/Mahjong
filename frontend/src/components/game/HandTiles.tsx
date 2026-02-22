import { useMemo } from 'react'
import Tile from '../tiles/Tile'

interface HandTilesProps {
  tiles: string[] | null
  tileCount: number
  isSelf: boolean
  selectedTileIndex: number | null
  onTileClick?: (index: number) => void
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

export default function HandTiles({ tiles, tileCount, isSelf, selectedTileIndex, onTileClick }: HandTilesProps) {
  const sortedWithIndices = useMemo(() => {
    if (!tiles) return null
    return tiles
      .map((tile, originalIndex) => ({ tile, originalIndex }))
      .sort((a, b) => tileSortKey(a.tile) - tileSortKey(b.tile))
  }, [tiles])

  if (isSelf && sortedWithIndices) {
    return (
      <div className="flex gap-0.5 justify-center flex-wrap">
        {sortedWithIndices.map((item, displayIndex) => (
          <Tile
            key={`${item.tile}-${item.originalIndex}`}
            code={item.tile}
            faceUp
            selected={selectedTileIndex === item.originalIndex}
            onClick={() => onTileClick?.(item.originalIndex)}
          />
        ))}
      </div>
    )
  }

  // Opponents: face-down tiles
  return (
    <div className="flex gap-0.5 justify-center flex-wrap">
      {Array.from({ length: tileCount }, (_, i) => (
        <Tile key={i} code="" faceUp={false} />
      ))}
    </div>
  )
}
