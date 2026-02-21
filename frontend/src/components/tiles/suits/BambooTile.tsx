interface BambooTileProps {
  value: number // 1-9
}

// For 1s, use a bird/special symbol. For 2-9, use green bamboo sticks.
// [x, y, vertical] - position and orientation of each stick
const STICK_LAYOUTS: Record<number, [number, number, boolean][]> = {
  2: [[-5, 0, true], [5, 0, true]],
  3: [[-7, 0, true], [0, 0, true], [7, 0, true]],
  4: [[-5, -8, true], [5, -8, true], [-5, 8, true], [5, 8, true]],
  5: [[-5, -8, true], [5, -8, true], [0, 0, true], [-5, 8, true], [5, 8, true]],
  6: [[-5, -10, true], [5, -10, true], [-5, 0, true], [5, 0, true], [-5, 10, true], [5, 10, true]],
  7: [[-5, -10, true], [5, -10, true], [-5, 0, true], [5, 0, true], [-5, 10, true], [0, 10, true], [5, 10, true]],
  8: [[-5, -10, true], [0, -10, true], [5, -10, true], [-5, 0, true], [5, 0, true], [-5, 10, true], [0, 10, true], [5, 10, true]],
  9: [[-5, -10, true], [0, -10, true], [5, -10, true], [-5, 0, true], [0, 0, true], [5, 0, true], [-5, 10, true], [0, 10, true], [5, 10, true]],
}

function BambooStick({ x, y }: { x: number; y: number }) {
  return (
    <rect
      x={x - 2}
      y={y - 7}
      width="4"
      height="14"
      rx="1"
      fill="#16a34a"
      stroke="#15803d"
      strokeWidth="0.5"
    />
  )
}

export default function BambooTile({ value }: BambooTileProps) {
  if (value === 1) {
    // Bird symbol for 1s (一索)
    return (
      <g>
        <circle cx="0" cy="-4" r="6" fill="#16a34a" />
        <ellipse cx="0" cy="8" rx="10" ry="5" fill="#16a34a" />
        <polygon points="-12,2 -6,0 -6,4" fill="#15803d" />
      </g>
    )
  }

  const sticks = STICK_LAYOUTS[value] || []
  return (
    <g>
      {sticks.map(([x, y], i) => (
        <BambooStick key={i} x={x} y={y} />
      ))}
    </g>
  )
}
