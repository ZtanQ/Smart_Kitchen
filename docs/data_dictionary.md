# Diccionario de datos — Entrega 1 (preliminar)

> Este diccionario refleja el estado **crudo** de los datos en la Entrega 1.
> Se completa con granularidad, nulos, cardinalidad y reglas de limpieza
> en la Entrega 2.

## Tabla: `catalog_raw.csv`

- **Unidad de análisis:** 1 fila = 1 producto comercial.
- **Clave primaria:** `product_id`.
- **Registros:** 50. **Duplicados de PK:** 0.

| Columna | Tipo | Nulos | Cardinalidad | Observaciones |
|---|---|---|---|---|
| `product_id` | string | 0 | 50 | Código de barras (EAN). |
| `product_name` | string | 0 | 48 | Puede repetirse entre variantes (ej. Nutella ×4). |
| `category` | string | 0 | 22 | **Sucio:** multiidioma, granularidades mezcladas (ver R1). |
| `nutriscore` | char | 0 | 5 | A(12), B(8), C(6), D(6), E(18). |
| `calories_100g` | float | 0 | — | **Outlier detectado:** 3833 en fila 42 (ver R2). |
| `proteins_100g` | float | 0 | — | Rango plausible 0–30 g. |
| `carbs_100g` | float | 0 | — | Rango plausible 0–85 g. |

## Tabla: `movements_raw.csv`

- **Unidad de análisis:** 1 fila = 1 evento de movimiento (IN u OUT).
- **Clave primaria:** `event_id`.
- **Clave foránea:** `product_id` → `catalog_raw.product_id`.
- **Registros:** 1,000. **Integridad referencial:** 100 %.

| Columna | Tipo | Nulos | Cardinalidad | Observaciones |
|---|---|---|---|---|
| `event_id` | string | 0 | 1,000 | Formato `EVT_XXXXX`. |
| `product_id` | string | 0 | 50 | FK a catálogo. |
| `timestamp` | datetime | 0 | — | Rango: 17-mar-2026 → 16-abr-2026. |
| `action_type` | string | 0 | 2 | `IN` (388), `OUT` (612). |
| `location` | string | 0 | 4 | Refrigerador (260), Estantería (260), Despensa (248), Caja (232). |
| `expiry_date` | date | 612 | — | **Nulo estructural:** solo se registra en eventos `IN`. No es problema de calidad. |
