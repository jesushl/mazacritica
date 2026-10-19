import { vi } from 'vitest'

export const api = {
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
  judicialDistrict: vi.fn(),
}

export const publishedNote = {
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

export const visibleThread = {
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

export const memberProfile = {
  id: 2,
  email: 'miembro@example.test',
  nickname: 'miembro_uno',
  groups: ['member'],
}

export function primeFeed() {
  api.getToken.mockReturnValue(null)
  api.publishedNotes.mockResolvedValue([publishedNote])
  api.tags.mockResolvedValue([{ id: 1, name: 'Señalamiento', slug: 'senalamiento' }])
  api.sources.mockResolvedValue([{ id: 3, name: 'Fuente ficticia', url: 'https://example.test/fuente' }])
  api.note.mockResolvedValue(publishedNote)
  api.comments.mockResolvedValue([visibleThread])
  api.source.mockResolvedValue({ id: 3, name: 'Fuente ficticia', url: 'https://example.test/fuente' })
  api.logout.mockResolvedValue(undefined)
}

export function primeVisitor() {
  api.getToken.mockReturnValue(null)
  api.publishedNotes.mockResolvedValue([publishedNote])
  api.tags.mockResolvedValue([{ id: 1, name: 'Señalamiento', slug: 'senalamiento' }])
  api.sources.mockResolvedValue([{ id: 3, name: 'Fuente ficticia', url: 'https://example.test/fuente' }])
  api.note.mockResolvedValue(publishedNote)
  api.comments.mockResolvedValue([])
  api.source.mockResolvedValue({ id: 3, name: 'Fuente ficticia', url: 'https://example.test/fuente' })
  api.me.mockResolvedValue(memberProfile)
  api.judicialDistrict.mockResolvedValue({
    code: '99000',
    zones: [],
    aspirantes: [],
    detail: 'No hay zonas oficiales registradas para este código postal.',
  })
  api.searchPostalCode.mockResolvedValue({
    code: '99000',
    zones: [],
    detail: 'No hay zonas oficiales registradas para este código postal.',
  })
}
