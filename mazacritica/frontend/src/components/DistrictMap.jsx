import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const mexico = [23.6, -102.5]

/* eslint-disable react/prop-types -- el mapa recibe el municipio ya resuelto */
export default function DistrictMap({ municipio, estado }) {
  const node = useRef(null)
  const [status, setStatus] = useState('Buscando el municipio en el mapa.')

  useEffect(() => {
    const map = L.map(node.current, { scrollWheelZoom: false }).setView(mexico, 5)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 18,
    }).addTo(map)
    const query = new URLSearchParams({
      format: 'jsonv2',
      limit: '1',
      countrycodes: 'mx',
      q: `${municipio}, ${estado}, México`,
    })
    let cancelled = false
    fetch(`https://nominatim.openstreetmap.org/search?${query}`, {
      headers: { 'Accept-Language': 'es' },
    })
      .then((response) => (response.ok ? response.json() : []))
      .then((places) => {
        if (cancelled) return
        const place = places[0]
        if (!place) {
          setStatus('No encontramos ese municipio en el mapa.')
          return
        }
        const point = [Number(place.lat), Number(place.lon)]
        L.circleMarker(point, {
          radius: 9,
          color: '#e55943',
          fillColor: '#e55943',
          fillOpacity: 0.9,
        }).addTo(map)
        map.setView(point, 11)
        setStatus(`Marca de ${municipio}. El mapa no dibuja el contorno del distrito.`)
      })
      .catch(() => {
        if (!cancelled) setStatus('No pudimos cargar el mapa del municipio.')
      })
    return () => {
      cancelled = true
      map.remove()
    }
  }, [municipio, estado])

  return (
    <div className="district-map-block">
      <div ref={node} className="district-map" role="region" aria-label={`Mapa de ${municipio}`} />
      <p>{status}</p>
    </div>
  )
}
/* eslint-enable react/prop-types */
