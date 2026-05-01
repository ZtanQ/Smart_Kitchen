# Propuesta del proyecto — Smart Kitchen Intelligence (SKI)

**Curso:** Data Visualization — UPC
**Entrega:** 1 (semana 3)
**Equipo:** *(por completar)*

---

## 1. Tema del proyecto

Analítica visual para la **gestión de alimentos en una cocina doméstica**,
con foco en la relación entre perfil nutricional de los productos, patrones
de uso por ubicación (refrigerador, estantería, despensa) y proximidad al
vencimiento.

El proyecto toma datos reales de productos desde la API de OpenFoodFacts
y los cruza con un registro simulado de entradas y salidas de cocina, para
construir un dashboard que permita observar qué se compra, qué se consume,
qué se queda estancado y qué perfil nutricional tiene el conjunto.

## 2. Pregunta analítica principal

> **¿Cómo evolucionan los puntos críticos de desperdicio y la calidad nutricional del inventario a lo largo de un trimestre, y qué impacto tiene la ubicación física en la pérdida económica y de salud del hogar?**

Esta pregunta es analíticamente compleja porque exige un **análisis longitudinal de 90 días** y un **análisis transversal por ubicación**, cruzando métricas de rotación con perfiles nutricionales (Nutriscore y densidad energética).

### Subpreguntas derivadas

1. ¿Qué combinaciones de categoría × ubicación generan el mayor tiempo de estancamiento (baja rotación)?
2. ¿Existe una correlación significativa entre los productos con peor Nutriscore (D-E) y una mayor frecuencia de consumo?
3. ¿Cuál es el costo de oportunidad acumulado por productos vencidos en ubicaciones de baja visibilidad (ej. "Caja" o fondo de "Despensa")?[cite: 9]
4. ¿Qué perfiles de productos emergen al reducir el espacio nutricional con **PCA o t-SNE** y cómo se comparan con las categorías comerciales?

## 3. Usuario objetivo y escenario de uso

**Usuario principal:** responsable de compras y planificación de comidas de
un hogar de 2 a 4 personas, con interés en reducir desperdicio y mejorar el
perfil nutricional del consumo.

**Escenario concreto de uso:** el usuario abre el dashboard una vez por
semana, antes de hacer la lista de compras. En menos de tres minutos debe
poder responder:

- ¿Qué categorías estoy comprando más de lo que consumo?
- ¿Qué ubicación concentra productos próximos a vencer?
- ¿Mi mix de compras se inclina hacia Nutriscore A–B o D–E?

**Decisión que apoya:** qué productos priorizar, reducir o sustituir en la
próxima compra, y qué consumir primero esta semana.

## 4. Fuente de datos propuesta

### Capa de catálogo — USDA FoodData Central
- **Origen:** API REST oficial de **USDA FoodData Central**, una fuente de datos abiertos del gobierno de EE. UU. enfocada en la transparencia alimentaria.
- **Estado:** 50 productos seleccionados con variables nutricionales completas (calorías, proteínas, carbohidratos, grasas)[cite: 9, 11].
- **Calidad:** Incluye registros con anomalías inyectadas intencionalmente (outliers y nulos) para validar la robustez de las reglas de limpieza en Python.

### Capa de movimientos — Simulación basada en Instacart
- **Patrones de comportamiento:** La simulación estocástica utiliza el dataset público anonimizado de **Instacart Online Grocery** para replicar distribuciones reales de compra y consumo.
- **Lógica de desperdicio:** La clasificación de alimentos descartados (`Waste`) se basa en los estándares técnicos de persistencia de la **USDA FoodKeeper App**.
- **Volumen verificado:** **25,444 registros** generados mediante UUIDs internos (garantizando la ausencia de Información de Identificación Personal o PII).
- **Temporalidad:** Rango de 90 días para permitir un análisis longitudinal profundo.

## 5. Hipótesis iniciales

| # | Hipótesis | Cómo se validará |
|---|---|---|
| H1 | **Preferencia de consumo:** Los productos con Nutriscore **D–E** (snacks, bebidas azucaradas) presentan una frecuencia de consumo (OUT) un 30% superior a los productos A–B. | Comparación de la frecuencia de eventos tipo `OUT` segmentada por grado de Nutriscore. |
| H2 | **Pérdida económica por ubicación:** La ubicación **Despensa** concentra el mayor volumen de desperdicio y la mayor pérdida monetaria acumulada debido a la baja rotación en comparación con el refrigerador. | Sumatoria del valor estimado (Precio × Cantidad) de los movimientos clasificados como `Expired` por ubicación física. |
| H3 | **Estacionalidad de flujo:** Existe un patrón semanal marcado donde el 70% de los ingresos (IN) ocurre en 1 o 2 días específicos, frente a un consumo (OUT) distribuido uniformemente. | Descomposición temporal de volúmenes de entrada y salida por día de la semana en el rango de 90 días. |
| H4 | **Agrupación Nutricional (PCA):** Al reducir el espacio nutricional, los productos se clasterizan por su **densidad energética** (macros × calorías) de forma más precisa que por su ID de categoría comercial. | Aplicación de PCA sobre variables normalizadas y comparación visual de clusters frente a la variable `category`. |

## 6. Justificación del valor del proyecto

El desperdicio alimentario en hogares es un problema medible y prevenible,
pero la mayoría de las personas no tiene visibilidad agregada de sus
propios patrones de consumo. Un dashboard que cruce rotación, ubicación y
perfil nutricional permite convertir datos dispersos en decisiones
semanales concretas, y sirve como prototipo replicable a escala
(cadenas de retail, bancos de alimentos, estudios de consumo).

Desde el punto de vista académico, el caso cumple los requisitos del
curso porque articula: (i) una pregunta analítica real, (ii) dos fuentes
de naturaleza distinta que exigen integración y perfilado, (iii)
dimensiones temporales y categóricas fuertes, y (iv) espacio numérico
suficiente para aplicar PCA o t-SNE de forma no cosmética.

## 7. Justificación de Tableau como herramienta

Tableau es adecuado para este caso por cuatro razones:

1. **Exploración interactiva.** El usuario objetivo necesita filtrar por
   categoría, ubicación y rango temporal de forma ágil, sin tocar código.
   Los filtros, parámetros y acciones de Tableau cubren ese requisito sin
   desarrollo custom.
2. **Modelo relacional estrella.** La estructura natural del proyecto
   (dimensión producto + hecho movimientos) se ajusta al modelo de
   *relationships* que Tableau resuelve bien sin pre-joinear.
3. **Visualización temporal y comparativa de primera clase.** Series,
   comparaciones transversales, mapas de calor y pequeños múltiplos
   están disponibles nativamente, lo que habilita los módulos
   longitudinal y transversal exigidos por la propuesta.
4. **Publicación y demo.** Tableau Public permite entregar el dashboard
   como pieza publicable, cumpliendo el criterio de "producto final
   presentable" de la Entrega 6.

Python queda como soporte de pipeline (perfilado, limpieza, cálculos
avanzados, PCA / t-SNE), no como capa de visualización final.

## 8. Riesgos iniciales de calidad y cobertura

| # | Riesgo | Evidencia | Mitigación prevista |
|---|---|---|---|
| R1 | **Categorías multiidioma y heterogéneas en el catálogo.** Un mismo producto (Nutella) aparece clasificado como `Snacks`, `Botanas`, `Breakfasts` y `Pâtes à tartiner au chocolat`. | Inspección directa del catálogo crudo (filas 7, 10, 18, 31, 50). | Homologación manual a una taxonomía propia de 6–10 categorías en Entrega 2. |
| R2 | **Outliers imposibles en variables nutricionales.** Al menos un registro reporta `calories_100g = 3833`, físicamente inviable (máximo teórico ≈ 900). | Fila 42 del catálogo crudo. | Regla de saneamiento con umbrales físicos documentada en bitácora. |
| R3 | **Volumen por debajo del mínimo curricular.** 50 productos y 1,000 eventos no alcanzan las 2,000 filas ni las 8 variables numéricas exigidas. | Perfilado inicial. | Enriquecimiento del catálogo con más nutrientes y re-simulación con ≥2,500 eventos antes de la Entrega 2. |
| R4 | **Movimientos son simulados, no reales.** Los patrones pueden no reflejar comportamiento humano (p. ej. consumo uniforme en lugar de picos de fin de semana). | Diseño del simulador actual. | Declarar explícitamente la naturaleza sintética en toda visualización; ajustar el simulador para introducir estacionalidad semanal plausible. |
| R5 | **Rango temporal corto (30 días).** Limita el análisis longitudinal y puede confundir ruido con tendencia. | Timestamps mín/máx. | Ampliar simulación a 90 días. |
| R6 | **Dependencia de API externa.** OpenFoodFacts puede devolver 5xx o limitar tasa. | Incidente 503 previo documentado. | Fallback local con dataset de emergencia ya implementado; congelar un snapshot de catálogo tras la Entrega 2. |
| R7 | **Ausencia de dimensión geográfica.** El dataset no permite análisis territorial natural. | Estructura de fuentes. | Sustituir la dimensión geográfica por la dimensión **ubicación dentro del hogar** como proxy de segmentación espacial. |

---

## Anexo — Cobertura de criterios de aprobación Entrega 1

| Criterio de la propuesta del curso | Sección | Estado |
|---|---|---|
| Pregunta analítica no descriptiva trivial | §2 | ✅ |
| Usuario objetivo claramente identificado | §3 | ✅ |
| Dataset con potencial para temporalidad, segmentación y comparación | §4 | ✅ |
| Justificación de por qué Tableau es adecuado | §7 | ✅ |
| Riesgos iniciales de calidad o cobertura identificados | §8 | ✅ |
