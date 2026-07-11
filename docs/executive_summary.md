# Resumen Ejecutivo — Smart Kitchen Intelligence (SKI)

**Curso:** 1ACC0211 · Data Visualization · NRC 18519 · UPC, 2026-I
**Equipo:** Arroyo Gamarra, Favio Enrique (u202220834) · Melgar Puertas, José Guillermo
(u202111660) · Reyna Alvarado, Gabriel Alonso (u202126097)
**Profesor:** Carlos Adrián Alarcón Delgado
**Entrega:** 6 — Proyecto Final y Defensa

---

## 1. Panorama del proyecto

Smart Kitchen Intelligence (SKI) es un producto de analítica visual que responde una
pregunta operativa concreta para cualquier hogar: **¿qué impacto tiene la ubicación
física donde se guarda un alimento (Refrigerador, Despensa, Estante) en cuánto dinero
y cuánta calidad nutricional se pierde por desperdicio?** El proyecto integra un
catálogo nutricional real (OpenFoodFacts, 50 productos) con un registro simulado —
pero calibrado con patrones reales de compra (Instacart) y reglas de vida útil (USDA
FoodKeeper) — de 25,819 movimientos de inventario en 10 hogares durante 90 días. El
resultado final es un dashboard interactivo (entregado en dos formatos: Plotly/HTML y
Tableau) más el pipeline Python reproducible que lo alimenta.

## 2. Problema de negocio

El desperdicio de alimentos en el hogar es un problema medible y prevenible, pero casi
ningún hogar tiene visibilidad agregada de sus propios patrones de compra, consumo y
pérdida. Sin esa visibilidad, las decisiones de compra semanal se toman a ciegas.
Trasladado a este caso de estudio: sobre S/ 222,270 en compras simuladas a lo largo de
90 días (10 hogares), **S/ 38,830 (17.5%) terminaron perdidos** — una cifra que, al
contrastarla con el 17% de desperdicio de alimentos a nivel de consumidor que estima
el PNUMA/ONU a nivel mundial (*Food Waste Index Report 2024*), resulta ser
prácticamente idéntica al patrón global, lo que da confianza en que la simulación es
una aproximación razonable a un problema real y no un artefacto arbitrario del
simulador.

## 3. Metodología

1. **Datos:** catálogo real (OpenFoodFacts) + movimientos simulados calibrados
   (`src/simulation.py`), con anomalías inyectadas deliberadamente para ejercitar el
   pipeline de limpieza (`src/anomaly_injection.py`).
2. **Limpieza y preparación:** 6 reglas de calidad verificables (P1–P6: outliers
   calóricos, homologación de categorías, integridad referencial, tipos explícitos,
   nulos estructurales de NutriScore, deduplicación), implementadas en
   `src/preprocessing.py` (Polars) y verificadas de forma independiente en
   `notebooks/02_limpieza.ipynb` (Pandas) — ambas implementaciones coinciden
   exactamente.
3. **Modelado predictivo:** Random Forest y Regresión Logística para clasificar
   eventos de salida como consumo vs. pérdida, con control explícito de fuga de datos
   (la variable `dias_para_vencer` se excluyó del entrenamiento tras confirmar que el
   simulador la usaba para asignar las etiquetas).
4. **Reducción de dimensionalidad (PCA + t-SNE):** sobre una matriz de 61
   características (nutrición, categoría, texto del nombre de producto, tiempo), para
   validar si la segmentación por ubicación física que organiza todo el dashboard
   refleja una estructura real de los datos. Resultado: sí — los productos se agrupan
   casi perfectamente por categoría, y en este dataset la ubicación es una función
   determinista de la categoría.
5. **Visualización:** dashboard narrativo (KPIs comparativos, ranking por ubicación,
   evolución temporal, cruce ubicación × NutriScore, acciones prescriptivas por
   hogar) entregado en Plotly/HTML y Tableau, con contexto de industria y un glosario
   de NutriScore para que sea legible sin conocimiento previo del proyecto.

## 4. Principales hallazgos

- **El Refrigerador concentra el 97% de la pérdida económica** (S/ 37,568 de
  S/ 38,830) — con una tasa de desperdicio de 37.5%, 9.1x más alta que el Estante
  (4.1%), la ubicación más eficiente.
- **La pérdida no es "comida chatarra"**: S/ 24,000 en frutas y verduras saludables
  (NutriScore A–B) se pierden en el Refrigerador — 45x más que en la Despensa. El
  desperdicio golpea justamente la parte más nutritiva de la compra.
- **Los productos, en promedio, salen del inventario 2.7 días después de vencer** —
  el problema no es solo cuánto se pierde, sino que se pierde después de ya no poder
  usarse, no antes.
- **La ubicación física, en este dataset, es estructuralmente equivalente a la
  categoría de producto** (hallazgo confirmado con PCA/t-SNE): Refrigerador =
  perecibles (frutas/verduras, lácteos, congelados), Estante = bebidas, Despensa =
  panadería y no perecibles. Esto valida organizar el dashboard por ubicación, y a la
  vez es una limitación metodológica importante a declarar (no se puede aislar
  "dónde se guarda" de "qué tipo de alimento es" con estos datos).

## 5. Valor de negocio

El dashboard convierte datos dispersos de inventario en 3 palancas de decisión
accionables por hogar: (1) qué ubicación revisar primero antes de comprar más, (2) qué
categorías reducir en el próximo ciclo de compras, y (3) qué sustituciones nutricionales
priorizar. El enfoque es replicable más allá de un hogar individual — a escala,
la misma lógica aplica a supermercados, bancos de alimentos o cadenas de retail que
necesiten priorizar dónde intervenir contra el desperdicio con el mayor impacto
económico y nutricional por unidad de esfuerzo.

## 6. Recomendaciones

1. **Priorizar el Refrigerador** en cualquier intervención de reducción de
   desperdicio — es donde vive el 97% de la pérdida económica y la mayoría de la
   pérdida nutricional.
2. **Adelantar la visibilidad de vencimiento**: dado que los productos salen ~2.7
   días después de vencer, una alerta a 3-5 días antes del vencimiento (ya prototipada
   como `rango_criticidad` en la capa de Tableau) tiene más margen de acción que
   revisar el inventario reactivamente.
3. **No tratar "ubicación" y "categoría" como palancas independientes** al diseñar
   intervenciones futuras — en este dataset son la misma variable; separarlas
   requeriría datos reales de hogares donde la ubicación de guardado varíe para un
   mismo tipo de producto.

## 7. Conclusiones finales

El proyecto demuestra que una pregunta de negocio aparentemente simple ("¿dónde se
pierde el dinero y la salud?") requiere, para responderse con rigor, un pipeline
completo de ingeniería de datos, validación estadística (PCA/t-SNE) y diseño de
visualización deliberado — no solo un gráfico. El hallazgo de que la ubicación física
es estructuralmente redundante con la categoría de producto es, en sí mismo, un
resultado de valor: evita que el equipo (o un usuario futuro del dashboard) le
atribuya a "dónde se guarda" un efecto causal que en realidad pertenece a "qué se
guarda". La comparación con el benchmark mundial de desperdicio (17.5% simulado vs.
17% real) es la pieza que conecta un ejercicio académico con una magnitud de negocio
verificable externamente.
