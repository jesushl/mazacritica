import { useEffect, useMemo, useRef, useState } from 'react';
import './App.css';

const notes = [
  {
    id: 1,
    type: 'Análisis',
    title: 'El nuevo mapa del poder: qué cambió esta semana',
    summary:
      'Una lectura con contexto sobre las decisiones que movieron la agenda pública y sus protagonistas.',
    source: 'MazaCrítica · Redacción',
    publishedAt: '13 oct. 2026 · 18:42',
    informationStatus: 'Contexto documentado',
    editor: 'Mesa editorial',
    content:
      'Las decisiones públicas de esta semana dibujan un nuevo mapa de alianzas, prioridades y tensiones institucionales. Esta nota reúne los hechos publicados, sus fuentes y las preguntas que todavía permanecen abiertas.',
    time: 'Hace 18 min',
    tags: ['Poder público', 'Contexto', 'Seguimiento'],
    comments: 38,
    commentSamples: [
      {
        nickname: '@NorteInformado',
        time: 'Hace 12 min',
        text: 'El contexto ayuda a separar la decisión publicada de las interpretaciones que todavía están abiertas.',
      },
      {
        nickname: '@ClaraM',
        time: 'Hace 5 min',
        text: '¿Podrían agregar la fuente original del documento en la próxima actualización?',
      },
    ],
    shares: 124,
    age: 18,
    discussionRank: 2,
    accent: 'coral',
  },
  {
    id: 2,
    type: 'Nota',
    title: 'Congreso abre discusión sobre la reforma de transparencia',
    summary:
      'La comisión presentó el calendario de trabajo. Estas son las preguntas que todavía no tienen respuesta.',
    source: 'El Diario Público',
    publishedAt: '13 oct. 2026 · 17:58',
    informationStatus: 'Debate abierto',
    editor: 'MazaCrítica · Verificación',
    content:
      'La comisión legislativa presentó un calendario para discutir la reforma de transparencia. El documento todavía está sujeto a cambios y la votación no tiene fecha definitiva.',
    time: 'Hace 1 h',
    tags: ['Legislativo', 'Transparencia'],
    comments: 16,
    commentSamples: [
      {
        nickname: '@VozPublica',
        time: 'Hace 28 min',
        text: 'Sería importante conocer el calendario completo antes de evaluar el alcance de la reforma.',
      },
    ],
    shares: 67,
    age: 60,
    discussionRank: 3,
    accent: 'ochre',
  },
  {
    id: 3,
    type: 'Seguimiento',
    title: 'Una investigación en curso, sin sentencia firme',
    summary:
      'Qué se ha documentado, qué se ha señalado y qué permanece pendiente en el expediente.',
    source: 'MazaCrítica · Archivo',
    publishedAt: '12 oct. 2026 · 09:15',
    informationStatus: 'Investigación en curso',
    editor: 'Mesa editorial',
    content:
      'El expediente reúne señalamientos y documentos públicos, pero no existe una sentencia firme. Esta nota separa lo que está documentado de aquello que todavía se encuentra bajo investigación.',
    time: 'Ayer',
    tags: ['Investigación en curso', 'Presunta irregularidad'],
    comments: 51,
    commentSamples: [
      {
        nickname: '@ObservadorCivico',
        time: 'Ayer',
        text: 'Gracias por distinguir entre un señalamiento y una resolución. Esa diferencia cambia la lectura.',
      },
      {
        nickname: '@ArchivoAbierto',
        time: 'Ayer',
        text: 'Queda pendiente revisar qué autoridad lleva el expediente y cuál es el siguiente plazo.',
      },
    ],
    shares: 89,
    age: 1440,
    discussionRank: 1,
    accent: 'blue',
  },
];

const trending = [
  ['#ReformaElectoral', '2,431 conversaciones'],
  ['#Presupuesto2026', '1,208 conversaciones'],
  ['#Transparencia', '864 conversaciones'],
];

function App() {
  const [activeTab, setActiveTab] = useState('Para ti');
  const [activeTag, setActiveTag] = useState('Todas');
  const [query, setQuery] = useState('');
  const [savedNotes, setSavedNotes] = useState([]);
  const [notice, setNotice] = useState('');
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [socialVariant, setSocialVariant] = useState('Facebook');
  const [headerVisible, setHeaderVisible] = useState(true);
  const lastScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      const scrollingDown = currentScrollY > lastScrollY.current;
      const shouldShow = currentScrollY < 80 || !scrollingDown;

      setHeaderVisible(shouldShow);
      lastScrollY.current = currentScrollY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const filteredNotes = useMemo(() => {
    const normalizedQuery = query.toLowerCase().trim();
    const matchingNotes = notes.filter((note) => {
      const matchesTag =
        activeTag === 'Todas' || note.tags.some((tag) => tag === activeTag);
      const matchesQuery =
        !normalizedQuery ||
        `${note.title} ${note.summary} ${note.tags.join(' ')}`
          .toLowerCase()
          .includes(normalizedQuery);
      return matchesTag && matchesQuery;
    });
    return [...matchingNotes].sort((first, second) => {
      if (activeTab === 'Más discutidas') {
        return first.discussionRank - second.discussionRank;
      }
      if (activeTab === 'Más recientes') {
        return first.age - second.age;
      }
      return first.id - second.id;
    });
  }, [activeTab, activeTag, query]);

  const toggleSaved = (noteId) => {
    setSavedNotes((current) =>
      current.includes(noteId)
        ? current.filter((id) => id !== noteId)
        : [...current, noteId],
    );
  };

  const showNotice = (message) => {
    setNotice(message);
    window.setTimeout(() => setNotice(''), 2400);
  };

  const handleShare = async (note) => {
    const shareText = `${note.title} · MazaCrítica`;
    try {
      await navigator.clipboard.writeText(shareText);
      showNotice('Título copiado para compartir.');
    } catch {
      showNotice('El enlace estará disponible al conectar el backend.');
    }
  };

  const selectedNote = notes.find((note) => note.id === selectedNoteId);

  const openNote = (noteId) => {
    setSelectedNoteId(noteId);
    setSocialVariant('Facebook');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            M
          </div>
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
            <button className="nav-item" type="button" onClick={() => showNotice('El archivo se conectará al backend.')}>
              <span aria-hidden="true">▱</span>
              Archivo
            </button>
            <button className="nav-item" type="button" onClick={() => showNotice('Las conversaciones estarán disponibles pronto.')}>
              <span aria-hidden="true">◌</span>
              Conversaciones
              <span className="nav-count">4</span>
            </button>
          </nav>
        </details>

        <div className="sidebar-footer">
          <div className="profile-avatar">LC</div>
          <div>
            <strong>Lectura ciudadana</strong>
            <span>Cuenta de prueba</span>
          </div>
          <button className="more-button" type="button" aria-label="Más opciones">
            ···
          </button>
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
          <button className="login-button" type="button" onClick={() => showNotice('El acceso estará disponible pronto.')}>
            Ingresar
          </button>
        </header>

        {selectedNote ? (
          <article className={`note-detail accent-${selectedNote.accent}`}>
            <button className="back-button" type="button" onClick={() => setSelectedNoteId(null)}>
              ← Volver al feed
            </button>
            <div className="detail-meta">
              <span className="note-type">{selectedNote.type}</span>
              <span>·</span>
              <span>{selectedNote.publishedAt}</span>
            </div>
            <h1>{selectedNote.title}</h1>
            <p className="detail-summary">{selectedNote.summary}</p>
            <div className="editor-byline">
              <span className="source-avatar">{selectedNote.editor === 'Mesa editorial' ? 'MC' : 'VE'}</span>
              <span>
                <strong>Publicado por {selectedNote.editor}</strong>
                <small>{selectedNote.source}</small>
              </span>
            </div>
            <div className="detail-status">
              <span className="status-mark" />
              <span><strong>Estado de la información:</strong> {selectedNote.informationStatus}</span>
            </div>
            <p className="detail-content">{selectedNote.content}</p>
            <div className="detail-tags">
              {selectedNote.tags.map((tag) => <span className="note-tag" key={tag}>{tag}</span>)}
            </div>

            <section className="social-preview" aria-labelledby="social-preview-title">
              <div className="detail-section-heading">
                <div>
                  <span className="eyebrow">PRESENTACIÓN SOCIAL</span>
                  <h2 id="social-preview-title">Una nota, distintos canales</h2>
                </div>
                <span className="editor-only-label">Solo editores</span>
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
                <p>{selectedNote.summary}</p>
                <small>{selectedNote.tags.join(' · ')}</small>
              </div>
            </section>

            <section className="comments-section" aria-labelledby="comments-title">
              <div className="detail-section-heading">
                <div>
                  <span className="eyebrow">CONVERSACIÓN</span>
                  <h2 id="comments-title">{selectedNote.comments} comentarios</h2>
                </div>
              </div>
              <div className="comment-list">
                {(selectedNote.commentSamples || []).map((comment) => (
                  <article className="comment" key={`${comment.nickname}-${comment.time}`}>
                    <div className="comment-avatar">{comment.nickname.slice(1, 3).toUpperCase()}</div>
                    <div className="comment-body">
                      <div className="comment-meta">
                        <strong>{comment.nickname}</strong>
                        <span>{comment.time}</span>
                      </div>
                      <p>{comment.text}</p>
                      <div className="comment-actions">
                        <button type="button" onClick={() => showNotice('Las respuestas estarán disponibles al conectar la cuenta.')}>
                          Responder
                        </button>
                        <button type="button" onClick={() => showNotice('Los reportes estarán disponibles al conectar la moderación.')}>
                          Reportar
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
              <div className="comment-gate">
                <span className="comment-gate-mark">◌</span>
                <div>
                  <strong>La conversación empieza con contexto.</strong>
                  <p>Regístrate para comentar con tu nickname. Las notas editoriales solo las publica MazaCrítica.</p>
                </div>
              </div>
            </section>
          </article>
        ) : (
          <>
            <section className="intro-section">
              <div>
                <p className="eyebrow"><span className="live-pulse" /> Actualizado hace 3 minutos</p>
                <h1>No seguimos personas.<br /><em>Seguimos hechos.</em></h1>
                <p className="intro-copy">
                  Noticias, contexto y conversación para entender cómo se mueve el poder público.
                </p>
              </div>
              <div className="intro-stamp">
                <span>EDICIÓN</span>
                <strong>01</strong>
                <span>13 OCT. 2026</span>
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
              {['Todas', 'Poder público', 'Legislativo', 'Investigación en curso'].map((tag) => (
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
              {filteredNotes.length ? (
                filteredNotes.map((note, index) => (
                  <article className={`note-card accent-${note.accent}`} key={note.id}>
                <div className="note-meta">
                  <span className="note-type">{note.type}</span>
                  <span className="meta-separator">·</span>
                  <span>{note.time}</span>
                  <button
                    className={savedNotes.includes(note.id) ? 'save-button is-saved' : 'save-button'}
                    onClick={() => toggleSaved(note.id)}
                    type="button"
                    aria-label={savedNotes.includes(note.id) ? 'Quitar de guardados' : 'Guardar nota'}
                  >
                    {savedNotes.includes(note.id) ? '★' : '☆'}
                  </button>
                </div>
                <button className="note-title-button" type="button" onClick={() => openNote(note.id)}>
                  <h2>{note.title}</h2>
                </button>
                <p className="note-summary">{note.summary}</p>
                <div className="note-source">
                  <span className="source-avatar">{index === 0 ? 'MC' : 'EP'}</span>
                  <span>{note.source}</span>
                </div>
                <div className="note-bottom">
                  <div className="note-tags">
                    {note.tags.map((tag) => <span className="note-tag" key={tag}>{tag}</span>)}
                  </div>
                  <div className="note-actions">
                    <button type="button" onClick={() => openNote(note.id)}>
                      Leer nota →
                    </button>
                    <button type="button" onClick={() => showNotice('La conversación se abrirá cuando haya comentarios.')}>
                      ◌ {note.comments}
                    </button>
                    <button type="button" onClick={() => handleShare(note)}>
                      ↗ {note.shares}
                    </button>
                  </div>
                </div>
                  </article>
                ))
              ) : (
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
        <section className="rail-module pulse-module">
          <div className="module-heading">
            <span className="eyebrow">EN ESTE MOMENTO</span>
            <span className="signal-dot" />
          </div>
          <p className="pulse-number">08</p>
          <p className="pulse-description">temas públicos están tomando forma en la conversación.</p>
          <button className="module-link" type="button" onClick={() => showNotice('Exploraremos todos los temas pronto.')}>
            Ver pulso completo <span>→</span>
          </button>
        </section>

        <section className="rail-module">
          <div className="module-heading">
            <span className="eyebrow">MÁS CONVERSADOS</span>
            <span className="module-period">Esta semana</span>
          </div>
          <div className="trend-list">
            {trending.map(([topic, count], index) => (
              <button className="trend-item" key={topic} type="button" onClick={() => setQuery(topic.replace('#', ''))}>
                <span className="trend-index">0{index + 1}</span>
                <span><strong>{topic}</strong><small>{count}</small></span>
                <span className="trend-arrow">↗</span>
              </button>
            ))}
          </div>
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
  );
}

export default App;
