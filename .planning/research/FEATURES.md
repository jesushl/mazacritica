# Investigación de funcionalidades — v0.1

## Patrones recomendados

1. **Feed de contenido único:** búsqueda y filtros refinan una lista lineal en lugar de dividir la información en múltiples feeds desconectados.
2. **Nota escaneable:** titular, resumen, fuente, tiempo relativo, etiquetas y una acción principal visible.
3. **Etiquetas controladas:** las etiquetas deben ser vocabulario canónico y filtrable; no deben convertirse en acusaciones libres ni en comportamiento oculto.
4. **Contexto de fuente:** cada nota debe hacer evidente de dónde proviene la información.
5. **Conversación con normas:** la futura conversación necesita moderación, reglas visibles y distinción entre aportes editoriales y comentarios ciudadanos.
6. **Estados honestos:** los controles simulados deben comunicar que una función todavía no está conectada.

## Aplicación a MazaCrítica

- Mantener el feed como la superficie principal.
- Usar etiquetas como `Investigación en curso` y `Presunta irregularidad` con lenguaje neutral.
- Reservar colores fuertes para estados y acciones, no para afirmar culpabilidad.
- Mostrar fuentes y contexto cerca del contenido, no escondidos en una pantalla secundaria.
- Diseñar el rail lateral como contexto complementario, no como una segunda lista competitiva.

## Fuentes consultadas

- [Reactor engagement feed patterns](https://github.com/promise-language/reactor/blob/main/docs/engagement-feed.md)
- [LLM-Based Content Tagging at The Washington Post](https://dl.acm.org/doi/10.1145/3774935.3807909)
- [Sports Community Design and Live Chat](https://iamsamhankins.com/work/sbnation-communities/)
