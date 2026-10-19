import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { contourColors } from './districtColor'

const mexico = [23.6, -102.5]

/* eslint-disable react/prop-types -- el mapa recibe las zonas ya resueltas */
export default function DistrictMap({ municipio, zones, color }) {
  const node = useRef(null)
  const polygons = (zones || []).map((zone) => zone.poligono).filter(Boolean)
  const polygonKey = polygons
    .map((feature) => `${feature.properties.circuito_j}-${feature.properties.distrito_j}`)
    .join('|')
  const polygonsRef = useRef(polygons)
  polygonsRef.current = polygons
  const colorRef = useRef(color)
  colorRef.current = color
  const [status, setStatus] = useState('Cargando el mapa.')

  useEffect(() => {
    const features = polygonsRef.current
    const map = L.map(node.current, { scrollWheelZoom: false }).setView(mexico, 5)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 18,
    }).addTo(map)
    if (features.length) {
      const layer = L.geoJSON(
        { type: 'FeatureCollection', features },
        {
          style: (feature) => {
            const index = features.indexOf(feature)
            const paint = colorRef.current || contourColors[(index < 0 ? 0 : index) % contourColors.length]
            return { color: paint, weight: 2, fillColor: paint, fillOpacity: 0.35 }
          },
        },
      ).addTo(map)
      map.fitBounds(layer.getBounds(), { padding: [16, 16] })
      setStatus(
        features.length > 1
          ? 'Contornos del INE. Este municipio toca más de un distrito judicial; se muestran todos.'
          : 'Contorno del distrito judicial publicado por el INE.',
      )
    } else {
      setStatus('No hay contorno del INE para estos distritos.')
    }
    return () => map.remove()
  }, [municipio, polygonKey, color])

  return (
    <div className="district-map-block">
      <div ref={node} className="district-map" role="region" aria-label={`Mapa de ${municipio}`} />
      <p>{status}</p>
    </div>
  )
}
/* eslint-enable react/prop-types */
