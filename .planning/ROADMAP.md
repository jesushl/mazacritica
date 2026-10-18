# Roadmap — v0.1 Experiencia social de noticias

## Phase 1 — Sistema visual y feed editorial

**Objetivo:** Consolidar la portada, los tokens visuales y la estructura del feed simulado.

**Cubre:** REQ-001, REQ-002

**Entregables:**
- Componentización de shell, navegación, feed, nota y rail.
- Tokens de color, tipografía, espaciado y estados.
- Búsqueda, filtros, pestañas, guardados y estado vacío.
- Datos mock alineados con la futura API.

## Phase 2 — Responsive y accesibilidad

**Objetivo:** Hacer que todas las funciones esenciales sean usables en móvil, tablet y teclado.

**Cubre:** REQ-003, REQ-004

**Entregables:**
- Breakpoints y reflujo de columnas.
- Objetivos táctiles y foco visible.
- Semántica, ARIA y mensajes de estado.
- Verificación en viewport móvil y escritorio.

## Dependencias

Phase 2 depende de la estructura y estados estabilizados en Phase 1.

## Alcance siguiente — API editorial y cívica autenticada

Este tramo ocurre en el backend. El frontend React permanece como prototipo hasta un tramo posterior.

### Phase A — Cuentas y token

**Objetivo:** Registrar, autenticar y consultar el perfil.

**Cubre:** REQ-005

**Entregables:**
- `UserProfile` con nickname normalizado.
- `TokenAuthentication` junto con la autenticación de sesión.
- `POST /register/`, `POST /login/`, `POST /logout/` y `GET /me/`.
- Grupos `member`, `editor` y `moderator`.

### Phase B — Permisos editoriales

**Objetivo:** Reservar la escritura de notas, etiquetas y fuentes al grupo `editor`.

**Cubre:** REQ-006, REQ-010

**Entregables:**
- Permiso `IsEditor` sobre el grupo `editor`.
- Lectura pública y de miembros limitada a notas publicadas.
- Autor forzado al editor autenticado y `published_at` obligatorio al publicar.

### Phase C — Conversación de dos niveles

**Objetivo:** Persistir comentarios moderables con profundidad de Facebook.

**Cubre:** REQ-007

**Entregables:**
- Modelos `Comment`, `CommentReport` y `ModerationAction`.
- Comentario de primer nivel o respuesta directa; rechazo `400` de un tercer nivel o de un padre de otra nota.
- Estado inicial `pending`, instantánea de nickname y lectura pública solo de comentarios visibles.
- Pruebas del límite de dos niveles antes del modelo y de la API.

### Phase D — Elegibilidad por código postal

**Objetivo:** Resolver candidaturas desde un código postal mediante una zona oficial fechada.

**Cubre:** REQ-008

**Entregables:**
- Modelos `Election`, `Office`, `Candidate`, `Candidacy`, `PostalCode`, `ElectionZone` y `PostalCodeZoneMapping`.
- Un código postal puede mapear a varias zonas.

### Phase E — Semilla ficticia

**Objetivo:** Cargar un conjunto local repetible.

**Cubre:** REQ-009

**Entregables:**
- Comando `seed_demo_data`, determinista y ficticio.

Phase B depende de Phase A. Phase C depende de Phase A y Phase B. Phase D y Phase E pueden seguir cuando las cuentas y los permisos editoriales ya estén verificados.

## Fuera de este tramo

La conexión del frontend React con la API queda para después de la API de cuentas, permisos, comentarios y datos cívicos.
