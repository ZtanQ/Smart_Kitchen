# Guion de Defensa — Smart Kitchen Intelligence (SKI)

Este documento es un guion continuo para la sustentación oral de la Entrega 6. Cada
sección enlaza al artefacto real que la respalda (notebook, script, doc, archivo de
datos) para que cualquier afirmación se pueda mostrar en vivo si el jurado lo pide.
El objetivo es que la presentación fluya como una sola historia, no como una lista de
entregas independientes.

---

## 1. Problema de negocio (arranca aquí)

*"¿Alguna vez compraste algo fresco con toda la intención de usarlo, y terminó en la
basura sin que te dieras cuenta de cuándo pasó?"*

Ese es el problema que ataca SKI. El desperdicio de alimentos en el hogar es
prevenible, pero casi nadie tiene visibilidad agregada de sus propios patrones de
compra, consumo y pérdida — las decisiones de compra semanal se toman a ciegas.
**Pregunta de investigación:** ¿qué impacto tiene la ubicación física donde se guarda
un alimento en la pérdida económica y de salud del hogar? (`docs/proposal.md` §2).

→ *Transición:* "Para responder eso con rigor, no alcanza con un gráfico — hace falta
un pipeline de datos completo. Empecemos por de dónde salen los datos."

## 2. Dataset

Dos fuentes de naturaleza distinta, integradas por `product_id`:
- **Catálogo real** (OpenFoodFacts, 50 productos, vía API pública ODbL): calorías,
  proteínas, carbohidratos, NutriScore.
- **Movimientos simulados** (`src/simulation.py`): 25,819 eventos de inventario,
  10 hogares, 90 días — calibrados con patrones reales de compra de Instacart Online
  Grocery y reglas de vida útil de la USDA FoodKeeper App (no son números
  inventados al azar).

**Por qué simulado y no 100% real:** conseguir datos reales de inventario doméstico
a este nivel de detalle (evento por evento, con ubicación física) no es viable en el
tiempo de un curso — se optó por declarar la naturaleza sintética explícitamente en
vez de disfrazarla (ver `docs/ethics_note.md`, `docs/data_dictionary.md`) y calibrar
el simulador con datos de comportamiento real para que los patrones sean plausibles.

→ *Transición:* "Datos de dos fuentes distintas, con calidad heterogénea de por sí
(OpenFoodFacts trae huecos reales), más anomalías que inyectamos nosotros a propósito
para probar el pipeline de limpieza. Así quedó antes de limpiarlo."

## 3. Preprocesamiento de datos

6 reglas de calidad verificables (P1–P6), documentadas y cuantificadas en
`docs/bitacora_entregas.md`:

| Regla | Qué hace | Efecto medido |
|---|---|---|
| P1 | Outlier calórico (umbral físico 900 kcal/100g) | 0 outliers en la fuente actual (salvaguarda activa) |
| P2 | `dept_id` numérico → `category_name` + `location` derivada | 6 categorías legibles, ubicación inferida del tipo de alimento |
| P3 | Integridad referencial (`product_id` huérfano) | 0 huérfanos |
| P4 | Tipos de dato explícitos | evita inferencia inconsistente Polars/Pandas |
| P5 | NutriScore `'Falta Dato'` → nulo estructural | 7 productos / 3,576 eventos, preservado (no imputado) |
| P6 | Deduplicación por `event_id` | 0 duplicados |

Implementado en `src/preprocessing.py` (Polars, la fuente de verdad reproducible) y
**verificado de forma independiente** reimplementando la misma lógica en Pandas en
`notebooks/02_limpieza.ipynb` — ambas coinciden exactamente (mismo conteo de filas,
nulos, y distribución de categorías; ver `docs/QA_validation.md` §9). Esa doble
implementación no es redundancia: es la evidencia de que la limpieza es correcta, no
solo "el script corre".

→ *Transición:* "Con el dataset limpio (`inventory_v1.csv`, 25,819 × 17), pasamos a la
pregunta de si hay más estructura debajo de la que ya conocíamos."

## 4. Pipeline Python

Arquitectura de scripts reproducibles, cada uno con una responsabilidad:
`simulation.py` → `ingestion.py` → `anomaly_injection.py` → `preprocessing.py` →
`features.py` → `reduction.py` → `export_star_schema.py` → los builders de dashboard
(`src/build_dashboard_html.py`, `tableau/build_dashboard_twb.py`). Cada paso es un
script standalone ejecutable desde la raíz del repo, y los notebooks narran/documentan
la misma lógica (no la reemplazan) — ver `docs/runbook.md` para la secuencia completa.

→ *Transición:* "Con el pipeline montado, aplicamos dos técnicas de machine learning:
una para predecir desperdicio, otra para validar la estructura misma del dataset."

## 5. Modelado y técnica analítica (clasificación)

Problema: clasificación binaria de eventos OUT en `is_waste` (Waste/Forced_Waste) vs.
`Consumption`. Random Forest superó a Regresión Logística en F1/Recall/ROC-AUC. Decisión
técnica clave, y la que más vale la pena mostrar en la defensa: se detectó
empíricamente que `dias_para_vencer` era **fuga de datos** (el simulador la usaba para
asignar las etiquetas — con ella incluida, ambos modelos daban F1=1.0 trivialmente) y
se excluyó del entrenamiento, aunque se conservó en el dataset para uso descriptivo en
Tableau (`docs/proposal.md` §9, `docs/bitacora_entregas.md` Entrega 3).

→ *Transición:* "Eso responde 'qué eventos son pérdida'. La otra pregunta técnica
exigida por la cátedra es distinta: ¿hay estructura latente en los datos que valide
cómo organizamos todo el análisis?"

## 6. Reducción de dimensionalidad (PCA + t-SNE) — el componente avanzado

**Por qué estas técnicas:** con 61 variables por evento no hay forma de inspeccionar
visualmente si los productos forman grupos naturales. Se combinaron PCA (lineal,
rápido, mide varianza retenida con un número exacto) y t-SNE (no lineal, revela
agrupamientos locales que PCA puede pasar por alto) porque son complementarias, no
intercambiables.

**Cómo se aplicaron:** `src/features.py` arma la matriz de 61 dimensiones
(nutrición + one-hot de categoría + TF-IDF del nombre de producto + hora/día,
escalada); `src/reduction.py` corre PCA completo (29/61 componentes retienen 90% de
varianza) y t-SNE sobre una muestra reproducible de 5,000 eventos.

**El resultado no es decorativo — es el hallazgo más importante del proyecto para
validar el enfoque completo del dashboard:** los productos se agrupan casi
perfectamente por categoría en el mapa PCA/t-SNE, y — verificado numéricamente con
`pd.crosstab(category_name, location)` — **`location` es una función determinista de
`category_name`** en este dataset (cada categoría vive en una sola ubicación física).
Esto significa que organizar el dashboard por "ubicación física" no fue una elección
arbitraria: es, estructuralmente, la variable que más separa a los datos. También
explica, desde los datos y no solo desde el conteo, por qué el Refrigerador concentra
el 97% de la pérdida — ahí vive la categoría más grande y perecible (Frutas y
Verduras, 20,481 de 25,819 eventos). Documentado completo en
`docs/componente_avanzado.md`.

**Limitación que hay que decir en voz alta si preguntan:** como ubicación ≡ categoría
en este dataset, no se puede aislar el efecto de "dónde se guarda" del efecto de "qué
tipo de alimento es" — un dataset real donde alguien guarde fruta en la despensa
permitiría desconfundir ambos efectos. Este proyecto no puede.

→ *Transición:* "Con esa validación de que la estructura del dashboard tiene respaldo
en los datos, pasamos al dashboard mismo."

## 7. Construcción del dashboard

Dos entregables paralelos con la misma narrativa: **Plotly/HTML**
(`tableau/Sem12_Dashboard_SmartKitchen.html`, generado por
`src/build_dashboard_html.py`) y **Tableau**
(`tableau/Sem12_Dashboard_SmartKitchen.twb`, generado por
`tableau/build_dashboard_twb.py`, 11 hojas + 3 dashboards). Estructura narrativa
(no solo una grilla de gráficos):

1. Hero — respuesta directa a la pregunta de investigación.
2. 4 KPIs comparativos (cada uno anclado a una referencia: % del gasto, multiplicador
   vs. la mejor ubicación — no números aislados sin contexto).
3. Contexto de gasto — benchmark de industria (PNUMA/ONU, FAO Perú) para dimensionar
   si la pérdida es alta, baja o típica.
4. Ranking por ubicación + impacto en salud (dónde se pierde el dinero / la salud).
5. Evolución temporal (longitudinal) + cruce ubicación × NutriScore (transversal).
6. Glosario NutriScore (qué es, cómo se calcula, cómo leer los colores).
7. Acciones prescriptivas por hogar.
8. Componente avanzado (PCA) — integrado como hallazgo, no como anexo aislado.
9. Sobre los datos — qué es el dataset, qué es `household_id`, universo de estudio,
   filtros aplicados.

Cada gráfico tiene un título descriptivo específico (no una frase de opinión) y un
callout de "Insight clave" separado — para que alguien sin contexto previo entienda
primero qué está viendo, y después la interpretación.

→ *Transición:* "Con el dashboard armado, ¿qué dice, en resumen?"

## 8. Insights

- El Refrigerador concentra 97% de la pérdida económica (S/ 37,568 de S/ 38,830).
- Tasa de desperdicio en Refrigerador: 37.5%, 9.1x más que Estante (4.1%).
- S/ 24,000 en frutas/verduras saludables (NutriScore A-B) se pierden en el
  Refrigerador — 45x más que en Despensa. El desperdicio no es "comida chatarra".
- Los productos salen del inventario, en promedio, 2.7 días **después** de vencer.
- 17.5% del gasto total en compras terminó perdido — casi idéntico al 17% que
  estima el PNUMA/ONU a nivel mundial de desperdicio de consumidor (2024).

## 9. Conclusiones

Responder "¿dónde se pierde el dinero y la salud?" con rigor exigió un pipeline
completo, no solo un gráfico: limpieza verificada por partida doble, modelado con
control explícito de fuga de datos, y una técnica de reducción de dimensionalidad que
terminó siendo la validación metodológica de todo el enfoque del dashboard (ubicación
≡ categoría). El hallazgo de esa redundancia es tan importante como los KPIs mismos:
evita atribuirle a "dónde se guarda" un efecto que en realidad pertenece a "qué se
guarda".

## 10. Recomendaciones de negocio

1. Priorizar el Refrigerador en cualquier intervención — ahí vive el 97% de la
   pérdida.
2. Adelantar la alerta de vencimiento a 3–5 días antes (ya prototipado como
   `rango_criticidad` en la capa Tableau), dado que hoy los productos salen ~2.7 días
   **después** de vencer.
3. No tratar "ubicación" y "categoría" como palancas de decisión independientes con
   este dataset — son la misma variable.

## 11. Trabajo futuro

- Reemplazar la simulación por datos reales de un piloto de hogares, para poder
  desconfundir ubicación de categoría.
- Extender el catálogo para incluir productos NutriScore E (ausentes en las 50
  referencias actuales) y así poblar el bucket "Riesgo (D-E)".
- Empaquetar el `.twb` como `.twbx` final en Tableau Desktop (pendiente manual, no
  ejecutable desde este entorno — ver `tableau/README.md`) y correr una verificación
  visual completa de filtros/parámetros en Tableau Desktop.
- Explorar una alerta operativa (no solo descriptiva) basada en `rango_criticidad`
  para consumo prioritario a 72 horas.

---

*Preguntas típicas de jurado y dónde está la respuesta lista:*
- *"¿Por qué simulado y no real?"* → §2, `docs/ethics_note.md`.
- *"¿Cómo saben que la limpieza es correcta?"* → §3, doble implementación verificada
  en `docs/QA_validation.md` §9.
- *"¿Por qué excluir `dias_para_vencer` del modelo si es tan útil?"* → §5, fuga de
  datos confirmada empíricamente.
- *"¿El PCA sirve para algo o es solo un requisito del curso?"* → §6 — sí, valida que
  ubicación ≡ categoría, la premisa estructural de todo el dashboard.
- *"¿Cómo saben que 17.5% de pérdida es mucho?"* → §7, benchmark PNUMA/ONU 2024 en el
  dashboard mismo.
