# MazaCrítica

MazaCrítica es una plataforma editorial de información y conversación pública. Su propósito es ayudar a la ciudadanía a descubrir noticias, consultar contexto y discutir críticamente asuntos relacionados con representantes populares y el ejercicio del poder público.

La plataforma combina:

- Un portal de notas creadas y publicadas exclusivamente por editores.
- Una experiencia de frontend inspirada en Facebook, Instagram y TikTok.
- Comentarios de personas registradas mediante nickname.
- Etiquetas y fuentes relacionadas en la base de datos.
- Seguimiento futuro de elecciones, candidaturas y zonas electorales mediante código postal.

> MazaCrítica no presenta sospechas como hechos probados. Los estados sensibles deben utilizar lenguaje neutral, como `Señalamiento`, `Investigación en curso`, `Presunta irregularidad` y `Resolución firme`.

## Estado actual

El proyecto se encuentra en una etapa de prototipo funcional:

- El backend Django ya tiene modelos, migraciones y API para notas, etiquetas y fuentes.
- El frontend React/Vite tiene una portada editorial, filtros, búsqueda, detalle de nota, variantes sociales simuladas y comentarios simulados.
- La integración entre el frontend y la API todavía no está realizada.
- La autenticación por token, los perfiles, los comentarios, la moderación, la base electoral y el comando `seed_demo_data` están definidos como alcance de implementación y todavía no están construidos.
- La sección del Poder Judicial y la base electoral están definidas en diseño, pero aún no tienen modelos ni endpoints.

## Alcance definido: API editorial y cívica autenticada

Este es el contrato de la implementación que sigue. No describe el frontend React ni afirma que los modelos de comentarios o elecciones ya existan.

### Roles

Los roles de producto son visitante, miembro, editor y moderador.

| Rol | Cómo se reconoce | Puede |
|---|---|---|
| Visitante | Solicitud sin autenticar | Leer notas publicadas y comentarios visibles |
| Miembro | Grupo de Django `member` | Comentar una nota existente. No crea ni edita notas, etiquetas ni fuentes |
| Editor | Grupo de Django `editor` | Crear, editar, publicar, archivar y eliminar notas, etiquetas y fuentes |
| Moderador | Grupo de Django `moderator` | Actuar sobre la cola de moderación cuando esa API exista |

Los grupos se llaman exactamente `editor`, `moderator` y `member`. El registro de una cuenta crea el usuario y lo agrega al grupo `member`.

### Autenticación

La API usa `TokenAuthentication` de Django REST Framework, además de la autenticación de sesión ya prevista por DRF.

| Método | Ruta | Cuerpo | Resultado |
|---|---|---|---|
| `POST` | `/register/` | `email`, `password`, `nickname` | Crea el usuario con `username` igual al nickname normalizado, correo, contraseña hasheada y perfil. `400` si el correo o el nickname ya existen o si el nickname es inválido |
| `POST` | `/login/` | `email` y `password`, o `username` y `password` | `{token, nickname, email, groups}`. `401` si las credenciales no coinciden |
| `POST` | `/logout/` | Token obligatorio | Elimina el token. `204` |
| `GET` | `/me/` | Token obligatorio | `id`, `email`, `nickname`, `groups` |

El nickname es único, se guarda en minúsculas, tiene de 3 a 30 caracteres y solo admite el patrón `[a-z0-9_]`.

### Contenido editorial

Solo quien pertenece al grupo `editor` puede crear, editar, publicar, archivar o eliminar notas, etiquetas y fuentes. Una persona registrada no puede crear notas. Las notas publicadas exigen `published_at`. El autor de una nota es siempre el editor autenticado. Los borradores quedan ocultos para visitantes y miembros.

### Conversación

La conversación sigue el modelo de Facebook y tiene exactamente dos niveles:

- Un comentario es de primer nivel (`parent` nulo) o una respuesta directa a un comentario de primer nivel.
- Una respuesta no puede tener respuestas.
- Si `parent` es a su vez una respuesta, o si `parent` pertenece a otra nota, la API responde `400`.
- Quien lee en público ve solo los comentarios de primer nivel visibles y sus respuestas directas visibles.

Las personas registradas comentan con una instantánea del nickname. Los comentarios nuevos empiezan en estado `pending`. La lectura pública solo incluye comentarios visibles.

Modelos previstos: `Comment`, `CommentReport` y `ModerationAction`.

### Base cívica y datos de demostración

Modelos previstos: `Election`, `Office`, `Candidate`, `Candidacy`, `PostalCode`, `ElectionZone` y `PostalCodeZoneMapping`.

El código postal es la entrada de búsqueda. Una correspondencia oficial y fechada entre código postal y zona decide la elegibilidad. Un código postal puede corresponder a varias zonas.

El comando de gestión `seed_demo_data` cargará datos ficticios y deterministas. No representa personas, procesos ni resultados reales.

### Etiquetas de estado

Las etiquetas de estado usan lenguaje neutral:

- `Señalamiento`
- `Denuncia presentada`
- `Investigación en curso`
- `Presunta irregularidad`
- `Proceso judicial`
- `Resolución firme`

## Arquitectura

```text
mazacritica/
├── mazacritica/
│   ├── api/                 # Aplicación Django y API REST
│   ├── mazacritica/        # Configuración del proyecto Django
│   ├── frontend/            # Aplicación React/Vite
│   ├── manage.py
│   └── db.sqlite3           # Base local de desarrollo
├── docs/                    # Documentación y decisiones de producto
├── .planning/               # Roadmap y requisitos Learnship
├── AGENTS.md                # Contexto persistente de diseño
└── memory.md               # Propósito permanente del proyecto
```

## Requisitos

- Python 3.14.7, indicado en `.python-version`.
- Node.js y npm.
- Un entorno virtual Python en `.env/`, o las dependencias Django y Django REST Framework instaladas.

## Instalación y ejecución

### Backend

Desde la raíz del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd mazacritica
python manage.py migrate
python manage.py runserver
```

El backend estará disponible en `http://localhost:8000/`.

Python 3.15.0 ya fue publicado, pero el proyecto se mantiene en Python 3.14.7 porque Django todavía no declara soporte oficial para Python 3.15. Cuando Django actualice esa compatibilidad, se podrá cambiar `.python-version` y revisar las dependencias.

### Frontend

En otra terminal:

```bash
cd mazacritica/frontend
npm install
npm run dev
```

El frontend estará disponible en `http://localhost:5173/`.

Comandos disponibles:

```bash
npm run dev       # Servidor de desarrollo
npm run lint      # ESLint
npm run build     # Compilación de producción
npm run preview   # Vista previa de la compilación
```

## API actual

Las rutas se sirven desde el backend Django:

| Método | Ruta | Propósito |
|---|---|---|
| `POST` | `/register/` | Crear cuenta, perfil y membresía del grupo `member` |
| `POST` | `/login/` | Obtener token, nickname, correo y grupos |
| `POST` | `/logout/` | Invalidar el token |
| `GET` | `/me/` | Consultar la cuenta autenticada |
| `GET` | `/notes/` | Listar notas visibles según el rol |
| `POST` | `/notes/` | Crear una nota; solo el grupo `editor` |
| `GET` | `/notes/<id>/` | Consultar una nota visible |
| `PUT/PATCH` | `/notes/<id>/` | Editar, publicar o archivar una nota; solo el grupo `editor` |
| `DELETE` | `/notes/<id>/` | Eliminar una nota; solo el grupo `editor` |
| `GET` | `/tags/` | Listar etiquetas |
| `POST` | `/tags/` | Crear una etiqueta; solo el grupo `editor` |
| `PUT/PATCH` | `/tags/<id>/` | Editar una etiqueta; solo el grupo `editor` |
| `DELETE` | `/tags/<id>/` | Eliminar una etiqueta; solo el grupo `editor` |
| `GET` | `/sources/` | Listar fuentes |
| `POST` | `/sources/` | Crear una fuente; solo el grupo `editor` |
| `PUT/PATCH` | `/sources/<id>/` | Editar una fuente; solo el grupo `editor` |
| `DELETE` | `/sources/<id>/` | Eliminar una fuente; solo el grupo `editor` |

Filtros de notas:

```text
/notes/?tag=investigacion-en-curso
/notes/?status=published
/notes/?date_from=2026-01-01&date_to=2026-12-31
/notes/?search=transparencia
```

Las personas no autenticadas y los miembros solo reciben notas publicadas. Las notas publicadas requieren fecha de publicación. Los borradores solo son visibles para el grupo `editor`.

## Modelo de contenido

Implementado:

- `Note`: nota editorial creada por un editor.
- `Tag`: etiqueta relacional de tema o estado.
- `Source`: fuente documental de una nota.
- `User`: usuario estándar de Django.

Definido para la implementación siguiente:

- `UserProfile`: perfil uno a uno con nickname normalizado.
- `Comment`, `CommentReport`, `ModerationAction`.
- `Election`, `Office`, `Candidate`, `Candidacy`, `PostalCode`, `ElectionZone`, `PostalCodeZoneMapping`.

Una nota puede tener múltiples etiquetas y una etiqueta puede relacionarse con múltiples notas. Una fuente puede tener múltiples notas y no puede eliminarse mientras existan notas que la utilicen.

## Principios editoriales y de producto

1. Las notas, etiquetas y fuentes solo las crean, editan, publican, archivan o eliminan personas del grupo `editor`.
2. Una persona registrada no crea notas. Solo puede comentar una nota existente, con una instantánea de su nickname.
3. La conversación tiene exactamente dos niveles, al estilo de Facebook: comentario de primer nivel o respuesta directa a ese comentario. Una respuesta no admite otra respuesta.
4. Los comentarios nuevos quedan pendientes. El público solo lee comentarios visibles y, en el segundo nivel, solo las respuestas directas visibles.
5. Las fuentes, fechas y estados deben ser visibles.
6. Una etiqueta de investigación no equivale a una condena.
7. Facebook, Instagram y TikTok son canales de presentación de la misma nota editorial.
8. El código postal es la entrada de búsqueda electoral. La elegibilidad la decide una correspondencia oficial y fechada con la zona. Un código postal puede mapear a varias zonas.

## Documentación relacionada

- [Documentación técnica del proyecto](docs/PROJECT.md)
- [Propósito del proyecto](Proposito%20del%20proyecto.md)
- [Memoria permanente](memory.md)
- [Diseño editorial-social](docs/brainstorm/2026-10-14-experiencia-social-editorial.md)
- [Requisitos del milestone](.planning/REQUIREMENTS.md)
- [Roadmap](.planning/ROADMAP.md)

## Verificación

Backend:

```bash
cd mazacritica
../.env/bin/python manage.py check
../.env/bin/python manage.py test
```

Frontend:

```bash
cd mazacritica/frontend
npm run lint
npm run build
```

## Contribución

Antes de implementar una funcionalidad nueva:

1. Revisar el propósito y la memoria del proyecto.
2. Confirmar si la funcionalidad pertenece a editores, usuarios registrados o visitantes.
3. Mantener la trazabilidad de fuentes y estados.
4. Ejecutar las verificaciones del backend y frontend.
5. Actualizar la documentación cuando cambie el alcance.
