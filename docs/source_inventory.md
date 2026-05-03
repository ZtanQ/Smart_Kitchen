# Inventario de fuentes de datos

## Fuente 1 — Catálogo de productos

| Atributo | Valor |
|---|---|
| Nombre | OpenFoodFacts |
| URL | https://world.openfoodfacts.org/data |
| Acceso | API REST pública (`src/ingestion.py`) |
| Licencia | Open Database License (ODbL) |
| Unidad de análisis | Producto comercial identificado por código de barras |
| Cobertura | Global, con sesgo hacia productos europeos y de alta popularidad |
| Variables actuales | 7 (ver `data_dictionary.md`) |
| Variables actuales | 7 (`product_id`, `product_name`, `category`, `nutriscore`, `calories_100g`, `proteins_100g`, `carbs_100g`) |
| Registros actuales | 50 productos (IDs Instacart, nutrición USDA FoodData Central) |
| Actualización | Continua del lado de la fuente; snapshot local congelado por entrega |

**Limitaciones conocidas:**

- Categorización multiidioma e inconsistente (ver R1 en `proposal.md`).
- Completitud variable en nutrientes secundarios.
- Outliers puntuales en variables numéricas (ver R2).

## Fuente 2 — Movimientos de cocina

| Atributo | Valor |
|---|---|
| Origen | Simulación interna (`src/simulation.py`) |
| Unidad de análisis | Evento de ingreso o consumo |
| Licencia | Interno del proyecto |
| Rango temporal | 01-feb-2026 a 01-may-2026 (90 días) |
| Registros | 25,819 eventos |
| Hogares simulados | 10 (`household_id` 0–9) |
| Distribución IN/OUT | 11,581 / 14,238 (~45 % / ~55 %) |
| Clasificación eventos | Purchase 11,581 · Consumption 9,185 · Forced_Waste 3,531 · Waste 1,522 |
| Patrones de compra | Distribución horaria real de Instacart (via `src/extract_patterns.py`) |
| Integridad referencial | 100 % — todos los `product_id` existen en el catálogo |

**Cambios de esquema respecto a Entrega 1:**

- `action_type` renombrado a `event_type`; columna `location` eliminada
- Nuevas columnas: `household_id`, `stock_id`, `classification`
- `expiry_date` presente en **todos** los eventos (IN y OUT)

**Limitaciones conocidas:**

- Son datos sintéticos; no representan conducta real de usuarios (ver R4).
- La estacionalidad semanal se deriva de patrones Instacart, no de observación directa.

## Estrategia de resiliencia (API)

El script `src/ingestion.py` incorpora un mecanismo de fallback:

1. Solicita datos a OpenFoodFacts con `User-Agent` identificado.
2. Si la API responde con error 5xx, timeout, o payload vacío, se activa
   automáticamente un catálogo mínimo de emergencia (`get_mock_catalog`).
3. El snapshot definitivo de catálogo se **congela localmente** tras la
   Entrega 2 para independizar el pipeline de la disponibilidad remota.
