import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const api = vi.hoisted(() => ({
  getToken: vi.fn(() => null),
  setToken: vi.fn(),
  publishedNotes: vi.fn(),
  sources: vi.fn(),
  tags: vi.fn(),
  note: vi.fn(),
  comments: vi.fn(),
  source: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  me: vi.fn(),
  postComment: vi.fn(),
  createNote: vi.fn(),
  searchPostalCode: vi.fn(),
}))

vi.mock('./api', () => ({
  api,
  isEditor: (account) => Boolean(account?.groups?.includes('editor')),
}))

const publishedNote = {
  id: 7,
  title: 'Nota publicada de prueba',
  excerpt: 'Resumen publicado.',
  content: 'Cuerpo documentado.',
  status: 'published',
  source: 3,
  tags: [1],
  author: 'editor_demo',
  published_at: '2026-03-01T12:00:00Z',
}

const visibleThread = {
  id: 10,
  nickname: 'miembro_uno',
  body: 'Comentario visible',
  parent: null,
  status: 'visible',
  replies: [
    {
      id: 11,
      nickname: 'editor_demo',
      body: 'Respuesta visible',
      parent: 10,
      status: 'visible',
      replies: [],
    },
  ],
}

function primeFeed() {
  api.getToken.mockReturnValue(null)
  api.publishedNotes.mockResolvedValue([publishedNote])
  api.tags.mockResolvedValue([{ id: 1, name: 'Señalamiento', slug: 'senalamiento' }])
  api.sources.mockResolvedValue([{ id: 3, name: 'Fuente ficticia', url: 'https://example.test/fuente' }])
  api.note.mockResolvedValue(publishedNote)
  api.comments.mockResolvedValue([visibleThread])
  api.source.mockResolvedValue({ id: 3, name: 'Fuente ficticia', url: 'https://example.test/fuente' })
  api.logout.mockResolvedValue(undefined)
}

describe('experiencia conectada', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    primeFeed()
  })

  afterEach(() => {
    cleanup()
  })

  it('shows published notes and visible comments without creation controls', async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Nota publicada de prueba' })).toBeInTheDocument()
    expect(api.publishedNotes).toHaveBeenCalled()
    expect(screen.queryByRole('button', { name: 'Nueva nota' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Publicar nota' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Editar nota' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Nota publicada de prueba' }))

    expect(await screen.findByText('Comentario visible')).toBeInTheDocument()
    expect(screen.getByText('Respuesta visible')).toBeInTheDocument()
    expect(screen.getByText('miembro_uno')).toBeInTheDocument()
    expect(screen.queryByText('Comentario pendiente')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Comentario')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Publicar comentario' })).not.toBeInTheDocument()
    expect(api.comments).toHaveBeenCalledWith(7)
    expect(api.source).toHaveBeenCalledWith(3)
    expect(screen.getByText('Fuente ficticia')).toBeInTheDocument()
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
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))
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
    expect(screen.queryByRole('button', { name: 'Publicar nota' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Editar nota' })).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Nota publicada de prueba' }))
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

  it('registers a nickname account', async () => {
    const user = userEvent.setup()
    api.register.mockResolvedValue({ id: 4, email: 'ana@example.test', nickname: 'ana_01' })
    render(<App />)
    await screen.findByRole('heading', { name: 'Nota publicada de prueba' })
    await user.click(screen.getByRole('button', { name: 'Ingresar' }))
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))
    await user.type(screen.getByLabelText('Nickname'), 'Ana_01')
    await user.type(screen.getByLabelText('Correo'), 'ana@example.test')
    await user.type(screen.getByLabelText('Contraseña'), 'password-segura')
    await user.click(screen.getByRole('button', { name: 'Registrarme' }))

    expect(api.register).toHaveBeenCalledWith({
      email: 'ana@example.test',
      password: 'password-segura',
      nickname: 'Ana_01',
    })
  })

  it('renders postal zones from the API, including an empty list', async () => {
    const user = userEvent.setup()
    api.searchPostalCode
      .mockResolvedValueOnce({
        code: '99020',
        zones: [
          { id: 1, name: 'Zona ficticia norte', code: 'ZN-F01', valid_from: '2024-01-01', valid_to: '2027-12-31', source: 'Acuerdo norte' },
          { id: 2, name: 'Zona ficticia sur', code: 'ZN-F02', valid_from: '2025-01-01', valid_to: '2028-12-31', source: 'Acuerdo sur' },
        ],
      })
      .mockResolvedValueOnce({
        code: '99000',
        zones: [],
        detail: 'No hay zonas oficiales registradas para este código postal.',
      })

    render(<App />)
    await screen.findByRole('heading', { name: 'Nota publicada de prueba' })
    await user.type(screen.getByLabelText('Código postal'), '99020')
    await user.click(screen.getByRole('button', { name: 'Buscar zona' }))

    const list = await screen.findByRole('list', { name: 'Zonas del código postal' })
    expect(within(list).getByText(/Zona ficticia norte/)).toBeInTheDocument()
    expect(within(list).getByText(/Zona ficticia sur/)).toBeInTheDocument()
    expect(within(list).getAllByRole('listitem')).toHaveLength(2)

    await user.clear(screen.getByLabelText('Código postal'))
    await user.type(screen.getByLabelText('Código postal'), '99000')
    await user.click(screen.getByRole('button', { name: 'Buscar zona' }))

    const emptyList = await screen.findByRole('list', { name: 'Zonas del código postal' })
    expect(within(emptyList).queryAllByRole('listitem')).toHaveLength(0)
    expect(screen.getByText('No hay zonas oficiales registradas para este código postal.')).toBeInTheDocument()
    expect(screen.queryByText('Zona inventada')).not.toBeInTheDocument()
  })

  it('logs out through the API client', async () => {
    const user = userEvent.setup()
    api.getToken.mockReturnValue('token-miembro')
    api.me.mockResolvedValue({
      id: 2,
      email: 'miembro@example.test',
      nickname: 'miembro_uno',
      groups: ['member'],
    })
    render(<App />)
    await user.click(await screen.findByRole('button', { name: 'Salir' }))
    expect(api.logout).toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Ingresar' })).toBeInTheDocument()
  })
})
