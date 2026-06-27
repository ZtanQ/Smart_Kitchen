# Entrega 5 — Dashboard Alpha, Insights Exploratorios y Selección de Gráficos

**Proyecto:** Smart Kitchen Intelligence (SKI)
**Curso:** Data Visualization — UPC
**Entrega:** 5 (semana 12–13)
**Fuente analítica:** `data/interim/inventory_v1.csv` → `tableau/datos_finales/`
**Workbook:** `tableau/Sem12_Dashboard_SmartKitchen.twbx`

---

## 1. Insights exploratorios

Los siguientes cinco insights fueron derivados del análisis exploratorio sobre los 25,819 eventos del dataset (10 hogares, 90 días). Todos los números están validados en `notebooks/05_metricas_segmentos_tableau.ipynb` y el cuadre cruzado está documentado en `tableau/datos_finales/qa_integridad.json`.

---

### Insight 1 — Frutas y Verduras concentra el 89.6% del desperdicio total pese a representar el 79.2% de las salidas

**Evidencia:**
- Total de salidas del inventario: 14,238 eventos.
- Frutas y Verduras genera 11,282 salidas (79.2%) pero acumula 4,525 eventos de desperdicio (89.6% del total de 5,053).
- Su tasa de desperdicio es 40.1%, frente al 17.9% del resto de categorías combinadas.

**Interpretación analítica:**
La categoría no solo domina por volumen; su tasa es 2.2 veces superior a la del resto. El problema no es que "se compra más", sino que la proporción de lo comprado que termina descartado es estructuralmente mayor. Esto apunta a un problema de gestión de frescura, no de exceso de compra.

**Implicación para el dashboard:**
Cualquier filtro por categoría debe advertir al usuario que eliminar Frutas y Verduras del análisis elimina casi el 90% del problema. La vista de comparación categórica debe presentar la tasa (no el volumen) como métrica principal para evitar que el usuario confunda "más eventos" con "peor comportamiento".

---

### Insight 2 — El turno Noche concentra el 77.5% del desperdicio total con solo el 43.1% de las salidas

**Evidencia:**
- Salidas nocturnas (20:00–23:59): 6,136 eventos → 3,914 de ellos son desperdicio (tasa 63.8%).
- El resto de turnos combinado (Mañana, Tarde, Madrugada): 8,102 salidas → 1,139 son desperdicio (tasa 14.1%).
- El turno Noche genera desperdicio a una tasa **4.5 veces mayor** que cualquier otro período del día.

**Interpretación analítica:**
La concentración nocturna del desperdicio sugiere que los eventos de tipo `Forced_Waste` (producto vencido al momento de la salida) tienden a registrarse al cierre del día. Esto es consistente con comportamientos reales: el responsable del hogar revisa el refrigerador al final de la jornada y descarta lo que no se consumió. El hallazgo implica que una intervención preventiva (alerta en la tarde) sería más efectiva que una reactiva (contabilidad del desperdicio ya ocurrido).

**Implicación para el dashboard:**
La vista de distribución por turno debe usar un gráfico que permita comparar tanto volumen como tasa. Un gráfico de barras simples del conteo de waste daría una imagen correcta en magnitud pero correcta también en la desproporción de la tasa nocturna.

---

### Insight 3 — Los productos con Nutriscore D se desperdician un 66% más que los de Nutriscore C, en dirección contraria a la hipótesis de preferencia

**Evidencia:**
- Nutriscore D: tasa de desperdicio 41.9% (825 de 1,965 salidas).
- Nutriscore C: tasa 25.2% (225 de 892 salidas).
- Nutriscore A: tasa 34.9% (1,980 de 5,672 salidas).
- Nota: 3,576 eventos (13.9%) tienen Nutriscore nulo (7 productos sin dato declarado).

**Interpretación analítica:**
La hipótesis H1 del proyecto postulaba que los productos con Nutriscore D–E serían *consumidos* más frecuentemente. Los datos no refutan eso directamente —la frecuencia de salida puede ser alta— pero sí muestran que, cuando salen, tienen la mayor proporción de desperdicio. Una lectura posible: los productos de baja calidad nutricional se compran en mayores cantidades de las que se consumen en el ciclo de frescura. La inversión del orden esperado (D peor que A, pero A peor que C) sugiere una relación no monotónica que merece revisión metodológica antes de la entrega final.

**Implicación para el dashboard:**
La vista de relación Nutriscore × tasa de desperdicio debe presentarse con la advertencia del 13.9% de nulos. Un scatter con 4 puntos etiquetados es más honesto que una línea de tendencia que implicaría continuidad entre categorías ordinales.

---

### Insight 4 — La tasa de desperdicio alcanzó su pico histórico en la semana 11 (49.1%) y se estabilizó en ~39.1% a partir de la semana 12

**Evidencia:**
- Semanas 5–6: tasa 0% (inventario recién cargado, productos frescos, sin vencimientos aún).
- Semana 7: 8.9% (primeros vencimientos).
- Semana 11: pico de 49.1% (mayor concentración de productos próximos a vencer simultáneamente).
- Semanas 12–18 (estado estacionario): tasa promedio 39.1%, desviación ±4pp.

**Interpretación analítica:**
La curva no es estable desde el inicio: existe un período de rodaje de ~6 semanas en el que el inventario está fresco y el desperdicio es mínimo, seguido de un pico cuando los primeros productos vencen en masa. A partir de la semana 12 el sistema entra en equilibrio dinámico: las compras reponen lo consumido y lo desperdiciado a una tasa constante. Esta forma de campana asimétrica es esperada en simulaciones de inventario rotativo y valida la lógica del simulador.

**Implicación para el dashboard:**
La vista longitudinal debe mostrar la serie completa de 13 semanas. Si se trunca a partir de la semana 12, el usuario no ve el período de rodaje y puede interpretar el 39% como la tasa normal desde el inicio. La anotación del pico en semana 11 es indispensable.

---

### Insight 5 — Los hogares del segmento Crítico desperdician en promedio 13 puntos porcentuales más que los Eficientes (43.6% vs. 30.6% por unidad)

**Evidencia:**
- Segmento Eficiente (hogares 0, 8, 9): tasa de desperdicio por unidad promedio 30.6% (rango 29.6%–31.0%).
- Segmento Promedio (hogares 3, 5, 7): promedio 39.7% (rango 35.9%–40.1%).
- Segmento Crítico (hogares 1, 2, 4, 6): promedio 43.6% (rango 41.9%–45.5%).
- Diferencia absoluta Crítico–Eficiente: 13.0pp en tasa de unidades; 12.9pp en tasa de eventos.

**Interpretación analítica:**
La segmentación por terciles produce grupos con diferencias suficientemente amplias para ser defendibles como segmentos distintos (13pp de brecha entre extremos, grupos internamente homogéneos con rango de ±1.5pp). Sin embargo, con solo 10 hogares, los terciles son aproximaciones: los límites Eficiente/Promedio y Promedio/Crítico no son robustos si se añade un hogar nuevo. La entrega final debe declarar esta limitación explícitamente.

**Implicación para el dashboard:**
La vista de segmentación debe mostrar los 10 hogares individualmente (strip chart o dot plot), con el color indicando el segmento. Un bar chart con un solo bar por segmento colapsaría la varianza interna y daría una falsa impresión de homogeneidad dentro de cada grupo.

---

## 2. Tabla de selección y descarte de gráficos

### 2.1 Gráficos seleccionados

| # | Gráfico | Vista en dashboard | Justificación técnica |
|---|---|---|---|
| G1 | **Barras horizontales ordenadas** (categoría × tasa de desperdicio) | Comparación categórica | La diferencia entre Frutas (40.1%) y Bebidas (4.1%) es legible en longitud de barra. El orden descendente permite al usuario identificar el problema en menos de 2 segundos. Se elige tasa (ratio) sobre conteo absoluto para evitar que el volumen de Frutas y Verduras distorsione la comparación. |
| G2 | **Línea temporal** (semana × tasa de desperdicio agregada) | Vista longitudinal | Muestra la curva de rodaje + pico + estabilización en un solo trazo. La línea es preferible al área porque el foco es la tendencia, no el volumen acumulado. Se añade una línea de referencia horizontal en 39.1% (media del estado estacionario) para orientar la lectura. |
| G3 | **Heatmap** (día de semana × turno, color = tasa de desperdicio) | Vista de distribución / patrón | La combinación de dos variables discretas con color es la forma más compacta de revelar el patrón nocturno. Con 7 × 4 = 28 celdas, el usuario ve de inmediato que la celda Noche domina en todas las columnas. Se elige sobre un scatter plot porque ambas variables son categóricas, no continuas. |
| G4 | **Dot plot individual con color por segmento** (household_id × tasa de desperdicio) | Segmentación de hogares | Muestra los 10 hogares individualmente, preservando la varianza interna de cada segmento. El color (Eficiente / Promedio / Crítico) añade la dimensión de segmento sin colapsar los puntos. Se elige sobre bar chart agrupado por segmento para no perder la heterogeneidad dentro del grupo Promedio. |
| G5 | **Scatter de 4 puntos** (Nutriscore × tasa de desperdicio, tamaño = volumen de salidas) | Vista de relación | Con 4 categorías ordinales y relación no monotónica (D > A > B > C), un scatter con puntos etiquetados comunica el patrón con honestidad. El tamaño del punto por volumen previene interpretar categorías de bajo volumen (C, D) como igualmente representativas que A. |

### 2.2 Gráficos descartados

| # | Gráfico descartado | Razón del descarte |
|---|---|---|
| D1 | **Treemap de categorías** (área = eventos_out, color = tasa_desperdicio) | Con solo 6 categorías y una diferencia de volumen de 20:1 entre Frutas y Verduras (11,282 eventos) y Despensa General (276 eventos), el treemap produce una celda dominante que hace ilegibles las demás. La comparación de área pequeña vs. área grande es cognitivamente costosa para el usuario. Se reemplazó por barras horizontales (G1). |
| D2 | **Mapa geográfico** (choropleth por región) | El dataset no tiene dimensión territorial. La variable `location` representa la ubicación física dentro del hogar (Refrigerador / Despensa / Estante), no una coordenada geográfica. Un mapa generaría una visualización sin referente analítico real. Se documentó como limitación en `docs/proposal.md` (Riesgo R7). |
| D3 | **Líneas múltiples por categoría** (semana × tasa, una línea por categoría) | Frutas y Verduras tiene 11,282 salidas frente a 276–560 de las demás. Al graficar las 6 categorías en el mismo eje, las líneas de las categorías menores son casi planas y se solapan en la zona inferior. La vista resulta ilegible. Se reemplazó por un filtro de categoría sobre la línea temporal única (G2), con la opción de small multiples para comparación selectiva. |
| D4 | **Pie chart de clasificación** (Consumption / Waste / Forced\_Waste / Purchase) | Los 4 segmentos tienen proporciones que oscilan entre 14% y 36%, lo que hace que los arcos sean difícilmente distinguibles sin etiquetas numéricas. Además, la comparación entre categorías o segmentos de hogar requiere múltiples pies simultáneos, lo que sobrecarga la lectura. Se reemplazó por barra apilada normalizada al 100% cuando se necesita composición. |

---

## 3. Cobertura de los cuatro tipos de vista requeridos

| Tipo de vista | Gráfico que lo cubre | Variable dependiente |
|---|---|---|
| Comparación categórica | G1 — Barras horizontales por categoría | Tasa de desperdicio por categoría |
| Distribución | G3 — Heatmap día × turno | Concentración del desperdicio por período |
| Relación entre variables | G5 — Scatter Nutriscore × tasa | Asociación calidad nutricional – desperdicio |
| Temporal / Tendencia | G2 — Línea semanal | Evolución de la tasa a lo largo de 90 días |

---

## 4. Estado del dashboard alpha

El workbook `tableau/Sem12_Dashboard_SmartKitchen.twbx` incluye las vistas preliminares conectadas a las cinco fuentes de `tableau/datos_finales/`. Los insights de la sección 1 son legibles directamente desde el dashboard sin necesidad de explicación externa adicional, lo que cumple el criterio de "estructura navegable con filtros y flujo de lectura inicial".

Las vistas de Nutriscore (G5) y el heatmap de turno (G3) están en fase de refinamiento visual para la Entrega 6: paleta de color accesible pendiente de validación de contraste.
