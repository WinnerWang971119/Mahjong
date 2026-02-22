import Tile from '../tiles/Tile'

interface FlowerAreaProps {
  flowers: string[]
  position?: 'bottom' | 'right' | 'top' | 'left'
}

export default function FlowerArea({ flowers, position }: FlowerAreaProps) {
  if (flowers.length === 0) return null

  const isSide = position === 'left' || position === 'right'

  return (
    <div className={isSide ? 'flex flex-col gap-0.5' : 'flex gap-0.5'}>
      {flowers.map((flower, i) => (
        <div key={i} className={isSide ? 'rotate-90' : ''}>
          <Tile code={flower} faceUp />
        </div>
      ))}
    </div>
  )
}
