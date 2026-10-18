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

## Alcance próximo — API editorial y cívica autenticada

Estas reglas ya están decididas. Su implementación sigue al cierre documental. El frontend React no forma parte de este alcance.

### REQ-005 — Cuentas, token y roles

La API autentica con el token de Django REST Framework y distingue visitante, miembro, editor y moderador.

**Criterios de aceptación**
- Los grupos de Django se llaman `member`, `editor` y `moderator`.
- `POST /register/` acepta `email`, `password` y `nickname`; crea el usuario con `username` igual al nickname normalizado, correo, contraseña hasheada y `UserProfile`, y lo agrega al grupo `member`.
- El nickname es único, se guarda en minúsculas, tiene de 3 a 30 caracteres y cumple `[a-z0-9_]`. Correo duplicado, nickname duplicado o nickname inválido responden `400`.
- `POST /login/` acepta correo y contraseña, o nombre de usuario y contraseña, y responde `{token, nickname, email, groups}`. Las credenciales incorrectas responden `401`.
- `POST /logout/` exige token, lo elimina y responde `204`.
- `GET /me/` exige token y responde `id`, `email`, `nickname` y `groups`.

### REQ-006 — Escritura editorial restringida

Solo el grupo `editor` administra el contenido editorial.

**Criterios de aceptación**
- Un miembro lee únicamente notas publicadas y recibe `403` al crear, actualizar o eliminar notas, etiquetas o fuentes.
- Una visita anónima solo ve notas publicadas.
- Un editor puede crear, publicar, editar y archivar notas, y administrar etiquetas y fuentes.
- Una nota publicada exige `published_at`.
- El autor de la nota es el editor autenticado.
- Los borradores permanecen ocultos para visitantes y miembros.

### REQ-007 — Conversación de dos niveles

Los comentarios siguen el modelo de Facebook: exactamente dos niveles.

**Criterios de aceptación**
- Una persona registrada comenta una nota existente y no puede crear notas.
- El comentario guarda una instantánea del nickname y nace en estado `pending`.
- La lectura pública solo incluye comentarios visibles.
- Un comentario es de primer nivel cuando `parent` es nulo, o una respuesta directa cuando `parent` es un comentario de primer nivel.
- Una respuesta no puede tener respuestas.
- Si `parent` ya es una respuesta, o si `parent` pertenece a otra nota, la API responde `400`.
- El público ve los comentarios de primer nivel visibles y sus respuestas directas visibles.
- Existen los modelos `Comment`, `CommentReport` y `ModerationAction`.
- Las pruebas del límite de dos niveles se escriben antes del modelo y de la API.

### REQ-008 — Elegibilidad electoral por código postal

La búsqueda cívica entra por código postal y resuelve la zona con una correspondencia oficial fechada.

**Criterios de aceptación**
- Existen `Election`, `Office`, `Candidate`, `Candidacy`, `PostalCode`, `ElectionZone` y `PostalCodeZoneMapping`.
- El código postal es la entrada de búsqueda.
- La elegibilidad la decide el mapeo oficial y fechado entre código postal y zona.
- Un código postal puede mapear a varias zonas.

### REQ-009 — Datos ficticios deterministas

Un comando de gestión prepara el entorno local sin inventar hechos reales en cada ejecución.

**Criterios de aceptación**
- Existe `python manage.py seed_demo_data`.
- Los datos son ficticios.
- Ejecuciones repetidas con la misma base vacía producen el mismo conjunto.

### REQ-010 — Etiquetas de estado neutrales

Los estados sensibles no se presentan como condena.

**Criterios de aceptación**
- El vocabulario de estado es `Señalamiento`, `Denuncia presentada`, `Investigación en curso`, `Presunta irregularidad`, `Proceso judicial` y `Resolución firme`.

## Candidatos posteriores

- Conectar el feed de React a `/notes/`, `/tags/` y `/sources/`.
- Vista de detalle de nota con fuentes y contexto.
- Persistencia real de guardados.
- Feed personalizado basado en datos de usuario.

## Fuera de alcance de esta definición

- Implementar ahora los modelos de comentarios, elecciones o el comando `seed_demo_data`.
- Cambiar el frontend React en el mismo tramo que la autenticación y los permisos editoriales.
