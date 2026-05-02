# Bitácora de transformaciones

Registro cronológico de decisiones sobre los datos. Cada entrada distingue entre **dato original** y **dato transformado**.

## Entrega 1 — Perfilado y Definición de Calidad

En esta entrega **no se modifican los datos crudos**. Se han generado datos a gran escala y se ha inyectado ruido intencional para planificar la limpieza de la Entrega 2.

| Fecha | Fuente | Observación detectada | Acción prevista (Entrega 2) |
|---|---|---|---|
| 2026-04-30 | `catalog_raw.csv` | Categorías multiidioma y granularidad inconsistente (multiidioma). | Homologar a taxonomía propia de 6–10 categorías maestras. |
| 2026-04-30 | `catalog_raw.csv` | **Ruido inyectado:** Outlier `calories_100g = 3833.33` y nulos aleatorios en Nutriscore. | Aplicar reglas de saneamiento (umbral 900 kcal) e imputación por moda de categoría. |
| 2026-04-30 | `catalog_raw.csv` | Variables numéricas enriquecidas para análisis avanzado (grasas, azúcares, fibra, sal, sodio). | Preparar matriz de correlación para reducción de dimensionalidad (PCA/t-SNE). |
| 2026-04-30 | `movements_raw.csv` | **Escalabilidad:** Volumen incrementado a >10,000 eventos en un rango de 90 días. | Validar integridad referencial total con la tabla de catálogo. |
| 2026-04-30 | `movements_raw.csv` | ~6,000 nulos en `expiry_date` confirmados como **estructurales** (solo aplica a ingresos `IN`). | Mantener nulos; crear columna derivada `Dias_Para_Vencer` solo para stock actual. |
| 2026-04-30 | `movements_raw.csv` | **Ruido inyectado:** Duplicados de eventos (`event_id`) para probar robustez del pipeline. | Implementar paso de deduplicación basado en PK en el notebook de limpieza. |