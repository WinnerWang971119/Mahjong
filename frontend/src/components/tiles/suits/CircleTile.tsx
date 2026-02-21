interface CircleTileProps {
  value: number // 1-9
}

// Circle positions for each value (centered at 0,0 in a ~30x40 space)
const LAYOUTS: Record<number, [number, number][]> = {
  1: [[0, 0]],
  2: [[0, -10], [0, 10]],
  3: [[0, -12], [-8, 8], [8, 8]],
  4: [[-7, -7], [7, -7], [-7, 7], [7, 7]],
  5: [[-7, -7], [7, -7], [0, 0], [-7, 7], [7, 7]],
  6: [[-7, -10], [7, -10], [-7, 0], [7, 0], [-7, 10], [7, 10]],
  7: [[-7, -10], [7, -10], [-7, 0], [7, 0], [-7, 10], [0, 10], [7, 10]],
  8: [[-7, -10], [0, -10], [7, -10], [-7, 0], [7, 0], [-7, 10], [0, 10], [7, 10]],
  9: [[-7, -10], [0, -10], [7, -10], [-7, 0], [0, 0], [7, 0], [-7, 10], [0, 10], [7, 10]],
}

export default function CircleTile({ value }: CircleTileProps) {
  const positions = LAYOUTS[value] || []
  const radius = value === 1 ? 10 : 5

  return (
    <g>
      {positions.map(([cx, cy], i) => (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={radius}
          fill="#2563eb"
          stroke="#1d4ed8"
          strokeWidth="0.5"
        />
      ))}
    </g>
  )
}
