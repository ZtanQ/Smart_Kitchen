# Bitácora de transformaciones

Registro cronológico de decisiones sobre los datos. Cada entrada
distingue entre **dato original** y **dato transformado**.

## Entrega 1 — Perfilado (sin transformaciones todavía)

En esta entrega **no se modifican los datos crudos**. Solo se documentan
observaciones para planificar la limpieza de la Entrega 2.

| Fecha | Fuente | Observación detectada | Acción prevista (Entrega 2) |
|---|---|---|---|
| 2026-04-17 | `catalog_raw.csv` | Categorías multiidioma y granularidad inconsistente (22 valores distintos para 50 productos). | Homologar a taxonomía propia de 6–10 categorías. |
| 2026-04-17 | `catalog_raw.csv` | Outlier `calories_100g = 3833.33` en fila 42 (Cookie cacao pépites Sans Sucre). | Aplicar regla de saneamiento: valores > 900 kcal/100 g se marcan como inválidos y se re-imputan desde la API. |
| 2026-04-17 | `catalog_raw.csv` | Variables numéricas insuficientes (3) para PCA / t-SNE. | Extender ingestión con grasas, saturadas, azúcares, fibra, sal y sodio. |
| 2026-04-17 | `movements_raw.csv` | Volumen (1,000) por debajo del mínimo curricular (2,000). | Re-simular con ≥2,500 eventos y rango de 90 días. |
| 2026-04-17 | `movements_raw.csv` | 612 nulos en `expiry_date` confirmados como **estructurales** (solo aplica a `IN`). | No requiere acción; documentar en diccionario. |
