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
| Variables objetivo | ≥11 tras enriquecimiento (grasas, saturadas, azúcares, fibra, sal, sodio) |
| Registros actuales | 50 productos |
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
| Rango temporal actual | 17-mar-2026 a 16-abr-2026 (30 días) |
| Rango temporal objetivo | 90 días |
| Registros actuales | 1,000 eventos |
| Registros objetivo | ≥2,500 eventos |
| Distribución IN/OUT | 388 / 612 (~39 % / ~61 %) |
| Ubicaciones | Refrigerador, Estantería, Despensa, Caja (distribución uniforme) |
| Integridad referencial | 100 % — todos los `product_id` existen en el catálogo |

**Limitaciones conocidas:**

- Son datos sintéticos; no representan conducta real de usuarios (ver R4).
- La distribución actual es uniforme en el tiempo; hay que introducir
  estacionalidad semanal plausible antes del análisis longitudinal.
- `expiry_date` solo existe en eventos `IN` (612 nulos estructurales en `OUT`).

## Estrategia de resiliencia (API)

El script `src/ingestion.py` incorpora un mecanismo de fallback:

1. Solicita datos a OpenFoodFacts con `User-Agent` identificado.
2. Si la API responde con error 5xx, timeout, o payload vacío, se activa
   automáticamente un catálogo mínimo de emergencia (`get_mock_catalog`).
3. El snapshot definitivo de catálogo se **congela localmente** tras la
   Entrega 2 para independizar el pipeline de la disponibilidad remota.
