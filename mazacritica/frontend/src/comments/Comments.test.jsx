import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { api, primeFeed } from '../test/fixtures'

vi.mock('../api', async () => {
  const fixtures = await import('../test/fixtures')
  return {
    api: fixtures.api,
    isEditor: (account) => Boolean(account?.groups?.includes('editor')),
  }
})

describe('comentarios', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    primeFeed()
  })

  afterEach(() => {
    cleanup()
  })

  it('shows the visible thread and hides pending comments from visitors', async () => {
    const user = userEvent.setup()
    render(<App />)
    await user.click(await screen.findByRole('button', { name: 'Nota publicada de prueba' }))
    expect(await screen.findByText('Comentario visible')).toBeInTheDocument()
    expect(screen.getByText('Respuesta visible')).toBeInTheDocument()
    expect(screen.getByText('miembro_uno')).toBeInTheDocument()
    expect(screen.queryByText('Comentario pendiente')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Comentario')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Publicar comentario' })).not.toBeInTheDocument()
  })

  it('lets a member comment and reply once, without publishing notes', async () => {
    const user = userEvent.setup()
    api.login.mockResolvedValue({
      token: 'token-miembro',
      nickname: 'miembro_uno',
      email: 'miembro@example.test',
      groups: ['member'],
    })
    api.me.mockResolvedValue({
      id: 2,
      email: 'miembro@example.test',
      nickname: 'miembro_uno',
      groups: ['member'],
    })
    api.postComment
      .mockResolvedValueOnce({
        id: 20,
        nickname: 'desde_api',
        body: 'Un hecho',
        parent: null,
        status: 'pending',
        replies: [],
      })
      .mockResolvedValueOnce({
        id: 21,
        nickname: 'desde_api',
        body: 'Una respuesta',
        parent: 10,
        status: 'pending',
        replies: [],
      })

    render(<App />)
    await screen.findByRole('heading', { name: 'Nota publicada de prueba' })
    await user.click(screen.getByRole('button', { name: 'Nota publicada de prueba' }))
    await user.click(await screen.findByRole('button', { name: 'Comentar' }))
    await user.type(screen.getByLabelText('Correo'), 'miembro@example.test')
    await user.type(screen.getByLabelText('Contraseña'), 'password-segura')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(api.login).toHaveBeenCalledWith({
      email: 'miembro@example.test',
      password: 'password-segura',
    })
    expect(api.me).toHaveBeenCalled()
    expect(await screen.findByRole('button', { name: 'Salir' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Nueva nota' })).not.toBeInTheDocument()

    expect(await screen.findByLabelText('Comentario')).toBeInTheDocument()
    expect(screen.queryByLabelText(/nickname/i)).not.toBeInTheDocument()
    await user.type(screen.getByLabelText('Comentario'), 'Un hecho')
    await user.click(screen.getByRole('button', { name: 'Publicar comentario' }))

    expect(api.postComment).toHaveBeenCalledWith(7, { body: 'Un hecho' })
    expect(await screen.findByText('desde_api')).toBeInTheDocument()

    const visibleComment = screen.getByText('Comentario visible').closest('article')
    const nestedReply = screen.getByText('Respuesta visible').closest('article')
    expect(within(nestedReply).queryByRole('button', { name: 'Responder' })).not.toBeInTheDocument()
    await user.click(within(visibleComment).getByRole('button', { name: 'Responder' }))
    await user.type(screen.getByLabelText('Respuesta directa'), 'Una respuesta')
    await user.click(screen.getByRole('button', { name: 'Publicar respuesta' }))

    expect(api.postComment).toHaveBeenLastCalledWith(7, { body: 'Una respuesta', parent: 10 })
    const postedReply = screen.getByText('Una respuesta').closest('article')
    expect(within(postedReply).queryByRole('button', { name: 'Responder' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Respuesta directa')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Salir' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Comentar' })).toBeInTheDocument()
    expect(screen.queryByText('Un hecho')).not.toBeInTheDocument()
    expect(screen.queryByText('Una respuesta')).not.toBeInTheDocument()
    expect(screen.getByText('Comentario visible')).toBeInTheDocument()
  })
})
