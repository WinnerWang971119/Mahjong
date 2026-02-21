import Tile from '../tiles/Tile'

interface DiscardPoolProps {
  discards: string[]
  lastDiscard: string | null
}

export default function DiscardPool({ discards, lastDiscard }: DiscardPoolProps) {
  return (
    <div className="grid grid-cols-6 gap-0.5 p-2 bg-black/20 rounded-lg">
      {discards.map((tile, i) => (
        <Tile
          key={i}
          code={tile}
          faceUp
          highlighted={tile === lastDiscard && i === discards.length - 1}
        />
      ))}
    </div>
  )
}
