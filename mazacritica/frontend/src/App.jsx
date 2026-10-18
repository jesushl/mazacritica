import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import { api, isEditor } from './api'

const accents = ['coral', 'ochre', 'blue']

function formatWhen(value) {
  if (!value) return 'Sin fecha'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Sin fecha'
  return new Intl.DateTimeFormat('es-MX', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function tagNames(note, tagsById) {
  return (note.tags || [])
    .map((tag) => tagsById.get(tag)?.name)
    .filter(Boolean)
}

/* eslint-disable react/prop-types -- los comentarios llegan de la API */
function CommentItem({ comment, canReply, onReply, replyForm }) {
  return (
    <article className={comment.parent ? 'comment comment-reply' : 'comment'}>
      <div className="comment-avatar">{(comment.nickname || '?').slice(0, 2).toUpperCase()}</div>
      <div className="comment-body">
        <div className="comment-meta">
          <strong>{comment.nickname}</strong>
          <span>{comment.status === 'pending' ? 'Pendiente de moderación' : 'Visible'}</span>
        </div>
        <p>{comment.body}</p>
        {canReply && (
          <div className="comment-actions">
            <button type="button" onClick={() => onReply(comment.id)}>Responder</button>
          </div>
        )}
        {replyForm}
        {(comment.replies || []).map((reply) => (
          <CommentItem comment={reply} canReply={false} key={reply.id} onReply={onReply} />
        ))}
      </div>
    </article>
  )
}
/* eslint-enable react/prop-types */

function App() {
  const [notes, setNotes] = useState([])
  const [tags, setTags] = useState([])
  const [sources, setSources] = useState([])
  const [account, setAccount] = useState(null)
  const [authOpen, setAuthOpen] = useState(false)
  const [authMode, setAuthMode] = useState('login')
  const [credentials, setCredentials] = useState({ email: '', password: '', nickname: '' })
  const [activeTab, setActiveTab] = useState('Para ti')
  const [activeTag, setActiveTag] = useState('Todas')
  const [query, setQuery] = useState('')
  const [savedNotes, setSavedNotes] = useState([])
  const [notice, setNotice] = useState('')
  const [selectedNoteId, setSelectedNoteId] = useState(null)
  const [detailSource, setDetailSource] = useState(null)
  const [comments, setComments] = useState([])
  const [commentBody, setCommentBody] = useState('')
  const [replyTo, setReplyTo] = useState(null)
  const [replyBody, setReplyBody] = useState('')
  const [noteFormOpen, setNoteFormOpen] = useState(false)
  const [noteDraft, setNoteDraft] = useState({ title: '', content: '' })
  const [socialVariant, setSocialVariant] = useState('Facebook')
  const [headerVisible, setHeaderVisible] = useState(true)
  const [postalCode, setPostalCode] = useState('')
  const [postalResult, setPostalResult] = useState(null)
  const [loadError, setLoadError] = useState('')
  const lastScrollY = useRef(0)

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY
      const scrollingDown = currentScrollY > lastScrollY.current
      setHeaderVisible(currentScrollY < 80 || !scrollingDown)
      lastScrollY.current = currentScrollY
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        if (api.getToken()) {
          const profile = await api.me()
          if (!cancelled) setAccount(profile)
        }
        const [noteList, tagList, sourceList] = await Promise.all([
          api.publishedNotes(),
          api.tags(),
          api.sources(),
        ])
        if (!cancelled) {
          setNotes(noteList)
          setTags(tagList)
          setSources(sourceList)
          setLoadError('')
        }
      } catch {
        if (!cancelled) setLoadError('No pudimos cargar las notas publicadas.')
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  const tagsById = useMemo(() => new Map(tags.map((tag) => [tag.id, tag])), [tags])
  const sourcesById = useMemo(() => new Map(sources.map((source) => [source.id, source])), [sources])
  const availableTags = useMemo(() => {
    const names = new Set()
    notes.forEach((note) => tagNames(note, tagsById).forEach((name) => names.add(name)))
    return ['Todas', ...names]
  }, [notes, tagsById])

  const filteredNotes = useMemo(() => {
    const normalizedQuery = query.toLowerCase().trim()
    const matching = notes.filter((note) => {
      const names = tagNames(note, tagsById)
      const matchesTag = activeTag === 'Todas' || names.includes(activeTag)
      const matchesQuery = !normalizedQuery || `${note.title} ${note.excerpt || ''} ${names.join(' ')}`
        .toLowerCase()
        .includes(normalizedQuery)
      return matchesTag && matchesQuery
    })
    return [...matching].sort((first, second) => {
      if (activeTab === 'Más recientes') {
        return new Date(second.published_at || 0) - new Date(first.published_at || 0)
      }
      return first.id - second.id
    })
  }, [activeTab, activeTag, notes, query, tagsById])

  const selectedNote = notes.find((note) => note.id === selectedNoteId) || null

  const showNotice = (message) => {
    setNotice(message)
    window.setTimeout(() => setNotice(''), 2400)
  }

  const openNote = async (noteId) => {
    setSelectedNoteId(noteId)
    setSocialVariant('Facebook')
    setReplyTo(null)
    setComments([])
    setDetailSource(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
    const note = notes.find((item) => item.id === noteId)
    try {
      const [freshNote, thread, source] = await Promise.all([
        api.note(noteId),
        api.comments(noteId),
        note?.source ? api.source(note.source) : Promise.resolve(null),
      ])
      setNotes((current) => current.map((item) => (item.id === freshNote.id ? { ...item, ...freshNote } : item)))
      setComments(thread)
      setDetailSource(source)
    } catch {
      showNotice('No pudimos abrir la nota.')
    }
  }

  const submitLogin = async (event) => {
    event.preventDefault()
    try {
      await api.login({ email: credentials.email, password: credentials.password })
      const profile = await api.me()
      setAccount(profile)
      setAuthOpen(false)
      showNotice(`Sesión de ${profile.nickname}.`)
    } catch {
      showNotice('No pudimos iniciar sesión.')
    }
  }

  const submitRegister = async (event) => {
    event.preventDefault()
    try {
      await api.register({
        email: credentials.email,
        password: credentials.password,
        nickname: credentials.nickname,
      })
      setAuthMode('login')
      showNotice('Cuenta creada. Ahora puedes ingresar.')
    } catch {
      showNotice('No pudimos crear la cuenta.')
    }
  }

  const submitLogout = async () => {
    await api.logout()
    setAccount(null)
    setNoteFormOpen(false)
    showNotice('Sesión cerrada.')
  }

  const submitComment = async (event) => {
    event.preventDefault()
    const created = await api.postComment(selectedNote.id, { body: commentBody })
    setComments((current) => [...current, { ...created, replies: created.replies || [] }])
    setCommentBody('')
  }

  const submitReply = async (event) => {
    event.preventDefault()
    const created = await api.postComment(selectedNote.id, { body: replyBody, parent: replyTo })
    setComments((current) => current.map((comment) => (
      comment.id === replyTo
        ? { ...comment, replies: [...(comment.replies || []), created] }
        : comment
    )))
    setReplyBody('')
    setReplyTo(null)
  }

  const submitNote = async (event) => {
    event.preventDefault()
    const sourceId = sources[0]?.id
    const created = await api.createNote({
      title: noteDraft.title,
      content: noteDraft.content,
      source: sourceId,
      status: 'published',
      published_at: new Date().toISOString(),
    })
    setNotes((current) => [created, ...current])
    setNoteDraft({ title: '', content: '' })
    setNoteFormOpen(false)
    showNotice('Nota publicada.')
  }

  const submitPostalSearch = async (event) => {
    event.preventDefault()
    const result = await api.searchPostalCode(postalCode.trim())
    setPostalResult({
      code: result.code,
      zones: Array.isArray(result.zones) ? result.zones : [],
      detail: result.detail || '',
    })
  }

  const editor = isEditor(account)

  return (
    <div className="app-shell">
      <aside className="sidebar">
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
            <button className="nav-item is-active" type="button" aria-current="page">
              <span aria-hidden="true">⌂</span>
              Inicio
            </button>
            <button className="nav-item" type="button" onClick={() => showNotice('La exploración estará disponible pronto.')}>
              <span aria-hidden="true">⌕</span>
              Explorar
            </button>
            <button className="nav-item" type="button" onClick={() => showNotice('El archivo se conectará con más archivos.')}>
              <span aria-hidden="true">▱</span>
              Archivo
            </button>
            <button className="nav-item" type="button" onClick={() => setQuery('')}>
              <span aria-hidden="true">◌</span>
              Conversaciones
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

      <main className="main-column">
        <header className={headerVisible ? 'topbar' : 'topbar is-hidden'}>
          <div className="mobile-brand">Maza<span>Crítica</span></div>
          <label className="search-box">
            <span aria-hidden="true">⌕</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar notas, temas o fuentes"
              aria-label="Buscar notas, temas o fuentes"
            />
            <kbd>⌘ K</kbd>
          </label>
          {account ? (
            <button className="login-button" type="button" onClick={submitLogout}>Salir</button>
          ) : (
            <button className="login-button" type="button" onClick={() => { setAuthOpen(true); setAuthMode('login') }}>
              Ingresar
            </button>
          )}
          {editor && (
            <button className="login-button" type="button" onClick={() => setNoteFormOpen((open) => !open)}>
              Nueva nota
            </button>
          )}
        </header>

        {authOpen && !account && (
          <section className="auth-panel" aria-label="Acceso">
            {authMode === 'login' ? (
              <form onSubmit={submitLogin}>
                <label>
                  Correo
                  <input value={credentials.email} onChange={(event) => setCredentials({ ...credentials, email: event.target.value })} />
                </label>
                <label>
                  Contraseña
                  <input type="password" value={credentials.password} onChange={(event) => setCredentials({ ...credentials, password: event.target.value })} />
                </label>
                <button type="submit">Entrar</button>
                <button type="button" onClick={() => setAuthMode('register')}>Crear cuenta</button>
              </form>
            ) : (
              <form onSubmit={submitRegister}>
                <label>
                  Nickname
                  <input value={credentials.nickname} onChange={(event) => setCredentials({ ...credentials, nickname: event.target.value })} />
                </label>
                <label>
                  Correo
                  <input value={credentials.email} onChange={(event) => setCredentials({ ...credentials, email: event.target.value })} />
                </label>
                <label>
                  Contraseña
                  <input type="password" value={credentials.password} onChange={(event) => setCredentials({ ...credentials, password: event.target.value })} />
                </label>
                <button type="submit">Registrarme</button>
                <button type="button" onClick={() => setAuthMode('login')}>Ya tengo cuenta</button>
              </form>
            )}
          </section>
        )}

        {editor && noteFormOpen && (
          <form className="note-composer" aria-label="Nueva nota editorial" onSubmit={submitNote}>
            <label>
              Título
              <input value={noteDraft.title} onChange={(event) => setNoteDraft({ ...noteDraft, title: event.target.value })} required />
            </label>
            <label>
              Contenido
              <textarea value={noteDraft.content} onChange={(event) => setNoteDraft({ ...noteDraft, content: event.target.value })} required />
            </label>
            <button type="submit">Publicar nota</button>
          </form>
        )}

        {loadError && <p role="alert">{loadError}</p>}

        {selectedNote ? (
          <article className={`note-detail accent-${accents[notes.indexOf(selectedNote) % accents.length]}`}>
            <button className="back-button" type="button" onClick={() => setSelectedNoteId(null)}>
              ← Volver al feed
            </button>
            <div className="detail-meta">
              <span className="note-type">Nota</span>
              <span>·</span>
              <span>{formatWhen(selectedNote.published_at)}</span>
            </div>
            <h1>{selectedNote.title}</h1>
            <p className="detail-summary">{selectedNote.excerpt}</p>
            <div className="editor-byline">
              <span className="source-avatar">MC</span>
              <span>
                <strong>Publicado por {selectedNote.author || 'MazaCrítica'}</strong>
                <small>
                  {detailSource?.url ? (
                    <a href={detailSource.url}>{detailSource.name}</a>
                  ) : (detailSource?.name || sourcesById.get(selectedNote.source)?.name || 'Fuente')}
                </small>
              </span>
            </div>
            <p className="detail-content">{selectedNote.content}</p>
            <div className="detail-tags">
              {tagNames(selectedNote, tagsById).map((tag) => <span className="note-tag" key={tag}>{tag}</span>)}
            </div>

            <section className="social-preview" aria-labelledby="social-preview-title">
              <div className="detail-section-heading">
                <div>
                  <span className="eyebrow">PRESENTACIÓN SOCIAL</span>
                  <h2 id="social-preview-title">Una nota, distintos canales</h2>
                </div>
              </div>
              <div className="variant-tabs" role="tablist" aria-label="Variantes sociales">
                {['Facebook', 'Instagram', 'TikTok'].map((variant) => (
                  <button
                    className={socialVariant === variant ? 'variant-tab is-active' : 'variant-tab'}
                    key={variant}
                    onClick={() => setSocialVariant(variant)}
                    aria-selected={socialVariant === variant}
                    role="tab"
                    type="button"
                  >
                    {variant}
                  </button>
                ))}
              </div>
              <div className={`social-card social-${socialVariant.toLowerCase()}`}>
                <span className="social-card-label">{socialVariant} · Vista previa</span>
                <strong>{selectedNote.title}</strong>
                <p>{selectedNote.excerpt}</p>
              </div>
            </section>

            <section className="comments-section" aria-labelledby="comments-title">
              <div className="detail-section-heading">
                <div>
                  <span className="eyebrow">CONVERSACIÓN</span>
                  <h2 id="comments-title">{comments.length} comentarios visibles</h2>
                </div>
              </div>
              <div className="comment-list">
                {comments.map((comment) => (
                  <CommentItem
                    key={comment.id}
                    comment={comment}
                    canReply={Boolean(account)}
                    onReply={(id) => {
                      setReplyTo(id)
                      setReplyBody('')
                    }}
                    replyForm={replyTo === comment.id ? (
                      <form onSubmit={submitReply}>
                        <label>
                          Respuesta directa
                          <textarea value={replyBody} onChange={(event) => setReplyBody(event.target.value)} required />
                        </label>
                        <button type="submit">Publicar respuesta</button>
                      </form>
                    ) : null}
                  />
                ))}
              </div>
              {account ? (
                <form className="comment-composer" aria-label="Nuevo comentario" onSubmit={submitComment}>
                  <label>
                    Comentario
                    <textarea value={commentBody} onChange={(event) => setCommentBody(event.target.value)} required />
                  </label>
                  <button type="submit">Publicar comentario</button>
                </form>
              ) : (
                <div className="comment-gate">
                  <span className="comment-gate-mark">◌</span>
                  <div>
                    <strong>La conversación empieza con contexto.</strong>
                    <p>Ingresa para comentar con tu nickname. Las notas editoriales solo las publica MazaCrítica.</p>
                  </div>
                </div>
              )}
            </section>
          </article>
        ) : (
          <>
            <section className="intro-section">
              <div>
                <p className="eyebrow"><span className="live-pulse" /> Edición en curso</p>
                <h1>No seguimos personas.<br /><em>Seguimos hechos.</em></h1>
                <p className="intro-copy">
                  Noticias, contexto y conversación para entender cómo se mueve el poder público.
                </p>
              </div>
              <div className="intro-stamp">
                <span>EDICIÓN</span>
                <strong>01</strong>
                <span>NOTAS PUBLICADAS</span>
              </div>
            </section>
            <div className="feed-tabs" role="tablist" aria-label="Orden del feed">
              {['Para ti', 'Más recientes', 'Más discutidas'].map((tab) => (
                <button
                  className={activeTab === tab ? 'feed-tab is-active' : 'feed-tab'}
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  aria-selected={activeTab === tab}
                  role="tab"
                  type="button"
                >
                  {tab}
                </button>
              ))}
            </div>
            <section className="tag-strip" aria-label="Filtrar por etiquetas">
              <span className="filter-label">Filtrar</span>
              {availableTags.map((tag) => (
                <button
                  className={activeTag === tag ? 'filter-chip is-active' : 'filter-chip'}
                  key={tag}
                  onClick={() => setActiveTag(tag)}
                  aria-pressed={activeTag === tag}
                  type="button"
                >
                  {tag}
                </button>
              ))}
            </section>
            <section className="feed" aria-live="polite">
              {filteredNotes.length ? filteredNotes.map((note, index) => (
                <article className={`note-card accent-${accents[index % accents.length]}`} key={note.id}>
                  <div className="note-meta">
                    <span className="note-type">Nota</span>
                    <span className="meta-separator">·</span>
                    <span>{formatWhen(note.published_at)}</span>
                    <button
                      className={savedNotes.includes(note.id) ? 'save-button is-saved' : 'save-button'}
                      onClick={() => setSavedNotes((current) => (
                        current.includes(note.id) ? current.filter((id) => id !== note.id) : [...current, note.id]
                      ))}
                      type="button"
                      aria-label={savedNotes.includes(note.id) ? 'Quitar de guardados' : 'Guardar nota'}
                    >
                      {savedNotes.includes(note.id) ? '★' : '☆'}
                    </button>
                  </div>
                  <button className="note-title-button" type="button" onClick={() => openNote(note.id)}>
                    <h2>{note.title}</h2>
                  </button>
                  <p className="note-summary">{note.excerpt}</p>
                  <div className="note-source">
                    <span className="source-avatar">MC</span>
                    <span>{sourcesById.get(note.source)?.name || 'Fuente'}</span>
                  </div>
                  <div className="note-bottom">
                    <div className="note-tags">
                      {tagNames(note, tagsById).map((tag) => <span className="note-tag" key={tag}>{tag}</span>)}
                    </div>
                    <div className="note-actions">
                      <button type="button" onClick={() => openNote(note.id)}>Leer nota →</button>
                    </div>
                  </div>
                </article>
              )) : (
                <div className="empty-state">
                  <span className="empty-mark">∅</span>
                  <h2>No encontramos esa nota</h2>
                  <p>Prueba con otra palabra o quita el filtro para ampliar la búsqueda.</p>
                </div>
              )}
            </section>
          </>
        )}
      </main>

      <aside className="right-rail">
        <section className="rail-module">
          <span className="eyebrow">CÓDIGO POSTAL</span>
          <form className="postal-search" onSubmit={submitPostalSearch}>
            <label>
              Código postal
              <input value={postalCode} onChange={(event) => setPostalCode(event.target.value)} inputMode="numeric" />
            </label>
            <button type="submit">Buscar zona</button>
          </form>
          {postalResult && (
            <div className="postal-result">
              <ul aria-label="Zonas del código postal">
                {postalResult.zones.map((zone) => (
                  <li key={`${zone.code}-${zone.valid_from}`}>
                    {zone.name} · {zone.code}
                    <small>{zone.valid_from} – {zone.valid_to}</small>
                  </li>
                ))}
              </ul>
              {postalResult.zones.length === 0 && <p>{postalResult.detail}</p>}
            </div>
          )}
        </section>
        <section className="rail-module principles-module">
          <span className="eyebrow">NUESTRA REGLA</span>
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
      {notice && <div className="toast" role="status">{notice}</div>}
    </div>
  )
}

export default App
