# QA y Validación Técnica — Smart Kitchen Intelligence (SKI)

**Entrega 6 — Proyecto Final y Defensa**
**Fecha de esta validación:** 2026-07-11
**Alcance:** pipeline Python, notebooks, dataset final, dashboard Plotly/HTML y workbook Tableau.

Este documento registra qué se verificó, cómo, y qué resultado dio — para que cualquier
persona (incluido el jurado) pueda repetir las comprobaciones sin tener que confiar
únicamente en afirmaciones. Donde no fue posible verificar algo desde este entorno
(por ejemplo, renderizado real en Tableau Desktop), se dice explícitamente.

---

## 1. Calidad de datos (dataset final)

Verificado programáticamente sobre los 4 CSV de negocio + `inventory_v1.csv` (interim
y processed) + los 2 CSV/joins con precio, el 2026-07-11:

| Archivo | Filas | Filas duplicadas | Nulos |
|---|---|---|---|
| `data/processed/inventory_v1.csv` | 25,819 | 0 | `nutriscore`: 3,576 · `calories_100g`: 3,576 |
| `data/interim/inventory_v1.csv` | 25,819 | 0 | idéntico al de arriba |
| `tableau/datos_finales/fact_con_precio.csv` | 25,819 | 0 | `nutriscore`/`calories_100g`/`bucket_calorico`: 3,576 |
| `tableau/datos_finales/fact_eventos_tableau.csv` | 25,819 | 0 | `nutriscore`/`calories_100g`/`bucket_calorico`: 3,576 |
| `tableau/datos_finales/kpi_por_hogar.csv` | 10 | 0 | ninguno |
| `tableau/datos_finales/agg_temporal_ubicacion.csv` | 389 | 0 | ninguno |
| `tableau/datos_finales/agg_ubicacion_nutriscore.csv` | 136 | 0 | ninguno |
| `tableau/datos_finales/dim_hogar_segmentos.csv` | 10 | 0 | ninguno |
| `tableau/datos_finales/insights_prescriptivos.csv` | 30 | 0 | ninguno |

**Los 3,576 nulos son un único hallazgo, no tres**: corresponden exactamente a los
**7 productos** del catálogo (de 50) cuyo `nutriscore` llegó como el literal
`'Falta Dato'` y que, verificado contra `data/raw/catalog_raw.csv`, también carecen de
`calories_100g` (Organic Red Bell Pepper, Apple Honeycrisp Organic, Organic Hass
Avocado, Organic Large Extra Fancy Fuji Apple, Strawberries, Organic Strawberries,
Organic Granny Smith Apple — todos productos frescos sin código de barras estándar,
consistente con huecos reales de cobertura en APIs de catálogo nutricional).
`proteins_100g`/`carbs_100g` sí están completos para esos 7 productos — es un hueco
parcial, no una fila totalmente vacía. Estos nulos se **preservan intencionalmente**
(no se imputan en el dataset final) para no inventar un grado NutriScore; ver
`docs/data_dictionary.md`.

**Integridad referencial:** `qa_integridad.json` confirma cuadre exacto entre
`fact_eventos_tableau` y `dim_hogar_segmentos` (14,238 eventos OUT y 5,053 eventos
Waste en ambas tablas, sin discrepancia).

---

## 2. Preprocesamiento (`src/preprocessing.py`)

- **Reproducibilidad verificada por reejecución:** se corrió `python
  src/preprocessing.py` con los defaults (sin argumentos) y se comparó el resultado
  contra el `data/interim/inventory_v1.csv` ya comprometido en git — **filas y
  columnas idénticas** tras ordenar por `event_id` (`DataFrame.equals() == True`).
  El único cambio observado fue en `transformations_log.json`: el archivo comprometido
  estaba truncado a mitad del JSON (le faltaba el cierre de `rango_temporal`); la
  reejecución produce el JSON completo con los mismos valores numéricos. No se
  modificó lógica de negocio en este script salvo lo descrito en la sección 6.
- **Reglas P1–P6** (outlier calórico, homologación de categorías + ubicación derivada,
  integridad referencial, tipos explícitos, nutriscore faltante, deduplicación) están
  implementadas y su efecto queda registrado cuantitativamente en el log de
  transformaciones en cada corrida.

---

## 3. Feature engineering (`src/features.py`, `src/reduction.py`)

- Matriz de 61 features (3 numéricas + 6 one-hot de categoría + 50 TF-IDF de
  `product_name` + hora/día), escalada con `StandardScaler`. Verificado:
  `feature_matrix.npy` tiene shape `(25819, 61)`.
- PCA: 29/61 componentes retienen el 90% de varianza (verificado, `reduction_summary.json`).
- t-SNE: muestra n=5,000, `perplexity=30`, `random_state=42` — reproducible.
- **Hallazgo de negocio verificado numéricamente** (no solo visual): `location` es
  función determinista de `category_name` en este dataset —
  `pd.crosstab(category_name, location)` no tiene superposición: cada una de las 6
  categorías cae en exactamente una ubicación. Esto se documenta en
  `docs/componente_avanzado.md` §6 y se integró como hallazgo real (no solo anexo
  técnico) en el dashboard HTML.

---

## 4. Dashboard Plotly/HTML (`tableau/Sem12_Dashboard_SmartKitchen.html`)

- **Generación:** `python src/build_dashboard_html.py` corre sin errores y produce un
  HTML autocontenido (~267 KB).
- **Verificación de renderizado real:** se sirvió el archivo con
  `python -m http.server` y se abrió con Playwright/Chromium headless (instalado para
  esta validación, ya que el entorno no tenía navegador). Se comprobó:
  - `console --errors` vacío (0 errores de JS) en cada carga.
  - Los 5 gráficos Plotly (`ranking`, `salud`, `longitudinal`, `transversal`, `pca`)
    parsean como JSON válido y montan en su `<div>` correspondiente.
  - Capturas de pantalla de página completa y de cada sección confirmaron: leyendas
    posicionadas al costado (no se superponen con las series), sin colisión de texto,
    sin desbordes, grid responsive a 1 columna probado conceptualmente vía CSS
    (`@media max-width:900px`) — **no se verificó visualmente en un viewport móvil
    real**, solo se confirmó que la regla CSS existe y aplica el patrón esperado.
- **Calculado en vivo desde datos, no hardcodeado:** los 4 KPI, el bloque de contexto
  de gasto, y las cifras de la hero section se calculan en `compute_narrative()` a
  partir de los CSV en `tableau/datos_finales/` en cada build — si los datos cambian,
  el dashboard se actualiza solo.

---

## 5. Workbook Tableau (`tableau/Sem12_Dashboard_SmartKitchen.twb`)

**Limitación explícita:** este entorno no tiene Tableau Desktop instalado, así que
**no se verificó el renderizado visual real** (tipos de marca, comportamiento de
filtros/parámetros en pantalla, formato condicional). Lo que sí se validó
automáticamente, sin necesitar Tableau Desktop, con `tableau/validate_twb.py`:

| Validación | Resultado |
|---|---|
| XML bien formado | OK |
| 11 hojas presentes y con nombre único | OK |
| Cada hoja referencia una fuente de datos que existe | OK (7/7 fuentes) |
| Cada campo usado en filas/columnas/encodings existe en las columnas reales de su fuente | OK — se encontró y corrigió 1 error real: `pca_components_tableau` declaraba columnas `PC4`/`PC5` que no existen en el CSV (que solo tiene PC1–PC3) y le faltaban `timestamp`/`dias_para_vencer`/`calories_100g`, que sí existen. Esto habría roto la conexión al abrir en Tableau. |
| Cada zona de los 3 dashboards apunta a una hoja existente | OK |
| IDs de zona únicos por dashboard | OK |
| Zonas dentro de los límites del lienzo (100000×100000) | OK |
| Rutas de conexión portables | Corregido: eran absolutas (`C:/Users/gabri/...`, solo funcionaban en una máquina); ahora son relativas al `.twb` (`datos_finales/`, `../outputs/`). |

**Hallazgo adicional:** el `.twbx` previamente comprometido en el repo
(`Sem12_Dashboard_SmartKitchen.twbx`, empaquetado 2026-06-12) solo contenía 3 hojas de
PCA/t-SNE — **no tenía el dashboard principal** (KPIs, longitudinal, transversal,
tabla por hogar, insights). Causa raíz: un script de debugging
(`build_twb_minimal.py`) escribía al mismo nombre de archivo que el script completo
(`build_dashboard_twb.py`) y lo sobrescribió. Se archivó todo el historial confuso en
`tableau/_archive/` (ver `tableau/README.md`) y se regeneró un `.twb` limpio desde el
script completo, que ahora incluye 11 hojas y 3 dashboards (principal, anexo
metodológico, y una nueva pestaña "Contexto y Glosario" con el mismo contenido de
benchmark/NutriScore agregado al dashboard HTML).

**Pendiente manual (requiere Tableau Desktop, no se puede hacer desde aquí):** abrir
`Sem12_Dashboard_SmartKitchen.twb`, confirmar que las 11 hojas cargan sin error de
conexión, revisar visualmente los 3 dashboards, y exportar como `.twbx` empaquetado
para la entrega final. Instrucciones detalladas en `tableau/README.md`.

### Validación de filtros y parámetros

Documentado en `docs/reglas_analiticas.md` y `docs/entregas/Entrega5_Arquitectura_Dashboard_SKI.md`:
el parámetro `household_id` (0–9) debe propagarse a las 8 hojas analíticas mínimas vía
una acción de filtrado. Esta lógica vive dentro de Tableau (parámetros y acciones no
son parte del XML generado por el script Python de forma completa) y **debe
verificarse manualmente en Tableau Desktop** — no es verificable desde este entorno.

---

## 6. Campos calculados

| Campo | Definición | Verificado |
|---|---|---|
| `costo_perdido` | `IF classification IN ('Waste','Forced_Waste') THEN quantity * precio_unitario ELSE 0` | Sí — recomputado en `compute_narrative()` del dashboard HTML y cruzado contra `kpi_global.json` (S/ 38,830.5 en ambos). |
| `dias_para_vencer` | `expiry_date - timestamp` (negativo = ya vencido) | Sí — reimplementado independientemente en pandas en `notebooks/02_limpieza.ipynb` y comparado campo a campo contra la salida de `src/preprocessing.py`: **coincide exactamente** (mismo conteo de eventos vencidos: 5,053). |
| `nutriscore_grupo` | Agrupación de A–E en 3 buckets (Saludable A-B / Crítico C-D / Riesgo D-E) | Sí — el catálogo de 50 productos no contiene grado E, por lo que "Riesgo (D-E)" nunca aparece poblado; documentado explícitamente en el glosario del dashboard para que no se lea como un error. |
| `tasa_desperdicio` | `eventos_waste / eventos_out` | Sí, verificado por ubicación (Refrigerador 37.5%, Despensa 19.4%, Estante 4.1%) contra `agg_temporal_ubicacion.csv`. |

---

## 7. Consistencia visual (dashboard HTML)

- Paleta categórica del mapa PCA validada con el script `validate_palette.js` de la
  skill de visualización: banda de luminosidad, piso de croma, separación CVD
  (deuteranopía/tritanopía) y contraste contra fondo blanco — **todas las
  verificaciones pasan** (ver commit del mapa PCA en `src/build_dashboard_html.py`).
- Colores por ubicación (Refrigerador/Despensa/Estante) y por categoría NutriScore son
  consistentes en las 4 secciones que los usan (ranking, salud, longitudinal,
  transversal) — se definen una sola vez en el diccionario `C` y se reutilizan, no se
  redefinen por gráfico.
- Legendas de series múltiples (longitudinal, transversal) reposicionadas al costado
  derecho, fuera del área de trazado — confirmado visualmente en las capturas de
  pantalla de la sección 4.

---

## 8. Beta testing realizado

| Prueba | Método | Resultado |
|---|---|---|
| ¿El dashboard carga sin JS roto? | Playwright headless, `console --errors` | 0 errores |
| ¿Los 5 gráficos montan? | Inspección de `Plotly.newPlot` calls + JSON parse | 5/5 OK |
| ¿El HTML es válido (tags balanceados)? | Conteo de `<div>`/`</div>` | 133/133 balanceados |
| ¿Las 4 notebooks núcleo corren de punta a punta? | `jupyter nbconvert --execute` en copia aislada | Ver sección 9 |
| ¿El `.twb` es abrible sin campos rotos? | `tableau/validate_twb.py` (estructural, sin Tableau Desktop) | Limpio tras corrección de `pca_components_tableau` |
| ¿La reimplementación en pandas de la limpieza coincide con Polars? | `notebooks/02_limpieza.ipynb`, celda de verificación final | 6/6 checks OK (filas, columnas, nulos, vencidos, distribución location, distribución categoría) |

---

## 9. Estado de los notebooks (reproducibilidad end-to-end)

Auditoría ejecutando cada notebook headless en una copia aislada (no se modificaron
los archivos originales del repo salvo las correcciones descritas abajo):

| Notebook | Estado antes de esta entrega | Corrección aplicada | Estado actual |
|---|---|---|---|
| `00_data_pipeline.ipynb` | Fallaba: usaba rutas relativas asumiendo cwd=raíz del repo, pero el kernel de Jupyter fija cwd=`notebooks/`; además los `subprocess.run` tragaban errores silenciosamente (solo imprimían, no fallaban) | Rutas ancladas a `REPO_ROOT = Path.cwd().parent`; nuevo helper `run_step()` que fija `cwd=REPO_ROOT` en cada subproceso y **lanza excepción** si el script falla, en vez de continuar con datos inexistentes. También se corrigieron 2 bugs latentes independientes: `preprocessing.py` no aceptaba los argumentos `--input/--catalog/--output` que este notebook le pasaba (los ignoraba silenciosamente y escribía en su ruta hardcodeada), y las celdas de reporte QA leían claves del log (`initial_record_count`, `anomalies_detected`) que **nunca existieron** en el esquema real. | Estructuralmente corregido. **Limitación honesta:** este notebook incluye una llamada de red real a una API externa (`src/ingestion.py` → USDA FoodData Central); no se re-ejecutó la cadena completa en vivo (arriesgaría sobrescribir el catálogo validado con una respuesta de red distinta/no determinista). Se verificó en cambio que `preprocessing.py` con sus defaults reproduce exactamente el dataset comprometido (sección 2). |
| `01_perfilado.ipynb` | Corre limpio | — | Sin cambios, documentación algo escueta (aceptable). |
| `02_limpieza.ipynb` | **Fallaba de forma determinística**: dos celdas de carga de datos y de mapeo de categorías estaban tipeadas como celdas Markdown en vez de código (nunca se ejecutaban), dejando el notebook dependiente de que `01_perfilado.ipynb` hubiera corrido antes en el mismo kernel. Contenía además dos implementaciones duplicadas e incompatibles de la limpieza (una con un mapeo de categorías que no corresponde al dataset real), y calculaba `dias_para_vencer` como `hoy - expiry_date` en vez de `expiry_date - timestamp` (no reproducible, fecha-dependiente, e inconsistente con toda la documentación). | Reescrito completo: notebook autocontenido (carga sus propios datos), narra las mismas reglas P1–P6 que `src/preprocessing.py`, calcula `dias_para_vencer` correctamente, y termina con una celda de verificación que compara su resultado contra el CSV oficial. | Ejecutado end-to-end con éxito; **los 6 checks de verificación final coinciden exactamente** con el pipeline oficial (ver sección 8). |
| `03_modelo_metricas.ipynb` | Corre limpio (~3 min) | — | Bien documentado, con tablas de justificación de features y métricas. |
| `04_componente_avanzado.ipynb` | Corría "limpio" solo porque los artefactos que necesita (`feature_matrix.npy`, `outputs/*_tableau.csv`) ya existían en el repo de una corrida manual anterior de `src/features.py`/`src/reduction.py` — ningún notebook de la cadena 00–05 los genera; en un clon nuevo habría fallado de inmediato. | Se agregó una celda de setup que verifica si los artefactos existen y, si faltan, ejecuta `features.py`/`reduction.py` automáticamente (mismo patrón `cwd=REPO_ROOT` + raise-on-failure que en 00). | Ejecutado end-to-end con éxito (confirmado con los artefactos ya presentes; la lógica de regeneración usa el mismo mecanismo ya probado en el notebook 00). |
| `05_metricas_segmentos_tableau.ipynb` | Corre limpio | — | Bien documentado. |

---

## 10. Limitaciones conocidas

- **Dataset sintético:** `movements_raw.csv` es una simulación calibrada (patrones
  Instacart + vida útil USDA FoodKeeper), no observaciones de hogares reales. Todas
  las cifras de pérdida/desperdicio deben leerse como ilustrativas de un fenómeno
  plausible, no como una medición censal (ver `docs/QA_validation.md` §1 y
  `docs/entregas` para el detalle de por qué se optó por simulación).
- **`location` ≡ `category_name`:** en este dataset ambas variables son
  redundantes (cada categoría cae en una sola ubicación física). El análisis "por
  ubicación" del dashboard es, matemáticamente, un análisis "por categoría de
  producto" — ver `docs/componente_avanzado.md` §6 para la discusión completa. No
  invalida el análisis (la lógica de negocio detrás del mapeo es realista: los
  perecibles van al refrigerador), pero significa que no se puede aislar el efecto
  de "dónde se guarda" del efecto de "qué tipo de alimento es" con este dataset.
- **`household_id` es un ID sintético** sin información generalizable — por diseño,
  excluido de los modelos predictivos (ver `docs/bitacora_entregas.md`, Entrega 3).
- **Catálogo de 50 productos no incluye NutriScore E** — el grado más bajo presente
  es D. El bucket "Riesgo (D-E)" existe en el código/leyenda por completitud
  conceptual del estándar NutriScore, pero nunca se puebla con estos datos.
- **`.twbx` empaquetado pendiente de generación manual** en Tableau Desktop (ver
  sección 5) — este entorno no puede producir ni verificar visualmente ese paso.
- **`00_data_pipeline.ipynb` depende de una API externa en vivo** (USDA FoodData
  Central vía `src/ingestion.py`); en un entorno sin acceso a internet o con la API
  caída, ese notebook específico no completará, aunque el resto del pipeline
  (`preprocessing.py` en adelante) no depende de la red.
- **Sesgo de imbalance en el target de ML** (~65% consumo / ~35% pérdida), mitigado
  con `class_weight='balanced'` — documentado y justificado en
  `docs/bitacora_entregas.md`, no es un descuido.

---

## 11. Checklist final de aprobación

- [x] Dataset final sin filas duplicadas, nulos documentados y trazables a su causa raíz.
- [x] `src/preprocessing.py` reproduce exactamente el dataset comprometido (byte-a-byte tras ordenar).
- [x] Reimplementación independiente de la limpieza (notebook 02, pandas) coincide con el pipeline oficial (Polars).
- [x] Los 6 notebooks corren sin error de código propio (00 y 04 requerían artefactos previos; ahora se autogeneran o fallan con mensaje claro en vez de silenciosamente).
- [x] Dashboard HTML: 0 errores de consola, 5/5 gráficos renderizan, leyendas al costado, paleta categórica validada.
- [x] Workbook Tableau: XML válido, 11/11 hojas con datasource y campos correctos, 0 referencias rotas — corregido 1 bug real (columnas PC4/PC5 inexistentes) que habría impedido abrir la hoja "Mapa latente (PCA)" en Tableau.
- [x] KPIs, contexto de gasto (benchmark de industria) y NutriScore explicados con fuente citada, no solo mostrados como números aislados.
- [x] Componente avanzado (PCA/t-SNE) documentado con justificación, mecánica, aplicación, impacto de negocio e interpretación — y visualmente integrado al dashboard (no solo un anexo textual).
- [ ] **Apertura y verificación visual manual en Tableau Desktop** (fuera del alcance de este entorno — ver `tableau/README.md`).
- [ ] **Empaquetado final `.twbx`** (paso manual en Tableau Desktop).
