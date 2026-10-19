export function formatWhen(value) {
  if (!value) return 'Sin fecha'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Sin fecha'
  return new Intl.DateTimeFormat('es-MX', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export function tagNames(note, tagsById) {
  return (note.tags || [])
    .map((tag) => tagsById.get(tag)?.name)
    .filter(Boolean)
}

export const accents = ['coral', 'ochre', 'blue']
