import axios from 'axios'

export const TOKEN_KEY = 'mazacritica.token'

export function resolveApiBaseUrl(env = import.meta.env) {
  const configured = env?.VITE_API_BASE_URL
  if (configured && String(configured).trim()) {
    return String(configured).trim().replace(/\/$/, '')
  }
  return 'http://127.0.0.1:8000'
}

export function isEditor(account) {
  return Boolean(account?.groups?.includes('editor'))
}

function unwrapList(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}

export function createApi(env = import.meta.env, storage = window.localStorage) {
  const baseURL = resolveApiBaseUrl(env)
  const client = axios.create({ baseURL })

  client.interceptors.request.use((config) => {
    const token = storage.getItem(TOKEN_KEY)
    const headers = { ...(config.headers || {}) }
    if (token) headers.Authorization = `Token ${token}`
    return { ...config, headers }
  })

  return {
    baseURL,
    client,
    getToken() {
      return storage.getItem(TOKEN_KEY)
    },
    setToken(token) {
      if (token) storage.setItem(TOKEN_KEY, token)
      else storage.removeItem(TOKEN_KEY)
    },
    async register(payload) {
      const { data } = await client.post('/register/', payload)
      return data
    },
    async login(payload) {
      const { data } = await client.post('/login/', payload)
      if (data?.token) storage.setItem(TOKEN_KEY, data.token)
      return data
    },
    async logout() {
      try {
        await client.post('/logout/')
      } catch {
        // La sesión local se cierra aunque el servidor no responda.
      } finally {
        storage.removeItem(TOKEN_KEY)
      }
    },
    async me() {
      const { data } = await client.get('/me/')
      return data
    },
    async publishedNotes() {
      const { data } = await client.get('/notes/', { params: { status: 'published' } })
      return unwrapList(data)
    },
    async note(id) {
      const { data } = await client.get(`/notes/${id}/`)
      return data
    },
    async comments(noteId) {
      const { data } = await client.get(`/notes/${noteId}/comments/`)
      return unwrapList(data)
    },
    async source(id) {
      const { data } = await client.get(`/sources/${id}/`)
      return data
    },
    async sources() {
      const { data } = await client.get('/sources/')
      return unwrapList(data)
    },
    async tags() {
      const { data } = await client.get('/tags/')
      return unwrapList(data)
    },
    async postComment(noteId, { body, parent } = {}) {
      const payload = { body }
      if (parent) payload.parent = parent
      const { data } = await client.post(`/notes/${noteId}/comments/`, payload)
      return data
    },
    async createNote(payload) {
      const { data } = await client.post('/notes/', payload)
      return data
    },
    async searchPostalCode(code) {
      const { data } = await client.get('/postal-code-search/', { params: { code } })
      return data
    },
    async judicialDistrict(code) {
      const { data } = await client.get('/poder-judicial/distrito/', { params: { code } })
      return data
    },
  }
}

let sharedApi

function defaultApi() {
  if (!sharedApi) sharedApi = createApi()
  return sharedApi
}

export const api = new Proxy({}, {
  get(_target, property) {
    const instance = defaultApi()
    const value = instance[property]
    return typeof value === 'function' ? value.bind(instance) : value
  },
})
