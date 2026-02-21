import Tile from '../tiles/Tile'

interface HandTilesProps {
  tiles: string[] | null
  tileCount: number
  isSelf: boolean
  selectedTile: string | null
  onTileClick?: (tile: string) => void
}

export default function HandTiles({ tiles, tileCount, isSelf, selectedTile, onTileClick }: HandTilesProps) {
  if (isSelf && tiles) {
    return (
      <div className="flex gap-0.5 justify-center">
        {tiles.map((tile, i) => (
          <Tile
            key={`${tile}-${i}`}
            code={tile}
            faceUp
            selected={selectedTile === tile}
            onClick={() => onTileClick?.(tile)}
          />
        ))}
      </div>
    )
  }

  // Opponents: face-down tiles
  return (
    <div className="flex gap-0.5 justify-center">
      {Array.from({ length: tileCount }, (_, i) => (
        <Tile key={i} code="" faceUp={false} />
      ))}
    </div>
  )
}
