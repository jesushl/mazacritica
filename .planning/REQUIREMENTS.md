# Requisitos — v0.1 Experiencia social de noticias

## En alcance

### REQ-001 — Sistema visual editorial-social

La portada debe utilizar una jerarquía tipográfica, paleta, espaciado y estados de interacción consistentes con la dirección social intensa y editorial cívica de MazaCrítica.

**Criterios de aceptación**
- La interfaz usa tokens visuales coherentes.
- El feed, la navegación y el rail lateral comparten reglas de composición.
- Los estados de foco, hover, activo y guardado son distinguibles.

### REQ-002 — Feed y descubrimiento simulados

La portada debe permitir explorar notas simuladas mediante pestañas, búsqueda y filtros por etiquetas.

**Criterios de aceptación**
- “Para ti”, “Más recientes” y “Más discutidas” cambian el orden visible.
- La búsqueda revisa título, resumen y etiquetas.
- Los filtros reducen la lista y existe un estado vacío explicativo.
- Las etiquetas sensibles usan lenguaje neutral.

### REQ-003 — Responsive multiplataforma

La portada debe adaptarse a escritorio, tablet y móvil sin scroll horizontal ni pérdida de las funciones esenciales.

**Criterios de aceptación**
- La composición de tres columnas se transforma en una lectura principal adecuada.
- La navegación lateral y el rail se adaptan en pantallas pequeñas.
- Los controles táctiles importantes alcanzan al menos 44px cuando sea razonable.
- El texto y los chips permanecen legibles.

### REQ-004 — Accesibilidad de interacción

Las interacciones del prototipo deben ser operables con teclado y comunicadas semánticamente.

**Criterios de aceptación**
- Hay foco visible con `:focus-visible`.
- Las pestañas y filtros exponen su selección mediante ARIA.
- Los inputs tienen nombre accesible.
- Los mensajes dinámicos usan una región de estado.
- La estructura usa landmarks y encabezados coherentes.

## Candidatos para v0.2

- Conectar el feed a `/notes/`, `/tags/` y `/sources/`.
- Vista de detalle de nota con fuentes y contexto.
- Persistencia real de guardados.
- Inicio de sesión y perfil.
- Conversaciones moderadas.

## Fuera de alcance

- Modelos o endpoints nuevos del backend.
- Publicación real de notas.
- Sistema de autenticación real.
- Feed personalizado basado en datos de usuario.
- Moderación persistente.
