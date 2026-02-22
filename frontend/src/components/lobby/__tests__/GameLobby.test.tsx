import { render, screen, fireEvent } from '@testing-library/react'
import GameLobby from '../GameLobby'

describe('GameLobby', () => {
  it('renders the title', () => {
    render(<GameLobby onStartGame={vi.fn()} connected={true} />)

    expect(screen.getByText('台灣16張麻將')).toBeInTheDocument()
  })

  it('easy mode button is enabled when connected=true', () => {
    render(<GameLobby onStartGame={vi.fn()} connected={true} />)

    const easyButton = screen.getByText(/簡單模式/)
    expect(easyButton).not.toBeDisabled()
  })

  it('easy mode button is disabled when connected=false', () => {
    render(<GameLobby onStartGame={vi.fn()} connected={false} />)

    const easyButton = screen.getByText(/簡單模式/)
    expect(easyButton).toBeDisabled()
  })

  it('clicking easy button calls onStartGame with "easy"', () => {
    const onStartGame = vi.fn()
    render(<GameLobby onStartGame={onStartGame} connected={true} />)

    fireEvent.click(screen.getByText(/簡單模式/))

    expect(onStartGame).toHaveBeenCalledTimes(1)
    expect(onStartGame).toHaveBeenCalledWith('easy')
  })

  it('clicking inspect button calls onStartGame with "inspect"', () => {
    const onStartGame = vi.fn()
    render(<GameLobby onStartGame={onStartGame} connected={true} />)

    fireEvent.click(screen.getByText(/觀戰模式/))

    expect(onStartGame).toHaveBeenCalledTimes(1)
    expect(onStartGame).toHaveBeenCalledWith('inspect')
  })

  it('shows connection message when not connected', () => {
    render(<GameLobby onStartGame={vi.fn()} connected={false} />)

    expect(screen.getByText(/Connecting to server/)).toBeInTheDocument()
  })
})
