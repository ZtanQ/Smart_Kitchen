# Bitacora de transformaciones

Registro cronologico de decisiones sobre los datos.
Cada entrada distingue entre **dato original** y **dato transformado**.

---

## Entrega 1 — Perfilado y Definicion de Calidad

En esta entrega **no se modifican los datos crudos**. Se generan datos a gran escala
y se inyecta ruido intencional para planificar la limpieza de la Entrega 2.

| Fecha | Fuente | Observacion detectada | Accion prevista |
|---|---|---|---|
| 2026-04-30 | catalog_raw.csv | Categorias numericas (Instacart dept_id): 6 valores sin nombre legible. | Mapear a taxonomy propia en P2. |
| 2026-04-30 | catalog_raw.csv | Nutriscore con valor 'Falta Dato' en 7 productos. | Convertir a null en P5; preservar como nulo estructural. |
| 2026-04-30 | catalog_raw.csv | Sin outlier calorico en nueva fuente (umbral 900 kcal). | Mantener salvaguarda P1 activa para datos futuros. |
| 2026-04-30 | movements_raw.csv | Esquema ampliado: 10 hogares x 90 dias = ~25k eventos. | Validar integridad referencial con catalogo (P3). |
| 2026-04-30 | movements_raw.csv | Campo 'location' no presente en nueva simulacion. | Derivar desde dept_id del catalogo via LOCATION_MAP (P2). |
| 2026-04-30 | movements_raw.csv | event_type (IN/OUT) en lugar de action_type. | Crear alias action_type en columnas derivadas. |
| 2026-04-30 | movements_raw.csv | classification distingue Purchase/Consumption/Waste/Forced_Waste. | Preservar; es clave para analisis de desperdicio. |

---

## Entrega 2 — Limpieza y Preparacion (pipeline v2, ejecutado 2026-05-02)

### Dato original -> Dato transformado

| Fecha | Dato original (data/raw/) | Dato transformado (data/interim/inventory_v1.csv) |
|---|---|---|
| 2026-05-02 | catalog_raw.csv: category = 4, 16, 7, 3, 1, 20 (numerico) | category_name = 'Frutas y Verduras', 'Lacteos y Refrigerados', etc. (6 valores legibles) |
| 2026-05-02 | catalog_raw.csv: nutriscore = 'Falta Dato' en 7 productos | nutriscore = null (nulo estructural preservado; 3,576 eventos afectados) |
| 2026-05-02 | catalog_raw.csv: sin columna location | location derivada: Refrigerador (23,758) / Despensa (1,053) / Estante (1,008) |
| 2026-05-02 | movements_raw.csv: event_type (IN/OUT) | action_type = alias normalizado (mismos valores, nombre canonico) |
| 2026-05-02 | movements_raw.csv: 25,819 eventos, 10 columnas | inventory_v1.csv: 25,819 eventos x 17 columnas, tipos uniformes |
| 2026-05-02 | Tablas separadas con tipos heterogeneos | Join materializado: product_id Int64 en ambas tablas, cast explicito completo |
| 2026-05-02 | Sin columna dias_para_vencer | dias_para_vencer derivada = expiry_date - timestamp en dias (positivo=fresco, negativo=vencido) |

### Resumen ejecutivo del pipeline (timestamp: 2026-05-02T23:31:25)

- Catalogo: 50 productos -> 50 productos (P1: 0 outliers caloricos)
- Movements: 25,819 eventos -> 25,819 eventos (P3: 0 huerfanos; P6: 0 duplicados)
- inventory_v1: 25,819 filas x 17 columnas, integridad referencial 100%
- Nutriscore nulo: 7 productos -> 3,576 eventos (nulo estructural preservado)
- Eventos vencidos al momento del evento: 5,053 (dias_para_vencer < 0)
- Cobertura temporal: 2026-02-01 -> 2026-05-01 (90 dias, 10 hogares)

**Trazabilidad tecnica:** data/interim/transformations_log.json — fuente de verdad cuantitativa.

---

## Diferencias respecto a la version anterior (semana5/)

La version anterior (semana5/inventory_v1_clean.csv, 975 filas x 13 columnas) fue
reemplazada por el dataset multi-hogar v2 con las siguientes mejoras:

| Aspecto | Version anterior (semana5) | Version actual (data/interim) |
|---|---|---|
| Volumen | 975 eventos (1 hogar simulado, 30 dias) | 25,819 eventos (10 hogares, 90 dias) |
| Columnas | 13 | 17 (+household_id, +stock_id, +quantity, +classification) |
| Cobertura temporal | Mar-Abr 2026 (30 dias) | Feb-May 2026 (90 dias) |
| Analisis de desperdicio | action_type IN/OUT unico indicador | classification distingue Waste vs Forced_Waste |
| Multi-hogar | No | Si (household_id 0-9) |
| location | Presente en crudo (simulada directamente) | Derivada desde dept_id del catalogo |
| expiry_date nulos | 612 nulos estructurales (solo OUT) | 0 nulos (todos los eventos tienen fecha) |
