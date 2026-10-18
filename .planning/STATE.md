# Estado del proyecto

## Current Position

Phase: 1 — Sistema visual y feed editorial
Plan: Alcance de API editorial y cívica autenticada definido
Status: Scope defined, implementation not started
Last activity: 2026-10-17 — Documented authenticated editorial and civic API scope

## Accumulated Context

- El backend ya cuenta con modelos relacionales para notas, etiquetas y fuentes.
- Las etiquetas sensibles deben ser neutrales: señalamiento, denuncia presentada, investigación en curso, presunta irregularidad, proceso judicial y resolución firme.
- El frontend actual es un borrador visual con datos simulados y no debe conectarse al backend en este milestone.
- La dirección visual es social intensa con base editorial cívica, tema claro cálido, tinta oscura y acentos fuertes.
- La audiencia principal es ciudadanía general que busca confianza, contexto y conversación responsable.
- El proyecto no tenía directorio `.planning/` ni repositorio Git al iniciar este ciclo.
- El alcance de API ya decidido usa los grupos `member`, `editor` y `moderator`, token de DRF y las rutas `/register/`, `/login/`, `/logout/` y `/me/`.
- Solo el grupo `editor` crea, edita, publica, archiva o elimina notas, etiquetas y fuentes. El miembro solo comenta una nota existente.
- La conversación tiene exactamente dos niveles: comentario de primer nivel o respuesta directa. Una respuesta no admite respuestas. Padre inválido u otra nota responden `400`. El público solo ve comentarios visibles de esos dos niveles.
- Los comentarios nuevos nacen en `pending` y guardan el nickname. Los modelos previstos son `Comment`, `CommentReport` y `ModerationAction`.
- La elegibilidad electoral entra por código postal y la resuelve un mapeo oficial fechado. Un código postal puede mapear a varias zonas.
- `seed_demo_data` será ficticio y determinista.
- Las etiquetas de estado son Señalamiento, Denuncia presentada, Investigación en curso, Presunta irregularidad, Proceso judicial y Resolución firme.
- Los comentarios, las elecciones, la semilla y React no empiezan hasta que cuentas y permisos editoriales estén comprometidos y las pruebas pasen. Las pruebas del límite de dos niveles se escriben antes que el modelo de comentarios.

## Pending Risks

- La integración frontend-backend queda fuera de v0.1.
- Las fuentes tipográficas se cargan desde Google Fonts y necesitarán una estrategia local o de fallback antes de producción.
- Las acciones simuladas deben conservar mensajes honestos hasta que exista persistencia real.
