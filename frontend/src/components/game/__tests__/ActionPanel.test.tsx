import { render, screen, fireEvent } from '@testing-library/react'
import ActionPanel from '../ActionPanel'
import type { ActionOption } from '../../../types/game'

describe('ActionPanel', () => {
  it('renders buttons for each unique action type', () => {
    const options: ActionOption[] = [
      { type: 'pong', tile: '1m', combo: null },
      { type: 'pass', tile: null, combo: null },
    ]
    const onAction = vi.fn()

    render(<ActionPanel options={options} onAction={onAction} />)

    expect(screen.getByText(/pong/i)).toBeInTheDocument()
    expect(screen.getByText(/pass/i)).toBeInTheDocument()
  })

  it('clicking a button calls onAction with correct type, tile, combo', () => {
    const options: ActionOption[] = [
      { type: 'pong', tile: '5p', combo: null },
      { type: 'pass', tile: null, combo: null },
    ]
    const onAction = vi.fn()

    render(<ActionPanel options={options} onAction={onAction} />)

    fireEvent.click(screen.getByText(/pong/i))

    expect(onAction).toHaveBeenCalledTimes(1)
    expect(onAction).toHaveBeenCalledWith('pong', '5p', undefined)
  })

  it('chi with single combo calls onAction directly', () => {
    const options: ActionOption[] = [
      { type: 'chi', tile: '3s', combo: ['1s', '2s', '3s'] },
      { type: 'pass', tile: null, combo: null },
    ]
    const onAction = vi.fn()

    render(<ActionPanel options={options} onAction={onAction} />)

    // With only one chi option, clicking the chi button should call onAction directly
    fireEvent.click(screen.getByText(/chi/i))

    expect(onAction).toHaveBeenCalledTimes(1)
    expect(onAction).toHaveBeenCalledWith('chi', '3s', ['1s', '2s', '3s'])
  })

  it('chi with multiple combos shows combo selection', () => {
    const options: ActionOption[] = [
      { type: 'chi', tile: '3s', combo: ['1s', '2s', '3s'] },
      { type: 'chi', tile: '3s', combo: ['2s', '3s', '4s'] },
      { type: 'pass', tile: null, combo: null },
    ]
    const onAction = vi.fn()

    render(<ActionPanel options={options} onAction={onAction} />)

    // Click chi button to show combo selection
    fireEvent.click(screen.getByText(/chi/i))

    // Should not have called onAction yet
    expect(onAction).not.toHaveBeenCalled()

    // Should now show combo selection UI with the combo tiles displayed
    expect(screen.getByText('1s 2s 3s')).toBeInTheDocument()
    expect(screen.getByText('2s 3s 4s')).toBeInTheDocument()

    // Click a specific combo
    fireEvent.click(screen.getByText('2s 3s 4s'))

    expect(onAction).toHaveBeenCalledTimes(1)
    expect(onAction).toHaveBeenCalledWith('chi', '3s', ['2s', '3s', '4s'])
  })

  it('pass button renders with correct label', () => {
    const options: ActionOption[] = [
      { type: 'pass', tile: null, combo: null },
    ]
    const onAction = vi.fn()

    render(<ActionPanel options={options} onAction={onAction} />)

    const passButton = screen.getByText(/pass/i)
    expect(passButton).toBeInTheDocument()

    fireEvent.click(passButton)
    expect(onAction).toHaveBeenCalledWith('pass', undefined, undefined)
  })
})
