import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { api, primeFeed, publishedNote } from '../test/fixtures'

vi.mock('../api', async () => {
  const fixtures = await import('../test/fixtures')
  return {
    api: fixtures.api,
    isEditor: (account) => Boolean(account?.groups?.includes('editor')),
  }
})

describe('portada', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    primeFeed()
  })

  afterEach(() => {
    cleanup()
  })

  it('shows published notes without creation controls or the postal field', async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Nota publicada de prueba' })).toBeInTheDocument()
    expect(api.publishedNotes).toHaveBeenCalled()
    expect(screen.queryByRole('button', { name: 'Nueva nota' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Publicar nota' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Editar nota' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Código postal')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Archivo' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Conversaciones' })).not.toBeInTheDocument()
    expect(screen.getByText('Fuente ficticia')).toBeInTheDocument()
    expect(screen.getAllByText('Señalamiento').length).toBeGreaterThan(0)

    await user.click(screen.getByRole('button', { name: 'Nota publicada de prueba' }))
    expect(api.comments).toHaveBeenCalledWith(7)
    expect(api.source).toHaveBeenCalledWith(3)
    expect(publishedNote.title).toBe('Nota publicada de prueba')
  })

  it('shows note creation only to an editor decided by /me/', async () => {
    api.getToken.mockReturnValue('token-editor')
    api.me.mockResolvedValue({
      id: 1,
      email: 'editor@example.test',
      nickname: 'editor_demo',
      groups: ['editor'],
    })
    render(<App />)
    expect(await screen.findByRole('button', { name: 'Nueva nota' })).toBeInTheDocument()
    expect(api.me).toHaveBeenCalled()
  })
})
