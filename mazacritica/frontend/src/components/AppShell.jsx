import './AppShell.css'

/* eslint-disable react/prop-types -- la sesión llega del estado de App */
export default function AppShell({ section, account, editor, onSection, onExplore, status, children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Navegación">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">M</div>
          <div>
            <span className="brand-name">MazaCrítica</span>
            <span className="brand-kicker">Información que resiste</span>
          </div>
        </div>
        <details className="nav-accordion" open>
          <summary>
            <span>Secciones</span>
            <span className="accordion-chevron" aria-hidden="true">⌄</span>
          </summary>
          <nav className="primary-nav" aria-label="Navegación principal">
            <button
              className={section === 'inicio' ? 'nav-item is-active' : 'nav-item'}
              type="button"
              aria-current={section === 'inicio' ? 'page' : undefined}
              onClick={() => onSection('inicio')}
            >
              <span aria-hidden="true">⌂</span>
              Inicio
            </button>
            <button className="nav-item" type="button" onClick={onExplore}>
              <span aria-hidden="true">⌕</span>
              Explorar
            </button>
            <button
              className={section === 'poder-judicial' ? 'nav-item is-active' : 'nav-item'}
              type="button"
              aria-current={section === 'poder-judicial' ? 'page' : undefined}
              onClick={() => onSection('poder-judicial')}
            >
              <span aria-hidden="true">§</span>
              Poder Judicial
            </button>
          </nav>
        </details>
        <div className="sidebar-footer">
          <div className="profile-avatar">{account ? account.nickname.slice(0, 2).toUpperCase() : 'LC'}</div>
          <div>
            <strong>{account ? account.nickname : 'Lectura ciudadana'}</strong>
            <span>{account ? (editor ? 'Editor' : 'Miembro') : 'Visita'}</span>
          </div>
        </div>
      </aside>
      {children}
      <aside className="right-rail" aria-label="Contexto editorial">
        <section className="rail-module principles-module">
          <h2 className="eyebrow">Nuestra regla</h2>
          <p>Una sospecha no es una sentencia.</p>
          <span className="principles-line" />
          <small>Señalamos el estado de la información para que puedas formar tu propio criterio.</small>
        </section>
        <footer className="rail-footer">
          <span>Sobre el proyecto</span>
          <span>Metodología</span>
          <span>Fuentes</span>
          <span>Contacto</span>
          <small>© 2026 MazaCrítica</small>
        </footer>
      </aside>
      {status}
    </div>
  )
}
/* eslint-enable react/prop-types */
