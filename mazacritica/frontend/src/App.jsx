import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import { api, isEditor } from './api'
import AppShell from './components/AppShell'
import AuthDialog from './components/AuthDialog'
import CommentThread from './components/CommentThread'
import Feed from './components/Feed'
import { accents, tagNames } from './components/format'
import JudicialPage from './components/JudicialPage'
import NoteDetail from './components/NoteDetail'

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
  const [section, setSection] = useState('inicio')
  const [postalCode, setPostalCode] = useState('')
  const [postalResult, setPostalResult] = useState(null)
  const [loadError, setLoadError] = useState('')
  const [catalogReady, setCatalogReady] = useState(false)
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
          setCatalogReady(true)
        }
      } catch {
        if (!cancelled) {
          setLoadError('No pudimos cargar las notas publicadas.')
          setCatalogReady(true)
        }
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

  const requestAuth = () => {
    setAuthMode('login')
    setAuthOpen(true)
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
    if (selectedNoteId) {
      try {
        setComments(await api.comments(selectedNoteId))
      } catch {
        setComments([])
      }
    }
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
    const result = await api.judicialDistrict(postalCode.trim())
    setPostalResult({
      code: result.code,
      zones: Array.isArray(result.zones) ? result.zones : [],
      aspirantes: Array.isArray(result.aspirantes) ? result.aspirantes : [],
      municipio: result.municipio || '',
      estado: result.estado || '',
      asentamientos: Array.isArray(result.asentamientos) ? result.asentamientos : [],
      detail: result.detail || '',
    })
  }

  const editor = isEditor(account)
  const emptyFeedMessage = catalogReady && !selectedNote && !loadError && section === 'inicio' && filteredNotes.length === 0
    ? 'No encontramos esa nota. Prueba con otra palabra o quita el filtro para ampliar la búsqueda.'
    : ''
  const statusMessage = notice || loadError || emptyFeedMessage
  const noteIndex = selectedNote ? notes.indexOf(selectedNote) : 0

  return (
    <AppShell
      section={section}
      account={account}
      editor={editor}
      onSection={(next) => {
        setSection(next)
        setSelectedNoteId(null)
      }}
      onExplore={() => showNotice('La exploración estará disponible pronto.')}
      status={<div className={notice ? 'toast' : 'live-status'} role="status">{statusMessage}</div>}
    >
      <main className="main-column">
        <header
          className={headerVisible ? 'topbar' : 'topbar is-hidden'}
          {...(headerVisible ? {} : { inert: '' })}
        >
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
          {account && (
            <button className="login-button" type="button" onClick={submitLogout}>Salir</button>
          )}
          {editor && (
            <button className="login-button" type="button" onClick={() => setNoteFormOpen((open) => !open)}>
              Nueva nota
            </button>
          )}
        </header>

        {authOpen && !account && (
          <AuthDialog
            mode={authMode}
            credentials={credentials}
            onCredentials={setCredentials}
            onMode={setAuthMode}
            onLogin={submitLogin}
            onRegister={submitRegister}
            onClose={() => setAuthOpen(false)}
          />
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

        {loadError && <p>{loadError}</p>}

        {section === 'poder-judicial' ? (
          <JudicialPage
            postalCode={postalCode}
            postalResult={postalResult}
            onPostalCode={setPostalCode}
            onSearch={submitPostalSearch}
            onOpenNote={(noteId) => {
              setSection('inicio')
              openNote(noteId)
            }}
          />
        ) : selectedNote ? (
          <NoteDetail
            note={selectedNote}
            accent={accents[noteIndex % accents.length]}
            tagsById={tagsById}
            source={detailSource}
            sourceName={sourcesById.get(selectedNote.source)?.name}
            socialVariant={socialVariant}
            onSocialVariant={setSocialVariant}
            onBack={() => setSelectedNoteId(null)}
          >
            <CommentThread
              comments={comments}
              account={account}
              commentBody={commentBody}
              replyTo={replyTo}
              replyBody={replyBody}
              onCommentBody={setCommentBody}
              onReplyBody={setReplyBody}
              onSubmitComment={submitComment}
              onSubmitReply={submitReply}
              onRequestAuth={requestAuth}
              onReply={(id) => {
                if (!account) {
                  requestAuth()
                  return
                }
                setReplyTo(id)
                setReplyBody('')
              }}
            />
          </NoteDetail>
        ) : (
          <Feed
            notes={filteredNotes}
            tagsById={tagsById}
            sourcesById={sourcesById}
            availableTags={availableTags}
            activeTab={activeTab}
            activeTag={activeTag}
            savedNotes={savedNotes}
            onTab={setActiveTab}
            onTag={setActiveTag}
            onOpen={openNote}
            onToggleSave={(noteId) => setSavedNotes((current) => (
              current.includes(noteId) ? current.filter((id) => id !== noteId) : [...current, noteId]
            ))}
          />
        )}
      </main>
    </AppShell>
  )
}

export default App
