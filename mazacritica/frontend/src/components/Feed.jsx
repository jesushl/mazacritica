import { accents, formatWhen, tagNames } from './format'
import './Feed.css'

/* eslint-disable react/prop-types -- el feed recibe el catálogo ya filtrado */
export default function Feed({
  notes,
  tagsById,
  sourcesById,
  availableTags,
  activeTab,
  activeTag,
  savedNotes,
  onTab,
  onTag,
  onToggleSave,
  onOpen,
}) {
  return (
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
            onClick={() => onTab(tab)}
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
            onClick={() => onTag(tag)}
            aria-pressed={activeTag === tag}
            type="button"
          >
            {tag}
          </button>
        ))}
      </section>
      <section className="feed">
        {notes.length ? notes.map((note, index) => (
          <article className={`note-card accent-${accents[index % accents.length]}`} key={note.id}>
            <div className="note-meta">
              <span className="note-type">Nota</span>
              <span className="meta-separator">·</span>
              <span>{formatWhen(note.published_at)}</span>
              <button
                className={savedNotes.includes(note.id) ? 'save-button is-saved' : 'save-button'}
                onClick={() => onToggleSave(note.id)}
                type="button"
                aria-label={savedNotes.includes(note.id) ? 'Quitar de guardados' : 'Guardar nota'}
              >
                {savedNotes.includes(note.id) ? '★' : '☆'}
              </button>
            </div>
            <button className="note-title-button" type="button" onClick={() => onOpen(note.id)}>
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
                <button type="button" onClick={() => onOpen(note.id)}>Leer nota →</button>
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
  )
}
/* eslint-enable react/prop-types */
