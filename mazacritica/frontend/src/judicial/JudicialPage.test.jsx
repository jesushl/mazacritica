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

describe('poder judicial', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    primeFeed()
  })

  afterEach(() => {
    cleanup()
  })

  it('renders postal zones from the API, including an empty list', async () => {
    const user = userEvent.setup()
    api.judicialDistrict
      .mockResolvedValueOnce({
        code: '99020',
        zones: [
          { id: 1, name: 'Zona ficticia norte', code: 'ZN-F01', valid_from: '2024-01-01', valid_to: '2027-12-31', source: 'Acuerdo norte' },
          { id: 2, name: 'Zona ficticia sur', code: 'ZN-F02', valid_from: '2025-01-01', valid_to: '2028-12-31', source: 'Acuerdo sur' },
        ],
        aspirantes: [
          {
            id: 4,
            name: 'Aspirante Judicial Ficticia',
            office: 'Magistratura ficticia',
            election: 'Elección ficticia 2027',
            zone: { code: 'ZN-F01', name: 'Zona ficticia norte' },
            status: 'confirmed',
            notes: [{ id: 7, title: 'Nota publicada de prueba', excerpt: 'Resumen publicado.', tags: ['Señalamiento'] }],
          },
        ],
        detail: '',
      })
      .mockResolvedValueOnce({
        code: '99000',
        zones: [],
        aspirantes: [],
        detail: 'No hay zonas oficiales registradas para este código postal.',
      })

    render(<App />)
    await screen.findByRole('heading', { name: 'Nota publicada de prueba' })
    expect(screen.queryByLabelText('Código postal')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Poder Judicial' }))
    await user.type(screen.getByLabelText('Código postal'), '99020')
    await user.click(screen.getByRole('button', { name: 'Buscar distrito' }))

    const list = await screen.findByRole('list', { name: 'Zonas del código postal' })
    expect(within(list).getByText(/Zona ficticia norte/)).toBeInTheDocument()
    expect(within(list).getByText(/Zona ficticia sur/)).toBeInTheDocument()
    expect(within(list).getAllByRole('listitem')).toHaveLength(2)
    expect(screen.getByRole('heading', { name: 'Aspirante Judicial Ficticia' })).toBeInTheDocument()
    expect(screen.getByText('Señalamiento')).toBeInTheDocument()

    await user.clear(screen.getByLabelText('Código postal'))
    await user.type(screen.getByLabelText('Código postal'), '99000')
    await user.click(screen.getByRole('button', { name: 'Buscar distrito' }))

    const emptyList = await screen.findByRole('list', { name: 'Zonas del código postal' })
    expect(within(emptyList).queryAllByRole('listitem')).toHaveLength(0)
    expect(screen.getByText('No hay zonas oficiales registradas para este código postal.')).toBeInTheDocument()
    expect(screen.queryByText('Zona inventada')).not.toBeInTheDocument()
  })
})
