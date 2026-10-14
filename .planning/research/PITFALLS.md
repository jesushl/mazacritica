# Riesgos y errores a evitar — v0.1

## Accesibilidad

- No depender únicamente del color para distinguir estados de notas.
- No usar controles visualmente pequeños en móvil.
- No ocultar el foco de teclado.
- No dejar pestañas con apariencia activa que no cambien el contenido.
- No usar texto de placeholder como único nombre de un campo.

## Producto editorial

- No presentar una etiqueta de sospecha como veredicto.
- No inventar persistencia: las acciones mock deben comunicar su estado.
- No mezclar fuente, análisis y conversación sin una señal visual clara.
- No convertir todos los controles en llamadas a la acción primarias.

## Responsive

- No permitir que el rail lateral provoque scroll horizontal.
- No mantener una grilla de tres columnas en pantallas pequeñas.
- No reducir el texto móvil por debajo de un tamaño legible.
- Probar el foco cuando aparecen mensajes toast o contenido dinámico.

## Rendimiento

- Evitar una dependencia de iconos pesada para símbolos simples.
- Revisar la carga de Google Fonts antes de producción.
- No introducir estado global mientras el feed siga siendo local.
