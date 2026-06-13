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
## Entrega 6 — Componente avanzado (PCA + t-SNE)

| Fecha | Fuente | Transformación | Justificación |
|---|---|---|---|
| 2026-06-12 | `data/interim/inventory_v1.csv` | Promovido a `data/processed/inventory_v1.csv` como fuente analítica oficial. | `features.py` y `reduction.py` consumen la capa `processed`; la carpeta estaba vacía. |
| 2026-06-12 | `src/features.py` | Corregido: columnas `category` → `category_name` (el dataset limpio usa `category_name`). | El script fallaba con KeyError; bug heredado de un esquema anterior. |
| 2026-06-12 | `src/reduction.py` | Corregido `event_type` → `action_type`; agregado t-SNE, exportables Tableau y resumen JSON. | Alinear con esquema real y cubrir requisitos de la Entrega 6. |
| 2026-06-12 | `data/features/feature_matrix.npy` | Generada matriz 25,819 × 61 (numéricas + one-hot categoría + TF-IDF nombre + temporales), escalada con StandardScaler. | Insumo para PCA/t-SNE. |
| 2026-06-12 | `outputs/pca_components_tableau.csv` | Export PC1–PC3 + metadata (25,819 filas). | Vista avanzada del dashboard beta en Tableau. |
| 2026-06-12 | `outputs/tsne_sample_tableau.csv` | Export t-SNE 2D sobre muestra reproducible n=5,000 (`random_state=42`, perplexity=30, pre-PCA 30 dims). | t-SNE es O(n²); muestra documentada como limitación. |
| 2026-06-12 | `outputs/pca_variance_table.csv` | Varianza explicada y acumulada por componente (29 componentes retienen 90%). | Sustento de la tabla de energía retenida. |
