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

> **¿Qué categorías de productos y ubicaciones de almacenamiento concentran
> el mayor riesgo de desperdicio y los peores perfiles nutricionales, y cómo
> varía esa concentración en el tiempo?**

Es una pregunta analítica no trivial porque exige cruzar tres dimensiones
(categoría, ubicación, tiempo) con dos familias de métricas (rotación y
perfil nutricional), y porque la respuesta depende de segmentaciones que no
son evidentes en los datos crudos.

### Subpreguntas derivadas

1. ¿Qué combinaciones de categoría × ubicación tienen mayor tiempo promedio
   entre ingreso y consumo?
2. ¿Existe correlación entre el Nutriscore de un producto y su tasa de
   rotación?
3. ¿Cómo se distribuye el riesgo de vencimiento a lo largo del período
   observado?
4. ¿Qué perfiles de producto emergen al reducir el espacio nutricional con
   PCA o t-SNE, y se alinean con las categorías declaradas?

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

### Capa de catálogo — OpenFoodFacts

- Licencia: Open Database License (ODbL).
- Acceso: API pública, filtro por productos con alta popularidad.
- Estado actual: **50 productos** con 7 variables.
- Plan: enriquecer con grasas, grasas saturadas, azúcares, fibra, sal y
  sodio para alcanzar las **≥8 variables numéricas** que exige el componente
  avanzado PCA / t-SNE de la propuesta del curso.

### Capa de movimientos — simulación interna

- Origen: `src/simulation.py`.
- Estado actual: **1,000 eventos** en un rango de 30 días, balance ~39 %
  IN / ~61 % OUT, distribución uniforme entre 4 ubicaciones.
- Plan: subir a **≥2,500 eventos** para cumplir el mínimo de 2,000 registros
  exigido por la propuesta, y ampliar el rango temporal a 90 días para
  habilitar análisis longitudinal con mayor señal.

Detalle completo en `source_inventory.md`.

## 5. Hipótesis iniciales

| # | Hipótesis | Cómo se validará |
|---|---|---|
| H1 | Los productos de Nutriscore **D–E** (snacks, chocolates, bebidas azucaradas) concentran más movimientos **OUT** en términos absolutos que los A–B. | Comparación de frecuencia OUT por nutriscore. |
| H2 | La ubicación **Despensa** concentra la mayor tasa de productos con tiempo prolongado sin rotación. | Tiempo promedio IN→OUT por ubicación. |
| H3 | Existe un **patrón semanal** en los ingresos (picos concentrados en 1–2 días) frente a un consumo más distribuido. | Descomposición temporal de IN vs OUT por día de la semana. |
| H4 | Al reducir el espacio nutricional con PCA, los productos se agrupan por **perfil energético** (densidad calórica × macros) más que por la categoría textual declarada por OpenFoodFacts. | PCA sobre variables nutricionales normalizadas, comparación con categorías. |

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
