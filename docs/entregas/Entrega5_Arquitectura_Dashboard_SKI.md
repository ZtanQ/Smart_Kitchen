# Arquitectura del Dashboard — Smart Kitchen Intelligence (SKI)
## Entrega 5 / Diseño del Dashboard Alpha

**Pregunta central:** ¿Qué impacto tiene la ubicación física en la pérdida económica y de salud del hogar?

---

## 1. Qué cambió y por qué

El dashboard anterior mostraba vistas de **PCA (mapa latente, clusters, energía retenida)**. Esas vistas son parte del componente técnico avanzado (Entrega 6) y tienen valor metodológico, pero **no responden la pregunta del usuario**: un responsable de compras no sabe qué es un cluster ni un componente principal. El dashboard principal debe responder con datos de alimentos: cuánto se consume, cuánto se desperdicia, dónde, con qué perfil nutricional y con qué costo.

**El componente PCA/t-SNE no desaparece** — se mueve a una hoja separada ("Componente Avanzado") como anexo técnico del workbook, no como vista principal del dashboard.

---

## 2. Fuentes de datos para Tableau

Conectar estos archivos desde `tableau/datos_finales/`:

| Archivo | Uso en Tableau | Granularidad |
|---|---|---|
| `fact_con_precio.csv` | Fuente principal — todos los gráficos | 1 evento |
| `dim_hogar_segmentos.csv` | Relación → household_id (N:1) | 1 hogar |
| `kpi_por_hogar.csv` | BANs dinámicos por hogar | 1 hogar |
| `agg_temporal_ubicacion.csv` | Gráfico 1 (longitudinal) | semana × ubicación × hogar |
| `agg_ubicacion_nutriscore.csv` | Gráfico 2 (transversal) | ubicación × nutriscore × tipo_salida |
| `parametros_tableau.csv` | Tabla de referencia (no joinear) | parámetro |

> **Nota sobre precios:** la columna `precio_unitario` (S/) se asignó por categoría con valores de referencia del mercado peruano. Se declara como estimación metodológica en el QA.

---

## 3. Estructura del dashboard (según plan arquitectónico)

### Banda superior — 4 KPIs (BANs)

Todos se calculan sobre `kpi_por_hogar.csv`, filtrados por el parámetro `household_id`.

| KPI | Campo | Fórmula en Tableau | Valor global (todos los hogares) |
|---|---|---|---|
| **KPI 1** Mermas en ubicación crítica | `kpi1_costo_perdido_soles` | `SUM([kpi1_costo_perdido_soles])` | S/ 37,568 (Refrigerador) |
| **KPI 2** Tasa de desperdicio físico | `kpi2_tasa_desperdicio` | `AVG([kpi2_tasa_desperdicio])` | 35.5% |
| **KPI 3** Nutriscore crítico D-E en mermas | `kpi3_pct_nutriscore_DE` | `AVG([kpi3_pct_nutriscore_DE])` | 19.3% |
| **KPI 4** Estancamiento medio (días al OUT) | `kpi4_dias_prom_vencer` | `AVG([kpi4_dias_prom_vencer])` | −2.68 días |

**Cómo leer KPI 4:** un valor negativo significa que el producto ya había vencido en promedio 2.68 días antes de ser retirado. Cuanto más negativo, peor es el punto ciego de esa ubicación.

---

### Módulo izquierdo — Visualizaciones

#### Gráfico 1: Evolución temporal del costo de pérdida por ubicación (Longitudinal)

- **Fuente:** `agg_temporal_ubicacion.csv`
- **Tipo:** Líneas continuas (una por ubicación) o áreas apiladas
- **Eje X:** `semana_iso` (13 semanas, Feb–May 2026)
- **Eje Y:** `costo_perdido` (S/)
- **Color:** `location` → Refrigerador / Despensa / Estante
- **Filtro:** `household_id` (parámetro global del dashboard)
- **Título analítico sugerido:** *"El Refrigerador acumula 98% del costo de pérdida — el pico ocurre en la semana 11"*
- **Anotación:** marcar semana 11 (pico 49.1% tasa) con línea vertical o tooltip explicativo

#### Gráfico 2: Consumo vs. Desperdicio por ubicación y Nutriscore (Transversal)

- **Fuente:** `agg_ubicacion_nutriscore.csv`
- **Tipo:** Barras horizontales agrupadas, segmentadas por `nutriscore`
- **Eje Y:** `location`
- **Eje X:** `eventos` (o `costo`)
- **Segmentos de barra:** `nutriscore` (A → verde, B → amarillo-verde, C → amarillo, D → naranja-rojo)
- **Grupos:** separar `tipo_salida` = Consumo vs. Desperdicio
- **Filtro:** `household_id`
- **Título analítico sugerido:** *"El Refrigerador concentra el 97% del desperdicio — dominado por Frutas y Verduras (Nutriscore A)"*
- **Insight clave que debe leerse solo:** en el Refrigerador se pierde comida saludable (A–B); en la Despensa se pierde comida con Nutriscore D. Son dos problemas distintos.

---

### Módulo derecho — Panel prescriptivo (3 ejes de acción)

Texto fijo que cambia al cambiar el filtro de hogar. Se construye con **hojas de texto** o **tooltips enriquecidos** en Tableau.

#### Eje 1 — Mitigación financiera (Ubicación vs. Pérdida económica)
> *"La [ubicación_critica] representa el [kpi1_costo_perdido_soles / costo_total_perdido × 100]% del impacto financiero por mermas en este hogar. Los productos con menos de 3 días para vencer deben rotarse al Estante de alta visibilidad antes de fin de semana."*

#### Eje 2 — Optimización de compras (Ubicación vs. Rotación)
> *"El inventario perecible en el Refrigerador tiene una tasa de desperdicio de [kpi2_tasa_desperdicio × 100]%. Reducir el volumen semanal de compra en Frutas y Verduras un 20% eliminaría el pico de pérdida de la semana 11."*

#### Eje 3 — Gestión de salud familiar (Ubicación vs. Nutriscore)
> *"El [kpi3_pct_nutriscore_DE × 100]% del desperdicio en este hogar corresponde a Nutriscore D. El hogar está perdiendo capital en alimentos de bajo valor nutricional almacenados en la Despensa."*

---

## 4. Hojas mínimas del workbook (mínimo 8 requeridas)

| # | Nombre de la hoja | Tipo | Responde a |
|---|---|---|---|
| 1 | KPI — Costo pérdida | BAN | KPI 1 |
| 2 | KPI — Tasa desperdicio | BAN | KPI 2 |
| 3 | KPI — Nutriscore crítico | BAN | KPI 3 |
| 4 | KPI — Días estancamiento | BAN | KPI 4 |
| 5 | Evolución temporal por ubicación | Líneas | Gráfico 1 longitudinal |
| 6 | Consumo vs. Desperdicio × Nutriscore | Barras segmentadas | Gráfico 2 transversal |
| 7 | Ranking de hogares por segmento | Dot plot | Comparación entre hogares |
| 8 | Distribución de desperdicio por categoría | Barras horizontales | Vista comparativa |
| 9 | [Anexo técnico] Mapa latente PCA | Scatter | Componente avanzado |
| 10 | [Anexo técnico] Varianza retenida | Pareto | Componente avanzado |

> Las hojas 9 y 10 (PCA) van en una **página separada** del workbook llamada "Componente Avanzado — Metodología". No forman parte del dashboard principal.

---

## 5. Filtro global del dashboard

El parámetro `household_id` (entero, rango 0–9) debe controlar simultáneamente:
- Los 4 BANs
- El gráfico de líneas temporal
- El gráfico de barras transversal
- El panel prescriptivo

En Tableau: usar **Acción de filtro** o **Parámetro → Fuente de datos calculada** para propagar el filtro a todas las hojas del dashboard desde un único selector.

---

## 6. Precios de referencia utilizados (declaración metodológica)

El dataset no incluye precios. Se asignaron precios unitarios estimados por categoría como valor de referencia para habilitar el KPI económico:

| Categoría | Precio unitario (S/) | Base de referencia |
|---|---|---|
| Frutas y Verduras | 4.50 | Mercado local promedio, productos frescos |
| Lácteos y Refrigerados | 8.00 | Supermercado, lácteos empacados |
| Despensa General | 6.50 | Conservas y secos de media gama |
| Congelados | 12.00 | Productos congelados procesados |
| Panadería y Granos | 5.00 | Pan de molde, cereales básicos |
| Bebidas | 7.50 | Bebidas envasadas de 1L |

**Limitación declarada:** los precios son estimativos. El costo real dependería de datos de compra reales por hogar. Esta limitación se incluirá en el documento de QA de la Entrega 6.
