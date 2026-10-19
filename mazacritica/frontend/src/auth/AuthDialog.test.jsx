import { cleanup, render, screen } from '@testing-library/react'
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

describe('acceso', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    primeFeed()
  })

  afterEach(() => {
    cleanup()
  })

  it('opens the comment dialog only when a visitor wants to comment', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByRole('heading', { name: 'Nota publicada de prueba' })
    expect(screen.queryByRole('button', { name: 'Ingresar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Nota publicada de prueba' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Comentar' }))
    expect(screen.getByRole('dialog', { name: 'Para comentar, ingresa' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Para comentar, ingresa' })).not.toBeInTheDocument()
  })

  it('registers a nickname account', async () => {
    const user = userEvent.setup()
    api.register.mockResolvedValue({ id: 4, email: 'ana@example.test', nickname: 'ana_01' })
    render(<App />)
    await screen.findByRole('heading', { name: 'Nota publicada de prueba' })
    await user.click(screen.getByRole('button', { name: 'Nota publicada de prueba' }))
    await user.click(await screen.findByRole('button', { name: 'Comentar' }))
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
    expect(screen.queryByRole('button', { name: 'Ingresar' })).not.toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
