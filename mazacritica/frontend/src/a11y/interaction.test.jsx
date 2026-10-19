import { act, cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { api, primeVisitor } from '../test/fixtures'

vi.mock('../api', async () => {
  const fixtures = await import('../test/fixtures')
  return {
    api: fixtures.api,
    isEditor: (account) => Boolean(account?.groups?.includes('editor')),
  }
})

describe('experiencia accesible', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    primeVisitor()
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
    expect(screen.queryByRole('heading', { name: 'Código postal' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Código postal')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Nuestra regla' })).toBeInTheDocument()

    const levels = screen.getAllByRole('heading').map((heading) => Number(heading.tagName.slice(1)))
    expect(levels[0]).toBe(1)
    levels.forEach((level, index) => {
      if (index > 0) expect(level).toBeLessThanOrEqual(levels[index - 1] + 1)
    })

    expect(screen.getByRole('tab', { name: 'Para ti' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('button', { name: 'Señalamiento' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('searchbox', { name: 'Buscar notas, temas o fuentes' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Archivo' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Conversaciones' })).not.toBeInTheDocument()
    expect(screen.getByText('Fuente ficticia')).toBeInTheDocument()
    expect(screen.getAllByText('Señalamiento').length).toBeGreaterThan(0)
    expect(document.querySelector('.feed')).not.toHaveAttribute('aria-live')
    expect(screen.getAllByRole('status')).toHaveLength(1)

    for (const name of ['Inicio', 'Explorar', 'Poder Judicial']) {
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

    await user.click(screen.getByRole('button', { name: 'Poder Judicial' }))
    expect(screen.getByRole('heading', { name: 'Aspirantes del distrito' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Nota publicada de prueba' })).not.toBeInTheDocument()
    await user.type(screen.getByLabelText('Código postal'), '99000')
    await user.click(screen.getByRole('button', { name: 'Buscar distrito' }))
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