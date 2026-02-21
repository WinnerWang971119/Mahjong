interface CharacterTileProps {
  value: number // 1-9
}

const NUMERALS = ['一', '二', '三', '四', '五', '六', '七', '八', '九']

export default function CharacterTile({ value }: CharacterTileProps) {
  return (
    <g>
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        y="-8"
        fontSize="16"
        fontFamily="'Noto Sans TC', sans-serif"
        fontWeight="700"
        fill="#c41e3a"
      >
        {NUMERALS[value - 1]}
      </text>
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        y="12"
        fontSize="12"
        fontFamily="'Noto Sans TC', sans-serif"
        fontWeight="500"
        fill="#c41e3a"
      >
        萬
      </text>
    </g>
  )
}
