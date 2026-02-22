import { render, screen, fireEvent } from '@testing-library/react'
import ScoringScreen from '../ScoringScreen'
import type { ScoringBreakdown } from '../../../types/game'

vi.mock('../../tiles/Tile', () => ({
  default: (props: any) => (
    <div data-testid="tile" data-code={props.code} />
  ),
}))

const mockScoring: ScoringBreakdown = {
  yaku: [
    ['門前清', 1],
    ['自摸', 1],
    ['平胡', 2],
  ],
  subtotal: 4,
  total: 4,
  payments: {
    0: -12,
    1: 4,
    2: 4,
    3: 4,
  },
}

describe('ScoringScreen', () => {
  it('shows scoring data when scoring is not null', () => {
    render(
      <ScoringScreen scoring={mockScoring} onContinue={vi.fn()} />,
    )

    // Yaku names visible
    expect(screen.getByText('門前清')).toBeInTheDocument()
    expect(screen.getByText('自摸')).toBeInTheDocument()
    expect(screen.getByText('平胡')).toBeInTheDocument()

    // Tai values visible
    const taiCells = screen.getAllByText('1')
    expect(taiCells.length).toBeGreaterThanOrEqual(2) // two yaku with value 1
    expect(screen.getByText('2')).toBeInTheDocument()

    // Total is shown
    expect(screen.getByText(/4 台/)).toBeInTheDocument()
  })

  it('shows draw message when scoring is null', () => {
    render(
      <ScoringScreen scoring={null} onContinue={vi.fn()} />,
    )

    // The component renders the Unicode-escaped string for "流局 — 無人胡牌"
    expect(screen.getByText(/流局/)).toBeInTheDocument()
  })

  it('clicking continue button calls onContinue', () => {
    const onContinue = vi.fn()
    render(
      <ScoringScreen scoring={null} onContinue={onContinue} />,
    )

    fireEvent.click(screen.getByText(/Continue/))

    expect(onContinue).toHaveBeenCalledTimes(1)
  })

  it('displays winning hand tiles when provided', () => {
    const winningHand = ['1m', '2m', '3m', '4p', '5p', '6p']
    render(
      <ScoringScreen
        scoring={mockScoring}
        winningHand={winningHand}
        onContinue={vi.fn()}
      />,
    )

    const tiles = screen.getAllByTestId('tile')
    expect(tiles).toHaveLength(winningHand.length)
    expect(tiles[0]).toHaveAttribute('data-code', '1m')
    expect(tiles[5]).toHaveAttribute('data-code', '6p')
  })
})
