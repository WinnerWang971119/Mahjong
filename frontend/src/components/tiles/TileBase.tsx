import type { ReactNode } from 'react'

interface TileBaseProps {
  faceUp?: boolean
  selected?: boolean
  highlighted?: boolean
  disabled?: boolean
  onClick?: () => void
  children?: ReactNode
}

export default function TileBase({
  faceUp = true,
  selected = false,
  highlighted = false,
  disabled = false,
  onClick,
  children,
}: TileBaseProps) {
  const isInteractive = !!onClick && !disabled

  return (
    <div className={isInteractive ? 'tile-interactive inline-block' : 'inline-block'}>
      <svg
        width="48"
        height="64"
        viewBox="0 0 48 64"
        onClick={disabled ? undefined : onClick}
        className={[
          'transition-transform duration-150',
          selected ? '-translate-y-2' : '',
          disabled ? 'opacity-50 cursor-not-allowed' : '',
        ].join(' ')}
      >
        {/* Shadow */}
        <rect x="2" y="2" width="44" height="60" rx="4" fill="#00000020" />

        {faceUp ? (
          <>
            {/* Tile face */}
            <rect x="0" y="0" width="44" height="60" rx="4" fill="#f5f0e1" stroke="#d4c5a9" strokeWidth="1" />
            {/* Content */}
            <g transform="translate(22, 30)">{children}</g>
          </>
        ) : (
          <>
            {/* Tile back - dark green */}
            <rect x="0" y="0" width="44" height="60" rx="4" fill="#1a5c2a" stroke="#145220" strokeWidth="1" />
            <rect x="4" y="4" width="36" height="52" rx="2" fill="none" stroke="#2a7c3a" strokeWidth="0.5" />
          </>
        )}

        {/* Highlight border */}
        {highlighted && (
          <rect x="0" y="0" width="44" height="60" rx="4" fill="none" stroke="#fbbf24" strokeWidth="2">
            <animate attributeName="opacity" values="1;0.5;1" dur="1.5s" repeatCount="indefinite" />
          </rect>
        )}

        {/* Selected glow */}
        {selected && (
          <rect x="-1" y="-1" width="46" height="62" rx="5" fill="none" stroke="#3b82f6" strokeWidth="2" />
        )}
      </svg>
    </div>
  )
}
