# Memoria del proyecto

## Propósito permanente

MazaCrítica es una plataforma de información y conversación pública que combina un portal de noticias con un frontend inspirado en la experiencia de redes sociales como Meta y X.

Su objetivo es generar noticias y construir un banco de información sobre representantes populares de los poderes Ejecutivo, Legislativo y Judicial. El sistema debe permitir dar seguimiento a las noticias por nombre de persona y relacionar información sobre:

- Cargos actuales y pasados.
- Relaciones temporales con departamentos, dependencias e instituciones.
- Postulaciones a puestos públicos.
- Postulaciones y candidaturas a cargos de elección popular.
- Noticias, decisiones, declaraciones y hechos vinculados con cada representante.

MazaCrítica también debe funcionar como un espacio de conversación crítica sobre representantes populares. Las futuras decisiones de producto y desarrollo deben conservar este equilibrio entre:

1. **Información:** datos y noticias organizados alrededor de personas representantes.
2. **Contexto:** trayectorias, cargos, periodos, relaciones temporales y postulaciones.
3. **Conversación:** participación social y discusión crítica.
4. **Trazabilidad:** diferenciación entre hechos documentados, análisis y opinión.

Este propósito debe orientar la arquitectura de datos, la experiencia de usuario, las funcionalidades editoriales y las herramientas de interacción social del proyecto.

## Alcance autenticado editorial y cívico

Las decisiones siguientes quedan fijadas para la API. El visitante no tiene cuenta. Los roles con cuenta usan los grupos de Django `member`, `editor` y `moderator`.

- Solo el grupo `editor` crea, edita, publica, archiva o elimina notas, etiquetas y fuentes.
- Una persona registrada no crea notas. Solo puede comentar una nota que ya existe.
- La autenticación de la API es el token de Django REST Framework. Las rutas son `POST /register/`, `POST /login/`, `POST /logout/` y `GET /me/`.
- El nickname se guarda normalizado en minúsculas, es único y cumple `[a-z0-9_]` con longitud de 3 a 30 caracteres.
- La conversación tiene exactamente dos niveles, al estilo de Facebook. Un comentario es de primer nivel (`parent` nulo) o una respuesta directa a un comentario de primer nivel. Una respuesta no puede tener respuestas. Si el padre ya es una respuesta, o si pertenece a otra nota, la API responde `400`.
- El público solo ve comentarios de primer nivel visibles y sus respuestas directas visibles. Los comentarios nuevos empiezan como `pending` y conservan una instantánea del nickname.
- Los modelos de conversación previstos son `Comment`, `CommentReport` y `ModerationAction`.
- Los modelos cívicos previstos son `Election`, `Office`, `Candidate`, `Candidacy`, `PostalCode`, `ElectionZone` y `PostalCodeZoneMapping`.
- El código postal es la entrada de búsqueda. La elegibilidad la decide una correspondencia oficial y fechada con la zona. Un código postal puede corresponder a varias zonas.
- `seed_demo_data` será un comando determinista con datos ficticios.
- Las etiquetas de estado permitidas son `Señalamiento`, `Denuncia presentada`, `Investigación en curso`, `Presunta irregularidad`, `Proceso judicial` y `Resolución firme`.

Cuando se implementen los comentarios, las pruebas que cubren el límite de dos niveles se escriben antes del modelo y de la API.
