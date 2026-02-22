import type { ReactNode } from 'react'
import TileBase from './TileBase'
import CharacterTile from './suits/CharacterTile'
import CircleTile from './suits/CircleTile'
import BambooTile from './suits/BambooTile'
import HonorTile from './suits/HonorTile'
import FlowerTile from './suits/FlowerTile'

interface TileProps {
  code: string          // "1m", "9p", "5s", "E", "C", "f3", etc.
  faceUp?: boolean
  selected?: boolean
  highlighted?: boolean
  disabled?: boolean
  onClick?: () => void
}

function parseTileCode(code: string): ReactNode | null {
  // Flowers: f1-f8
  if (code.startsWith('f') && code.length === 2) {
    const idx = parseInt(code[1], 10)
    return <FlowerTile index={idx} />
  }

  // Honor tiles: E, S, W, N, C, F, B
  if (code.length === 1 && 'ESWNFCB'.includes(code)) {
    return <HonorTile code={code} />
  }

  // Number tiles: 1m-9m, 1p-9p, 1s-9s
  if (code.length === 2) {
    const value = parseInt(code[0], 10)
    const suit = code[1]
    if (suit === 'm') return <CharacterTile value={value} />
    if (suit === 'p') return <CircleTile value={value} />
    if (suit === 's') return <BambooTile value={value} />
  }

  return null
}

export default function Tile({ code, faceUp = true, selected, highlighted, disabled, onClick }: TileProps) {
  return (
    <TileBase faceUp={faceUp} selected={selected} highlighted={highlighted} disabled={disabled} onClick={onClick}>
      {faceUp && parseTileCode(code)}
    </TileBase>
  )
}
