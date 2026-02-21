interface HonorTileProps {
  code: string // E, S, W, N, C, F, B
}

const HONOR_CHARS: Record<string, { char: string; color: string }> = {
  E: { char: '東', color: '#1e293b' },
  S: { char: '南', color: '#1e293b' },
  W: { char: '西', color: '#1e293b' },
  N: { char: '北', color: '#1e293b' },
  C: { char: '中', color: '#c41e3a' },  // Red
  F: { char: '發', color: '#16a34a' },  // Green
  B: { char: '白', color: '#64748b' },  // Gray border only
}

export default function HonorTile({ code }: HonorTileProps) {
  const info = HONOR_CHARS[code]
  if (!info) return null

  if (code === 'B') {
    // 白板 - empty tile with border
    return (
      <rect x="-10" y="-10" width="20" height="20" rx="2" fill="none" stroke="#64748b" strokeWidth="1.5" />
    )
  }

  return (
    <text
      textAnchor="middle"
      dominantBaseline="middle"
      fontSize="20"
      fontFamily="'Noto Sans TC', sans-serif"
      fontWeight="700"
      fill={info.color}
    >
      {info.char}
    </text>
  )
}
