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
- La autenticación y la persistencia de comentarios todavía no están implementadas.
- La sección del Poder Judicial y la base electoral están definidas en diseño, pero aún no tienen modelos ni endpoints.

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

- Python 3.12 o compatible con el entorno del proyecto.
- Node.js y npm.
- Un entorno virtual Python en `.env/`, o las dependencias Django y Django REST Framework instaladas.

## Instalación y ejecución

### Backend

Desde la raíz del repositorio:

```bash
cd mazacritica
../.env/bin/python manage.py migrate
../.env/bin/python manage.py runserver
```

El backend estará disponible en `http://localhost:8000/`.

Si el entorno virtual no existe, crea uno e instala Django, Django REST Framework y `django-webpack-loader` según las dependencias del entorno utilizado.

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
| `POST` | `/register/` | Crear un usuario |
| `GET` | `/notes/` | Listar notas visibles |
| `POST` | `/notes/` | Crear una nota autenticada |
| `GET` | `/notes/<id>/` | Consultar una nota |
| `PUT/PATCH` | `/notes/<id>/` | Actualizar una nota autenticada |
| `DELETE` | `/notes/<id>/` | Eliminar una nota autenticada |
| `GET` | `/tags/` | Listar etiquetas |
| `GET` | `/sources/` | Listar fuentes |

Filtros de notas:

```text
/notes/?tag=investigacion-en-curso
/notes/?status=published
/notes/?date_from=2026-01-01&date_to=2026-12-31
/notes/?search=transparencia
```

Las personas no autenticadas solo reciben notas publicadas. Las notas publicadas requieren fecha de publicación.

## Modelo de contenido

- `Note`: nota editorial creada por un editor.
- `Tag`: etiqueta relacional de tema o estado.
- `Source`: fuente documental de una nota.
- `User`: usuario estándar de Django; será la base para futuras cuentas de comentaristas y editores.

Una nota puede tener múltiples etiquetas y una etiqueta puede relacionarse con múltiples notas. Una fuente puede tener múltiples notas y no puede eliminarse mientras existan notas que la utilicen.

## Principios editoriales y de producto

1. Las notas solo las crean y publican editores de MazaCrítica.
2. La comunidad conversa alrededor de las notas mediante comentarios con nickname.
3. Las fuentes, fechas y estados deben ser visibles.
4. Una etiqueta de investigación no equivale a una condena.
5. Facebook, Instagram y TikTok son canales de presentación de la misma nota editorial.
6. El código postal será una entrada de búsqueda electoral, pero la zona oficial será la relación territorial verificable.

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
