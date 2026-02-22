import type { ReactNode } from 'react'
import Tile from '../components/tiles/Tile'

// All 42 unique tile codes
const CHARACTERS = ['1m', '2m', '3m', '4m', '5m', '6m', '7m', '8m', '9m']
const CIRCLES = ['1p', '2p', '3p', '4p', '5p', '6p', '7p', '8p', '9p']
const BAMBOO = ['1s', '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s']
const HONORS = ['E', 'S', 'W', 'N', 'C', 'F', 'B']
const FLOWERS = ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8']

export default function DevTileGallery() {
  return (
    <div className="min-h-screen bg-table-green p-8">
      <h1 className="text-3xl font-bold text-white mb-8">Tile Gallery — 麻將牌面一覽</h1>

      <Section title="萬 (Characters)">
        {CHARACTERS.map((c) => <Tile key={c} code={c} />)}
      </Section>

      <Section title="筒 (Circles)">
        {CIRCLES.map((c) => <Tile key={c} code={c} />)}
      </Section>

      <Section title="索 (Bamboo)">
        {BAMBOO.map((c) => <Tile key={c} code={c} />)}
      </Section>

      <Section title="字牌 (Honors)">
        {HONORS.map((c) => <Tile key={c} code={c} />)}
      </Section>

      <Section title="花牌 (Flowers)">
        {FLOWERS.map((c) => <Tile key={c} code={c} />)}
      </Section>

      <h2 className="text-xl font-bold text-white mt-8 mb-4">Tile States</h2>
      <div className="flex gap-4 items-end">
        <div className="text-center">
          <Tile code="1m" />
          <p className="text-white text-xs mt-1">Normal</p>
        </div>
        <div className="text-center">
          <Tile code="1m" selected />
          <p className="text-white text-xs mt-1">Selected</p>
        </div>
        <div className="text-center">
          <Tile code="1m" highlighted />
          <p className="text-white text-xs mt-1">Highlighted</p>
        </div>
        <div className="text-center">
          <Tile code="1m" disabled />
          <p className="text-white text-xs mt-1">Disabled</p>
        </div>
        <div className="text-center">
          <Tile code="1m" faceUp={false} />
          <p className="text-white text-xs mt-1">Face Down</p>
        </div>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mb-6">
      <h2 className="text-xl font-bold text-white mb-2">{title}</h2>
      <div className="flex gap-1 flex-wrap">{children}</div>
    </div>
  )
}
