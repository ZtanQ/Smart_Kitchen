# Reglas de Métricas, Segmentos y Parámetros — Semana 11

**Proyecto:** Smart Kitchen Intelligence (SKI)
**Curso:** Data Visualization — UPC
**Fecha:** 2026-06-13
**Notebook responsable:** `notebooks/05_metricas_segmentos_tableau.ipynb`
**Fuente analítica única:** `data/interim/inventory_v1.csv` (25 819 eventos, flat table validada en Sem 5)

---

## 1. Principios de diseño

1. **Una sola fuente de verdad por métrica.** Cada flag/derivada se calcula en el notebook 05 y se materializa en una columna. Tableau **suma o cuenta**, no recalcula reglas de negocio.
2. **Granularidad explícita por tabla.** El esquema relacional declara qué tabla agrega y cuál no, para evitar doble conteo si Tableau hace un blend involuntario.
3. **Parámetros como datos, no como cálculos hardcoded.** Todos los umbrales (riesgo, terciles, buckets) se publican como filas en `parametros_tableau.csv`; el workbook los referencia.
4. **Cuadre cruzado obligatorio.** Antes de exportar, se valida que `eventos_out` y `eventos_waste` cuadren entre `fact`, `dim_hogar` y `agg_categoria`. Falla → no se publica.

---

## 2. Estructura relacional final

```
fact_eventos_tableau            dim_hogar_segmentos
  PK: event_id        ────┐       PK: household_id
  FK: household_id ───────┴────── (1:N por household_id)
  FK: product_id

agg_categoria_metricas      ←  fuente independiente (no se une al fact)
agg_temporal_semanal        ←  fuente independiente
parametros_tableau          ←  tabla de referencia (no joinable)
```

| Tabla | Granularidad | PK | Filas | Métricas que vive aquí |
|---|---|---|---|---|
| `fact_eventos_tableau.csv` | 1 evento | `event_id` | 25 819 | flags binarios, buckets, dimensiones |
| `dim_hogar_segmentos.csv` | 1 hogar | `household_id` | 10 | tasas, segmento, umbrales |
| `agg_categoria_metricas.csv` | 1 categoría | `category_name` | 6 | tasa_desperdicio por categoría |
| `agg_temporal_semanal.csv` | 1 semana × categoría | (`semana_iso`, `category_name`) | 82 | tasa_desperdicio temporal |
| `parametros_tableau.csv` | 1 parámetro | `parametro` | 7 | umbrales materializados |

**Control de duplicidad:** `eventos_waste` aparece en `dim_hogar` y `agg_categoria`, pero ambos agregan **desde el mismo subconjunto del fact** (eventos OUT). El QA del notebook valida que sumen al mismo total (5 053).

---

## 3. Métricas derivadas — definiciones

### 3.1 A nivel evento (en `fact_eventos_tableau.csv`)

| Métrica | Fórmula | Tipo | Interpretación |
|---|---|---|---|
| `is_out` | `action_type == 'OUT'` | 0/1 | Es una salida del inventario |
| `is_in` | `action_type == 'IN'` | 0/1 | Es una entrada (compra) |
| `is_waste` | `classification ∈ {Waste, Forced_Waste}` | 0/1 | Salida fue desperdicio |
| `is_forced_waste` | `classification == 'Forced_Waste'` | 0/1 | Producto vencido al momento del OUT |
| `is_consumo` | `classification == 'Consumption'` | 0/1 | Salida fue consumo efectivo |
| `is_vencido` | `dias_para_vencer < 0` | 0/1 | Producto vencido en el evento |
| `flag_riesgo_vencer` | `0 ≤ dias_para_vencer ≤ 2` | 0/1 | Producto en stock y por vencer |
| `bucket_calorico` | `cut(calories_100g, [50, 150, 300])` | ordinal | Densidad energética del producto |
| `turno` | `cut(hora, [5, 11, 17, 23])` | ordinal | Madrugada / Mañana / Tarde / Noche |
| `semana_iso`, `mes`, `dia_semana` | derivadas de `timestamp` | string | Buckets temporales |

**Cómo afectan a la interpretación:**
- `is_waste` es el target del proyecto: cualquier KPI de desperdicio se construye con `SUM(is_waste) / SUM(is_out)`.
- `flag_riesgo_vencer` habilita la **vista preventiva** del dashboard sin reproducir reglas de fecha en Tableau (que tiende a errar con timezones).
- `bucket_calorico` permite el cruce nutrición × desperdicio sin que el usuario tenga que parametrizar cortes en la herramienta.

### 3.2 A nivel hogar (en `dim_hogar_segmentos.csv`)

| Métrica | Fórmula | Interpretación |
|---|---|---|
| `eventos_out` | `COUNT(event_id) WHERE is_out=1` | Volumen de salidas |
| `eventos_waste` | `SUM(is_waste) WHERE is_out=1` | Salidas a desperdicio |
| `tasa_desperdicio_eventos` | `eventos_waste / eventos_out` | KPI principal del hogar |
| `tasa_desperdicio_unidades` | `unidades_waste / unidades_out` | KPI ponderado por cantidad |
| `tasa_forced_waste` | `eventos_forced / eventos_out` | Severidad: % vencidos |

`tasa_desperdicio_eventos` y `tasa_desperdicio_unidades` pueden diferir cuando el hogar desperdicia productos con `quantity > 1` con mayor frecuencia. Reportar ambas evita ocultar ese sesgo.

### 3.3 Agregados (en `agg_categoria_metricas.csv` y `agg_temporal_semanal.csv`)

`tasa_desperdicio = eventos_waste / eventos_out` calculada al nivel de agregación de cada tabla.

---

## 4. Segmentación — definición operativa

**Variable de segmentación:** `tasa_desperdicio_eventos` del hogar.

**Método:** terciles empíricos sobre los 10 hogares (Q33 y Q66 calculados, materializados en `parametros_tableau.csv` y en columnas `umbral_q33`/`umbral_q66` de `dim_hogar`).

**Etiquetas:**
- `Eficiente` — tasa ≤ Q33
- `Promedio` — Q33 < tasa ≤ Q66
- `Crítico` — tasa > Q66

**Distribución resultante (validada en notebook 05):**

| Segmento | Hogares | Tasa promedio |
|---|---|---|
| Eficiente | 0, 8, 9 | ~0.28 |
| Promedio | 3, 5, 7 | ~0.36 |
| Crítico | 1, 2, 4, 6 | ~0.40 |

**Por qué terciles y no umbrales absolutos:** el dataset es simulado y no existe un benchmark externo aceptado de "tasa esperada". Terciles entregan comparación relativa robusta y son trivialmente recomputables si cambia la muestra.

**Uso en Tableau:** filtrar/colorear por `segmento_hogar`. El workbook no necesita recalcular umbrales — los lee de `dim_hogar` o de `parametros_tableau`.

---

## 5. Parámetros — tabla maestra

Materializados como filas en `parametros_tableau.csv`:

| Parámetro | Valor | Tipo | Significado |
|---|---|---|---|
| `umbral_riesgo_dias` | 2 | int | Cota superior de `dias_para_vencer` para `flag_riesgo_vencer` |
| `umbral_segmento_q33` | (calculado) | float | Frontera Eficiente / Promedio |
| `umbral_segmento_q66` | (calculado) | float | Frontera Promedio / Crítico |
| `cutoff_calorico_bajo` | 50 | int | Frontera bajo/medio de `bucket_calorico` |
| `cutoff_calorico_medio` | 150 | int | Frontera medio/alto |
| `cutoff_calorico_alto` | 300 | int | Frontera alto/muy alto |
| `ventana_temporal_dias` | 90 | int | Cobertura del dataset (Feb 1 – May 1 2026) |

**Convención de sincronización:** si se modifica un parámetro en el workbook de Tableau, se actualiza también la fila correspondiente en `parametros_tableau.csv` **y** se re-ejecuta el notebook 05. Los parámetros del workbook **no deben divergir** de la tabla maestra.

---

## 6. Conectividad a Tableau — sin reprocesamiento manual

1. Conectar `fact_eventos_tableau.csv` como **Text File** (delimitador `,`, primera fila como encabezado, codificación UTF-8). Tableau infiere tipos correctamente porque el pipeline cast explícito en notebook 02.
2. Conectar `dim_hogar_segmentos.csv` como segunda fuente y relacionar `household_id ↔ household_id` con cardinalidad N:1 (fact → dim).
3. Conectar `agg_categoria_metricas.csv`, `agg_temporal_semanal.csv` y `parametros_tableau.csv` como **fuentes independientes** (no joinear al fact — generaría doble conteo).
4. Crear los parámetros del workbook leyendo los valores desde `parametros_tableau.csv` (no hardcodear).

Las 5 fuentes son CSV planos, sin caracteres especiales en encabezados, sin nulos en PKs, y con tipos consistentes — listas para conectar.

---

## 7. Chequeos de QA — `qa_integridad.json`

El notebook 05 valida y exporta los siguientes cuadres antes de publicar:

```
fact_pk_unica                : true
dim_hogar_pk_unica           : true
eventos_out  (fact = dim = agg_cat)   : 14 238  ✓
eventos_waste (fact = dim = agg_cat)  :  5 053  ✓
```

Si cualquier `assert` falla, el notebook se detiene y los CSV no se sobrescriben.

---

## 8. Cumplimiento de criterios — Semana 11

| Criterio | Evidencia |
|---|---|
| Estructura relacional validada, sin duplicación de métricas | Sección 2 + QA cuadre cruzado |
| Métricas derivadas consistentes con la pregunta | Sección 3 — todas referidas al desperdicio |
| Al menos un segmento relevante definido | Sección 4 — segmento Eficiente/Promedio/Crítico |
| El equipo puede explicar cómo cada cálculo afecta la interpretación | Comentarios en secciones 3 y 4 |
| Fuentes exportadas conectables sin retrabajo | Sección 6 + tipos validados en notebook 02 |
