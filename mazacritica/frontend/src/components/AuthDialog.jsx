import { useEffect, useRef } from 'react'
import './AuthDialog.css'

/* eslint-disable react/prop-types -- el cuadro solo se abre desde App */
export default function AuthDialog({
  mode,
  credentials,
  onCredentials,
  onMode,
  onLogin,
  onRegister,
  onClose,
}) {
  const dialogRef = useRef(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return undefined
    if (!dialog.open) {
      try {
        dialog.showModal()
      } catch {
        dialog.setAttribute('open', '')
      }
    }
    return () => {
      if (dialog.open) dialog.close()
    }
  }, [])

  return (
    <dialog
      ref={dialogRef}
      className="auth-dialog"
      aria-labelledby="auth-title"
      onClose={onClose}
    >
      <p id="auth-title">Para comentar, ingresa</p>
      <button className="auth-close" type="button" onClick={onClose}>Cerrar</button>
      {mode === 'login' ? (
        <form onSubmit={onLogin}>
          <label>
            Correo
            <input value={credentials.email} onChange={(event) => onCredentials({ ...credentials, email: event.target.value })} />
          </label>
          <label>
            Contraseña
            <input type="password" value={credentials.password} onChange={(event) => onCredentials({ ...credentials, password: event.target.value })} />
          </label>
          <button type="submit">Entrar</button>
          <button type="button" onClick={() => onMode('register')}>Crear cuenta</button>
        </form>
      ) : (
        <form onSubmit={onRegister}>
          <label>
            Nickname
            <input value={credentials.nickname} onChange={(event) => onCredentials({ ...credentials, nickname: event.target.value })} />
          </label>
          <label>
            Correo
            <input value={credentials.email} onChange={(event) => onCredentials({ ...credentials, email: event.target.value })} />
          </label>
          <label>
            Contraseña
            <input type="password" value={credentials.password} onChange={(event) => onCredentials({ ...credentials, password: event.target.value })} />
          </label>
          <button type="submit">Registrarme</button>
          <button type="button" onClick={() => onMode('login')}>Ya tengo cuenta</button>
        </form>
      )}
    </dialog>
  )
}
/* eslint-enable react/prop-types */
