import { useEffect, useState } from 'react'
import DistrictDetail from './DistrictDetail'
import DistrictMap from './DistrictMap'
import { contourColor, zoneKey } from './districtColor'
import './JudicialPage.css'

/* eslint-disable react/prop-types -- el distrito llega de la búsqueda por código postal */
export default function JudicialPage({
  postalCode,
  postalResult,
  onPostalCode,
  onSearch,
  onOpenNote,
}) {
  const [selectedKey, setSelectedKey] = useState(null)
  const zones = postalResult?.zones || []
  const selected = zones.find((zone) => zoneKey(zone) === selectedKey) || null

  useEffect(() => {
    setSelectedKey(null)
  }, [postalResult])

  return (
    <section className="judicial-page" aria-labelledby="judicial-title">
      <p className="eyebrow">Poder Judicial</p>
      <h1 id="judicial-title">Aspirantes del distrito</h1>
      <p className="intro-copy">
        El código postal localiza las zonas oficiales. Desde ahí se listan las personas que aspiran a un cargo judicial.
      </p>
      <p className="district-definition">
        Un distrito judicial electoral es la región, dentro de un circuito, donde se vota por cargos del Poder Judicial. No es el distrito federal electoral: su número vale dentro del estado. El corte usado es del 10 de febrero de 2025 y junta secciones electorales. El código postal ubica un municipio; si ese municipio toca más de un distrito, aquí aparecen todos.
      </p>
      <form className="postal-search" onSubmit={onSearch}>
        <label>
          Código postal
          <input value={postalCode} onChange={(event) => onPostalCode(event.target.value)} inputMode="numeric" />
        </label>
        <button type="submit">Buscar distrito</button>
      </form>
      {postalResult && (
        <div className="postal-result">
          {(postalResult.municipio || postalResult.estado) && (
            <p>{[postalResult.municipio, postalResult.estado].filter(Boolean).join(' · ')}</p>
          )}
          {postalResult.asentamientos?.length > 0 && (
            <p>{postalResult.asentamientos.map((item) => item.nombre).join(' · ')}</p>
          )}
          {postalResult.municipio && !selected && (
            <DistrictMap municipio={postalResult.municipio} zones={zones} />
          )}
          {selected ? (
            <DistrictDetail
              zone={selected}
              zones={zones}
              municipio={postalResult.municipio}
              estado={postalResult.estado}
              aspirantes={postalResult.aspirantes}
              onBack={() => setSelectedKey(null)}
              onOpenNote={onOpenNote}
            />
          ) : (
          <ul aria-label="Zonas del código postal">
            {zones.map((zone) => {
              const color = contourColor(zones, zone)
              return (
                <li key={zoneKey(zone)}>
                  <a
                    className="district-link"
                    href={`#distrito-${zoneKey(zone)}`}
                    style={color ? { color } : undefined}
                    onClick={(event) => {
                      event.preventDefault()
                      setSelectedKey(zoneKey(zone))
                    }}
                  >
                    {zone.name} · {zone.code}
                  </a>
                  <small>
                    {zone.secciones
                      ? `${zone.source} · ${zone.secciones} secciones`
                      : `${zone.valid_from} – ${zone.valid_to}`}
                  </small>
                </li>
              )
            })}
          </ul>
          )}
          {zones.length === 0 && <p>{postalResult.detail}</p>}
          {!selected && <div className="aspirant-list">
            {(postalResult.aspirantes || []).map((aspirante) => (
              <article className="aspirant-card" key={`${aspirante.id}-${aspirante.office}-${aspirante.zone.code}`}>
                <h2>{aspirante.name}</h2>
                <p>{aspirante.office} · {aspirante.election}</p>
                <p>{aspirante.zone.name} · {aspirante.zone.code}</p>
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
            ))}
          </div>}
        </div>
      )}
    </section>
  )
}
/* eslint-enable react/prop-types */
