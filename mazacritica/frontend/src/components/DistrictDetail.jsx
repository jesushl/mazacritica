import DistrictMap from './DistrictMap'
import { contourColor } from './districtColor'

/* eslint-disable react/prop-types -- la zona llega de la búsqueda por código postal */
export default function DistrictDetail({
  zone,
  zones,
  municipio,
  estado,
  aspirantes,
  onBack,
  onOpenNote,
}) {
  const color = contourColor(zones, zone)
  const people = (aspirantes || []).filter((aspirante) => aspirante.zone.code === zone.code)

  return (
    <article className="district-detail" aria-labelledby="district-detail-title">
      <a href="#distritos" onClick={(event) => { event.preventDefault(); onBack() }}>
        Distritos de este código postal
      </a>
      <h2 id="district-detail-title" style={color ? { color } : undefined}>
        {zone.name}
      </h2>
      <p className="district-detail-code">{zone.code}</p>
      {municipio && (
        <DistrictMap municipio={municipio} zones={[zone]} color={color || undefined} />
      )}
      <dl>
        <div>
          <dt>Circuito</dt>
          <dd>{zone.source}</dd>
        </div>
        {zone.secciones ? (
          <div>
            <dt>Secciones de {municipio || 'este municipio'}</dt>
            <dd>{zone.secciones}</dd>
          </div>
        ) : (
          <div>
            <dt>Vigencia</dt>
            <dd>{zone.valid_from} – {zone.valid_to}</dd>
          </div>
        )}
        {(municipio || estado) && (
          <div>
            <dt>Lugar de la búsqueda</dt>
            <dd>{[municipio, estado].filter(Boolean).join(' · ')}</dd>
          </div>
        )}
      </dl>
      <div className="aspirant-list">
        {people.length ? people.map((aspirante) => (
          <article className="aspirant-card" key={`${aspirante.id}-${aspirante.office}`}>
            <h3>{aspirante.name}</h3>
            <p>{aspirante.office} · {aspirante.election}</p>
            {aspirante.notes.length ? (
              <ul aria-label={`Notas de ${aspirante.name}`}>
                {aspirante.notes.map((note) => (
                  <li key={note.id}>
                    <button type="button" onClick={() => onOpenNote(note.id)}>
                      {note.title}
                    </button>
                    {note.tags.length > 0 && <small>{note.tags.join(' · ')}</small>}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No aparece en notas publicadas de MazaCrítica.</p>
            )}
          </article>
        )) : (
          <p>No hay aspirantes publicados para este distrito.</p>
        )}
      </div>
    </article>
  )
}
/* eslint-enable react/prop-types */
