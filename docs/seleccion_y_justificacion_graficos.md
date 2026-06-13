# Selección y Justificación Técnica de Gráficos

**Proyecto:** Smart Kitchen Intelligence (SKI)  
**Curso:** Data Visualization (UPC)  
**Hito:** Sustentación Metodológica de la Capa Visual (Entrega 5)  

Este documento detalla la fundamentación científica, computacional y de negocio que justifica la arquitectura visual implementada en Tableau para el proyecto SKI. El diseño rechaza el uso de componentes cosméticos o redundantes, optimizando la decodificación cognitiva del usuario y maximizando la eficiencia del motor de renderizado VizQL sobre el modelo en estrella del repositorio.

---

## 1. Matriz de Justificación Técnica de Gráficos Seleccionados

Cada gráfico activo en el dashboard responde a la escala de medición de las variables y a los requisitos analíticos del problema:

### A. Tarjetas de KPI / BANs (Big Angry Numbers)
* **Variables:** `Costo de Pérdida` (Numérica continua), `% Desperdicio Global` (Proporcional derivada), `Total Transacciones` (Entero discreto).
* **Justificación Científica:** El escenario de uso prioritario del usuario exige una velocidad de respuesta menor a tres minutos antes de planificar las compras. Siguiendo el patrón de lectura en "Z", las tarjetas numéricas de alta escala eliminan la carga cognitiva de decodificar ejes cartesianos, proporcionando una respuesta inmediata sobre el estado macro financiero de la cocina doméstica sin requerir interactividad inicial.

### B. Gráfico de Líneas Dual con Ejes Sincronizados (Módulo Longitudinal)
* **Variables:** `Dim_Tiempo` (Temporal continua truncada a nivel diario), `action_type` (Categórica nominal binaria: `IN` / `OUT`), `Cantidad` (Numérica continua en kg/unidades).
* **Justificación Científica:** Basado en la jerarquía de percepción de Cleveland & McGill, la posición a lo largo de un escala común es el canal de mayor precisión para el cerebro humano. Al mapear una serie de tiempo longitudinal de 90 días, las líneas explotan el principio de continuidad de Gestalt. Sincronizar los ejes duales de ingresos (`IN` compras) y salidas (`OUT`) permite contrastar flujos de forma directa, permitiendo al usuario identificar de inmediato si el 70% de las entradas se concentra en fines de semana mientras el consumo es uniforme, validando directamente la hipótesis H3 del proyecto.

### C. Gráfico de Barras Horizontales Agrupadas (Módulo Transversal)
* **Variables:** `category_name` (Categórica nominal, 6 clases), `location` (Categórica nominal, 3 clases: Refrigerador, Despensa, Estante), `Métrica de Estancamiento / Pérdida Monetaria` (Numérica continua).
* **Justificación Científica:** Las categorías del catálogo poseen etiquetas de texto extensas (ej. "Lácteos y Refrigerados"). La orientación horizontal permite una lectura natural de izquierda a derecha sin truncar texto ni forzar rotaciones de ejes a 45° o 90° que ralentizan la interpretación. Al agrupar las barras horizontales por ubicación física (`location`) y codificarlas con color intencional, se resuelve en una sola vista la comparación transversal de qué zonas ciegas de la cocina (como el fondo de la despensa) concentran baja rotación y pérdida económica, resolviendo la subpregunta analítica N°1 del equipo.

### D. Gráfico de Frecuencias de Barras Ordenadas
* **Variables:** `nutriscore` (Categórica ordinal de jerarquía estricta: A, B, C, D, E), `Frecuencia de Salidas (OUT - Consumption)` (Métrica discreta de conteo).
* **Justificación Científica:** A diferencia de una variable cualitativa ordinaria, el Nutriscore posee un orden semántico intrínseco donde A es óptimo y E es crítico. El uso de barras alineadas horizontalmente respeta la secuencia natural A-B-C-D-E y mapea la longitud de la barra como canal de magnitud de alta precisión. Esto permite evaluar la asimetría de la distribución de consumo de forma instantánea para validar si los productos de peor perfil nutricional (D-E) presentan una frecuencia de consumo superior al 30% respecto a los saludables, atacando la hipótesis H1.

### E. Gráficos de Dispersión (Scatter Plots Cartesianos — Módulo Avanzado)
* **Variables:** Coordenadas latentes continuas extraídas en el pipeline de Python (`PC1`, `PC2`, `tsne_1`, `tsne_2`), `category_name` (Variable cualitativa de agrupación por color).
* **Justificación Científica:** El pipeline de Machine Learning reduce la matriz dimensional textual y nutricional de 61 dimensiones a componentes latentes continuos. Un diagrama de dispersión es mecánicamente el único espacio geométrico bidimensional capaz de proyectar estas coordenadas cartesianas abstractas. Al renderizar los 25,819 registros (o la muestra controlada de 5,000 para t-SNE), la proximidad espacial de los puntos explota la ley de cercanía de Gestalt, evidenciando ante el jurado si existen macro y micro clusters basados en densidad energética que se superponen o diferencian de las categorías comerciales, respondiendo la subpregunta analítica N°4 del proyecto.

### F. Diagrama de Pareto Combinado (Barras + Línea Acumulada — Módulo Avanzado)
* **Variables:** `Número de Componente de PCA` (Discreta ordinaria), `Varianza Explicada Individual` e `Inercia Acumulada` (Métricas porcentuales continuas).
* **Justificación Científica:** Es la pieza visual estándar en ciencia de datos para defender el criterio de truncamiento en técnicas de reducción de dimensionalidad. Las barras decrecientes demuestran la pérdida paulatina de varianza por componente, mientras que la línea de tendencia acumulada permite trazar de forma inequívoca el umbral del 90% de energía retenida. Esto justifica matemáticamente ante el jurado por qué el equipo seleccionó exactamente 29 de los 61 componentes efectivos.

---

## 2. Matriz de Gráficos Evaluados y Descartados (Requisito Curricular)

Para cumplir con la directiva explícita de la rúbrica de evaluación de la UPC, se documenta el descarte técnico de al menos dos alternativas visuales preliminares:

| Gráfico Descartado | Módulo Evaluado | Razón Técnica y Científica del Descarte | Alternativa de Reemplazo Implementada |
| :--- | :--- | :--- | :--- |
| **Gráfico de Torta (Pie Chart)** | Distribución del Volumen por Categorías | **Falla perceptual y sobrecarga cognitiva.** El ojo humano no posee la capacidad de decodificar ángulos o áreas con precisión. Al tener 6 categorías comerciales con proporciones transaccionales variables, los sectores angulares adyacentes causaban ambigüedad visual, requiriendo un exceso de etiquetas de texto independientes que saturaban el layout. | **Gráfico de Barras Horizontales Ordenadas.** Reemplazado por aprovechar la longitud alineada como canal de magnitud de máxima precisión perceptual. |
| **Scatter Plot de 61 Dimensiones** | Exploración Nutricional Multivariable | **Problema crítico de sobre-representación (*Overplotting*).** Intentar cruzar variables continuas nutricionales originales (`calories_100g`, `proteins_100g`, `carbs_100g`) directamente en un scatter plot convencional con 25,819 registros provocaba una masa densa y uniforme de puntos solapados que impedía identificar fronteras de comportamiento reales o patrones de hogares. | **Pipeline de Reducción con PCA + t-SNE.** Delegado al espacio latente avanzado para extraer componentes principales significativos antes de proyectar espacialmente en Tableau. |

---

## 3. Coherencia Arquitectónica con el Negocio

Las decisiones de diseño visual se integran directamente con el modelo relacional subyacente. Al evitar tablas planas y conectar las hojas analíticas mediante relaciones atómicas a través de `fact_inventory`, cada gráfico renderizado mediante VizQL ejecuta agregaciones limpias sobre la granularidad exacta del evento, garantizando que los cálculos de porcentaje de desperdicio y costo de pérdida económica no dupliquen registros de forma artificial ante el filtrado interactivo del usuario.