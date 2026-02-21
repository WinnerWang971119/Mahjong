import Tile from '../tiles/Tile'

interface FlowerAreaProps {
  flowers: string[]
}

export default function FlowerArea({ flowers }: FlowerAreaProps) {
  if (flowers.length === 0) return null

  return (
    <div className="flex gap-0.5">
      {flowers.map((flower, i) => (
        <Tile key={i} code={flower} faceUp />
      ))}
    </div>
  )
}
