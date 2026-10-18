import { act, cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const here = dirname(fileURLToPath(import.meta.url))
const appCss = readFileSync(resolve(here, 'App.css'), 'utf8')
const indexCss = readFileSync(resolve(here, 'index.css'), 'utf8')

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

function mediaBlock(css, width) {
  const marker = `@media (max-width: ${width}px)`
  const start = css.indexOf(marker)
  expect(start, marker).toBeGreaterThan(-1)
  const open = css.indexOf('{', start)
  let depth = 0
  for (let index = open; index < css.length; index += 1) {
    if (css[index] === '{') depth += 1
    if (css[index] === '}') {
      depth -= 1
      if (depth === 0) return css.slice(start, index + 1)
    }
  }
  throw new Error(`Bloque ${marker} sin cerrar`)
}

function hides(block, selector) {
  const pattern = new RegExp(`${selector.replace('.', '\\.')}\\s*\\{[^}]*display:\\s*none`)
  return pattern.test(block)
}

describe('contrato responsive', () => {
  const narrow = mediaBlock(appCss, 760)
  const tablet = mediaBlock(appCss, 1120)

  it('keeps navigation, login and the postal rail reachable', () => {
    expect(hides(narrow, '.sidebar')).toBe(false)
    expect(hides(narrow, '.login-button')).toBe(false)
    expect(hides(narrow, '.right-rail')).toBe(false)
    expect(hides(tablet, '.right-rail')).toBe(false)
    expect(hides(narrow, '.note-source')).toBe(false)
    expect(hides(narrow, '.note-tag')).toBe(false)
    expect(hides(tablet, '.note-source')).toBe(false)
    expect(narrow).toMatch(/grid-template-columns:\s*minmax\(0,\s*1fr\)/)
    expect(tablet).toMatch(/grid-area:\s*rail/)
  })

  it('uses 44px targets and readable chip text without the Vite root padding', () => {
    expect(appCss).not.toMatch(/#root\s*\{[^}]*max-width:\s*1280px/)
    expect(appCss).not.toMatch(/#root\s*\{[^}]*padding:\s*2rem/)
    expect(appCss).toMatch(/\.filter-chip[\s\S]*font-size:\s*12px/)
    expect(appCss).toMatch(/\.note-tag[\s\S]*font-size:\s*12px/)
    for (const selector of [
      '.filter-chip',
      '.note-actions button',
      '.variant-tab',
      '.comment-actions button',
      '.search-box',
      '.auth-panel button',
      '.postal-search button',
      '.comment-composer button',
      '.note-composer button',
    ]) {
      expect(appCss, selector).toMatch(
        new RegExp(`${selector.replace('.', '\\.')}[\\s\\S]{0,220}min-height:\\s*44px`),
      )
    }
  })

  it('keeps a visible focus style and hides the collapsed header from the tab order', () => {
    const styles = `${indexCss}\n${appCss}`
    expect(appCss).not.toMatch(/\.search-box input\s*\{[^}]*outline:\s*0/)
    expect(styles).toMatch(/button:focus-visible/)
    expect(styles).toMatch(/a:focus-visible/)
    expect(styles).toMatch(/input:focus-visible/)
    expect(styles).toMatch(/textarea:focus-visible/)
    expect(styles).toMatch(/summary:focus-visible/)
    expect(appCss).toMatch(/\.search-box input:focus-visible/)
    expect(appCss).toMatch(/\.topbar\.is-hidden\s*\{[^}]*visibility:\s*hidden/)
  })
})

describe('experiencia accesible', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.getToken.mockReturnValue(null)
    api.publishedNotes.mockResolvedValue([publishedNote])
    api.tags.mockResolvedValue([{ id: 1, name: 'Señalamiento', slug: 'senalamiento' }])
    api.sources.mockResolvedValue([{ id: 3, name: 'Fuente ficticia', url: 'https://example.test/fuente' }])
    api.note.mockResolvedValue(publishedNote)
    api.comments.mockResolvedValue([])
    api.source.mockResolvedValue({ id: 3, name: 'Fuente ficticia', url: 'https://example.test/fuente' })
    api.me.mockResolvedValue({
      id: 2,
      email: 'miembro@example.test',
      nickname: 'miembro_uno',
      groups: ['member'],
    })
    api.searchPostalCode.mockResolvedValue({
      code: '99000',
      zones: [],
      detail: 'No hay zonas oficiales registradas para este código postal.',
    })
  })

  afterEach(() => {
    cleanup()
  })

  it('exposes landmarks, headings, selection and named fields', async () => {
    render(<App />)
    expect(await screen.findByRole('heading', { name: 'Nota publicada de prueba' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Navegación principal' })).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByRole('complementary', { name: 'Navegación' })).toBeInTheDocument()
    expect(screen.getByRole('complementary', { name: 'Contexto editorial' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Código postal' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Nuestra regla' })).toBeInTheDocument()

    const levels = screen.getAllByRole('heading').map((heading) => Number(heading.tagName.slice(1)))
    expect(levels[0]).toBe(1)
    levels.forEach((level, index) => {
      if (index > 0) expect(level).toBeLessThanOrEqual(levels[index - 1] + 1)
    })

    expect(screen.getByRole('tab', { name: 'Para ti' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('button', { name: 'Señalamiento' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('searchbox', { name: 'Buscar notas, temas o fuentes' })).toBeInTheDocument()
    expect(screen.getByLabelText('Código postal')).toBeInTheDocument()
    expect(screen.getByText('Fuente ficticia')).toBeInTheDocument()
    expect(screen.getAllByText('Señalamiento').length).toBeGreaterThan(0)
    expect(document.querySelector('.feed')).not.toHaveAttribute('aria-live')
    expect(screen.getAllByRole('status')).toHaveLength(1)

    for (const name of ['Inicio', 'Explorar', 'Archivo', 'Conversaciones', 'Ingresar']) {
      expect(screen.getByRole('button', { name })).toBeInTheDocument()
    }
    const accordion = screen.getByRole('navigation', { name: 'Navegación principal' }).closest('details')
    expect(accordion).toHaveAttribute('open')
  })

  it('announces notices from the single status region and keeps an empty zone list', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByRole('heading', { name: 'Nota publicada de prueba' })
    await user.click(screen.getByRole('button', { name: 'Explorar' }))
    expect(screen.getByRole('status')).toHaveTextContent('La exploración estará disponible pronto.')

    await user.type(screen.getByLabelText('Código postal'), '99000')
    await user.click(screen.getByRole('button', { name: 'Buscar zona' }))
    const zones = await screen.findByRole('list', { name: 'Zonas del código postal' })
    expect(within(zones).queryAllByRole('listitem')).toHaveLength(0)
    expect(screen.getByText('No hay zonas oficiales registradas para este código postal.')).toBeInTheDocument()
    expect(screen.queryByText('Zona inventada')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Nueva nota' })).not.toBeInTheDocument()
  })

  it('lets a keyboard user open a note, return, and reach the comment box', async () => {
    const user = userEvent.setup()
    api.getToken.mockReturnValue('token-miembro')
    render(<App />)
    const open = await screen.findByRole('button', { name: 'Nota publicada de prueba' })
    open.focus()
    await user.keyboard('{Enter}')
    const back = await screen.findByRole('button', { name: /Volver al feed/ })
    expect(screen.getByRole('tab', { name: 'Facebook' })).toHaveAttribute('aria-selected', 'true')
    const comment = screen.getByRole('textbox', { name: 'Comentario' })
    comment.focus()
    await user.keyboard('Hecho')
    expect(comment).toHaveValue('Hecho')
    expect(screen.queryByRole('button', { name: 'Responder' })).not.toBeInTheDocument()
    back.focus()
    await user.keyboard('{Enter}')
    expect(screen.getByRole('button', { name: 'Nota publicada de prueba' })).toBeInTheDocument()
  })

  it('drops the hidden header from the tab order', async () => {
    render(<App />)
    await screen.findByRole('heading', { name: 'Nota publicada de prueba' })
    await act(async () => {
      Object.defineProperty(window, 'scrollY', { configurable: true, value: 160 })
      window.dispatchEvent(new Event('scroll'))
    })
    const header = document.querySelector('.topbar')
    expect(header.className).toContain('is-hidden')
    expect(header).toHaveAttribute('inert')
  })

  it('reports a load error in the status region', async () => {
    api.publishedNotes.mockRejectedValueOnce(new Error('red'))
    render(<App />)
    expect(await screen.findByRole('status')).toHaveTextContent('No pudimos cargar las notas publicadas.')
  })
})
