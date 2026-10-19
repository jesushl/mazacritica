export const contourColors = ['#e55943', '#1f4b4a', '#c4a35a', '#355c7d']

export function zoneKey(zone) {
  return `${zone.code}-${zone.valid_from}`
}

export function contourColor(zones, zone) {
  const drawn = (zones || []).filter((item) => item.poligono)
  const index = drawn.findIndex((item) => zoneKey(item) === zoneKey(zone))
  if (index < 0) return null
  return contourColors[index % contourColors.length]
}
