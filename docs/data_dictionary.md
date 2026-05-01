# Diccionario de datos — Entrega 1 (Validado)

> Este diccionario refleja la estructura real de los archivos CSV presentes en el repositorio, incluyendo la integración final en `inventory_v1.csv`.

## Tabla: `catalog_raw.csv` (Dimensión Producto)
- **Registros:** 50 productos únicos.

| Columna | Tipo | Observaciones |
|---|---|---|
| `product_id` | int | Identificador único del producto (PK). |
| `product_name` | string | Nombre descriptivo del alimento. |
| `category` | int | ID del departamento/categoría (necesita mapeo). |
| `nutriscore` | char | Calificación A-E. Contiene nulos inyectados para pruebas. |
| `calories_100g` | float | Contenido energético (kcal). |
| `proteins_100g` | float | Gramos de proteína por cada 100g. |
| `carbs_100g` | float | Gramos de carbohidratos por cada 100g. |

## Tabla: `movements_raw.csv` (Hechos de Inventario)
- **Registros:** 25,444 eventos.

| Columna | Tipo | Observaciones |
|---|---|---|
| `event_id` | string | UUID único del movimiento (PK). |
| `stock_id` | string | ID de la unidad física específica en inventario. |
| `product_id` | int | Relación con el catálogo (FK). |
| `event_type` | string | Tipo de acción: `IN` (Entrada) / `OUT` (Salida). |
| `quantity` | int | Cantidad de unidades afectadas. |
| `timestamp` | datetime | Fecha y hora exacta del evento. |
| `expiry_date` | date | Fecha de vencimiento (solo presente en eventos `IN`) |
| `classification` | string | Motivo del movimiento (ej. Purchase, Consumption, Expired). |

## Tabla: `inventory_v1.csv` (Dataset Analítico Final)
Este archivo es el resultado del join entre movimientos y catálogo, listo para Tableau. Contiene todas las columnas anteriores unificadas en una sola unidad de análisis por evento.