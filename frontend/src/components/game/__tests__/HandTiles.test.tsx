import { render, screen, fireEvent } from '@testing-library/react'
import HandTiles from '../HandTiles'

vi.mock('../../tiles/Tile', () => ({
  default: (props: any) => (
    <div
      data-testid="tile"
      data-code={props.code}
      data-selected={props.selected}
      data-faceup={props.faceUp}
      onClick={props.onClick}
    />
  ),
}))

describe('HandTiles', () => {
  it('renders face-up tiles for self player with tiles array', () => {
    render(
      <HandTiles
        tiles={['1m', '2m', '3m']}
        tileCount={3}
        isSelf={true}
        selectedTileIndex={null}
      />,
    )

    const tiles = screen.getAllByTestId('tile')
    expect(tiles).toHaveLength(3)
    expect(tiles[0]).toHaveAttribute('data-code', '1m')
    expect(tiles[1]).toHaveAttribute('data-code', '2m')
    expect(tiles[2]).toHaveAttribute('data-code', '3m')
    // All face-up
    tiles.forEach((tile) => {
      expect(tile).toHaveAttribute('data-faceup', 'true')
    })
  })

  it('renders face-down tiles for opponent (isSelf=false)', () => {
    render(
      <HandTiles
        tiles={null}
        tileCount={16}
        isSelf={false}
        selectedTileIndex={null}
      />,
    )

    const tiles = screen.getAllByTestId('tile')
    expect(tiles).toHaveLength(16)
    tiles.forEach((tile) => {
      expect(tile).toHaveAttribute('data-code', '')
      expect(tile).toHaveAttribute('data-faceup', 'false')
    })
  })

  it('only marks the tile at selectedTileIndex as selected', () => {
    render(
      <HandTiles
        tiles={['1m', '2m', '3m', '4m']}
        tileCount={4}
        isSelf={true}
        selectedTileIndex={2}
      />,
    )

    const tiles = screen.getAllByTestId('tile')
    expect(tiles[0]).toHaveAttribute('data-selected', 'false')
    expect(tiles[1]).toHaveAttribute('data-selected', 'false')
    expect(tiles[2]).toHaveAttribute('data-selected', 'true')
    expect(tiles[3]).toHaveAttribute('data-selected', 'false')
  })

  it('with duplicate tiles, selecting index 0 only selects the first instance', () => {
    render(
      <HandTiles
        tiles={['1m', '1m', '2m']}
        tileCount={3}
        isSelf={true}
        selectedTileIndex={0}
      />,
    )

    const tiles = screen.getAllByTestId('tile')
    // Both tiles have code "1m" but only index 0 should be selected
    expect(tiles[0]).toHaveAttribute('data-code', '1m')
    expect(tiles[0]).toHaveAttribute('data-selected', 'true')
    expect(tiles[1]).toHaveAttribute('data-code', '1m')
    expect(tiles[1]).toHaveAttribute('data-selected', 'false')
    expect(tiles[2]).toHaveAttribute('data-code', '2m')
    expect(tiles[2]).toHaveAttribute('data-selected', 'false')
  })

  it('clicking a tile calls onTileClick with the index', () => {
    const onTileClick = vi.fn()
    render(
      <HandTiles
        tiles={['1m', '2m', '3m']}
        tileCount={3}
        isSelf={true}
        selectedTileIndex={null}
        onTileClick={onTileClick}
      />,
    )

    const tiles = screen.getAllByTestId('tile')
    fireEvent.click(tiles[1])

    expect(onTileClick).toHaveBeenCalledTimes(1)
    expect(onTileClick).toHaveBeenCalledWith(1)
  })

  it('renders face-down tiles when tiles is null and isSelf is true', () => {
    render(
      <HandTiles
        tiles={null}
        tileCount={16}
        isSelf={true}
        selectedTileIndex={null}
      />,
    )

    const tiles = screen.getAllByTestId('tile')
    expect(tiles).toHaveLength(16)
    tiles.forEach((tile) => {
      expect(tile).toHaveAttribute('data-code', '')
      expect(tile).toHaveAttribute('data-faceup', 'false')
    })
  })
})
