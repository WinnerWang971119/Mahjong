interface FlowerTileProps {
  index: number // 1-8
}

// f1-f4: Seasons (春夏秋冬), f5-f8: Plants (梅蘭竹菊)
const FLOWERS: Record<number, { char: string; subtitle: string }> = {
  1: { char: '春', subtitle: 'Spring' },
  2: { char: '夏', subtitle: 'Summer' },
  3: { char: '秋', subtitle: 'Autumn' },
  4: { char: '冬', subtitle: 'Winter' },
  5: { char: '梅', subtitle: 'Plum' },
  6: { char: '蘭', subtitle: 'Orchid' },
  7: { char: '竹', subtitle: 'Bamboo' },
  8: { char: '菊', subtitle: 'Chrysan.' },
}

export default function FlowerTile({ index }: FlowerTileProps) {
  const info = FLOWERS[index]
  if (!info) return null

  return (
    <g>
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        y="-4"
        fontSize="18"
        fontFamily="'Noto Sans TC', sans-serif"
        fontWeight="700"
        fill="#ca8a04"
      >
        {info.char}
      </text>
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        y="14"
        fontSize="6"
        fill="#a16207"
      >
        {info.subtitle}
      </text>
    </g>
  )
}
