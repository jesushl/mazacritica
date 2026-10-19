import axios from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TOKEN_KEY, createApi, resolveApiBaseUrl } from './api'

vi.mock('axios', () => ({
  default: {
    create: vi.fn(),
  },
}))

function memoryStorage(initial = {}) {
  const data = new Map(Object.entries(initial))
  return {
    getItem: (key) => (data.has(key) ? data.get(key) : null),
    setItem: (key, value) => data.set(key, String(value)),
    removeItem: (key) => data.delete(key),
  }
}

function mockClient() {
  const client = {
    interceptors: { request: { use: vi.fn() } },
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
  }
  axios.create.mockReturnValueOnce(client)
  return client
}

describe('resolveApiBaseUrl', () => {
  it('uses VITE_API_BASE_URL and falls back to the local API', () => {
    expect(resolveApiBaseUrl({ VITE_API_BASE_URL: 'https://api.example.test/' }))
      .toBe('https://api.example.test')
    expect(resolveApiBaseUrl({})).toBe('http://127.0.0.1:8000')
    expect(resolveApiBaseUrl({ VITE_API_BASE_URL: '  ' })).toBe('http://127.0.0.1:8000')
  })
})

describe('createApi', () => {
  beforeEach(() => {
    axios.create.mockReset()
  })

  it('creates the client with the configured base URL', () => {
    mockClient()
    const api = createApi({ VITE_API_BASE_URL: 'https://api.example.test' }, memoryStorage())
    expect(api.baseURL).toBe('https://api.example.test')
    expect(axios.create).toHaveBeenCalledWith({ baseURL: 'https://api.example.test' })
  })

  it('stores the login token and sends it on the next request', async () => {
    const storage = memoryStorage()
    const client = mockClient()
    client.post.mockResolvedValueOnce({
      data: {
        token: 'token-demo',
        nickname: 'miembro_uno',
        email: 'miembro@example.test',
        groups: ['member'],
      },
    })
    const api = createApi({}, storage)

    await api.login({ email: 'miembro@example.test', password: 'password-segura' })

    expect(storage.getItem(TOKEN_KEY)).toBe('token-demo')
    const authorize = client.interceptors.request.use.mock.calls[0][0]
    const config = authorize({ headers: {}, url: '/me/' })
    expect(config.headers.Authorization).toBe('Token token-demo')
  })

  it('clears the token on logout even if the request fails', async () => {
    const storage = memoryStorage({ [TOKEN_KEY]: 'token-demo' })
    const client = mockClient()
    client.post.mockRejectedValueOnce(new Error('red'))
    const api = createApi({}, storage)

    await expect(api.logout()).resolves.toBeUndefined()
    expect(storage.getItem(TOKEN_KEY)).toBeNull()
    const authorize = client.interceptors.request.use.mock.calls[0][0]
    const config = authorize({ headers: {}, url: '/notes/' })
    expect(config.headers.Authorization).toBeUndefined()
  })

  it('requests published notes, account, comments and postal zones', async () => {
    const client = mockClient()
    client.get.mockImplementation((url) => {
      if (url === '/notes/') return Promise.resolve({ data: [{ id: 1, status: 'published' }] })
      if (url === '/me/') return Promise.resolve({ data: { id: 2, groups: ['member'], nickname: 'miembro_uno' } })
      if (url === '/notes/4/comments/') {
        return Promise.resolve({ data: [{ id: 9, nickname: 'desde_api', body: 'Visible', replies: [] }] })
      }
      if (url === '/postal-code-search/') return Promise.resolve({ data: { code: '99020', zones: [] } })
      if (url === '/poder-judicial/distrito/') return Promise.resolve({ data: { code: '99020', zones: [], aspirantes: [] } })
      return Promise.resolve({ data: {} })
    })
    const api = createApi({}, memoryStorage())

    await api.publishedNotes()
    await api.me()
    await api.comments(4)
    await api.postComment(4, { body: 'Hola', nickname: 'falso' })
    await api.searchPostalCode('99020')
    await api.judicialDistrict('99020')

    expect(client.get).toHaveBeenCalledWith('/notes/', { params: { status: 'published' } })
    expect(client.get).toHaveBeenCalledWith('/me/')
    expect(client.get).toHaveBeenCalledWith('/notes/4/comments/')
    expect(client.post).toHaveBeenCalledWith('/notes/4/comments/', { body: 'Hola' })
    expect(client.get).toHaveBeenCalledWith('/postal-code-search/', { params: { code: '99020' } })
    expect(client.get).toHaveBeenCalledWith('/poder-judicial/distrito/', { params: { code: '99020' } })
  })

  it('calls register and login endpoints', async () => {
    const client = mockClient()
    client.post.mockImplementation((url) => {
      if (url === '/register/') return Promise.resolve({ data: { id: 1, nickname: 'ana_01' } })
      return Promise.resolve({ data: { token: 't', groups: ['member'] } })
    })
    const api = createApi({}, memoryStorage())

    await api.register({
      email: 'ana@example.test',
      password: 'password-segura',
      nickname: 'ana_01',
    })
    await api.login({ username: 'ana_01', password: 'password-segura' })

    expect(client.post).toHaveBeenCalledWith('/register/', {
      email: 'ana@example.test',
      password: 'password-segura',
      nickname: 'ana_01',
    })
    expect(client.post).toHaveBeenCalledWith('/login/', {
      username: 'ana_01',
      password: 'password-segura',
    })
  })
})
