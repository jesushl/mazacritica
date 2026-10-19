import { formatWhen, tagNames } from './format'
import './NoteDetail.css'

/* eslint-disable react/prop-types -- la nota abierta llega de App */
export default function NoteDetail({
  note,
  accent,
  tagsById,
  source,
  sourceName,
  socialVariant,
  onSocialVariant,
  onBack,
  children,
}) {
  return (
    <article className={`note-detail accent-${accent}`}>
      <button className="back-button" type="button" onClick={onBack}>
        ← Volver al feed
      </button>
      <div className="detail-meta">
        <span className="note-type">Nota</span>
        <span>·</span>
        <span>{formatWhen(note.published_at)}</span>
      </div>
      <h1>{note.title}</h1>
      <p className="detail-summary">{note.excerpt}</p>
      <div className="editor-byline">
        <span className="source-avatar">MC</span>
        <span>
          <strong>Publicado por {note.author || 'MazaCrítica'}</strong>
          <small>
            {source?.url ? (
              <a href={source.url}>{source.name}</a>
            ) : (source?.name || sourceName || 'Fuente')}
          </small>
        </span>
      </div>
      <p className="detail-content">{note.content}</p>
      <div className="detail-tags">
        {tagNames(note, tagsById).map((tag) => <span className="note-tag" key={tag}>{tag}</span>)}
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
              onClick={() => onSocialVariant(variant)}
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
          <strong>{note.title}</strong>
          <p>{note.excerpt}</p>
        </div>
      </section>
      {children}
    </article>
  )
}
/* eslint-enable react/prop-types */
