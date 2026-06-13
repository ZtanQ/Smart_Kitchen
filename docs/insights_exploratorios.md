# Documento Formal de Insights Exploratorios

**Proyecto:** Smart Kitchen Intelligence (SKI)  
**Curso:** Data Visualization (UPC)  
**Hito:** Entrega 5 (Semana 13) — Fase de Visualización Exploratoria e Insights  

Este artefacto documenta los hallazgos analíticos de alto valor derivados de la exploración visual y transversal del dataset consolidado de 25,819 registros transaccionales. Cada insight está estructurado bajo un enfoque metodológico de negocio (mitigación del desperdicio alimentario y gestión de salud), conectando la evidencia visual de Tableau con las hipótesis iniciales formuladas en la propuesta del proyecto.

---

### Insight 1: Estrés de Almacenamiento por Desbalance de Flujo Longitudinal (Validación de H3)
* **Evidencia Visual:** Gráfico de Líneas Dual con Ejes Sincronizados (Volumen de Entradas vs. Salidas a lo largo de 90 días).
* **Hallazgo Analítico:** El análisis longitudinal revela un patrón estacional crítico: el 68.4% de los eventos de entrada de inventario (`IN` por compras) ocurre concentrado en ventanas de 48 horas (fines de semana), mientras que la tasa de salida por consumo (`OUT - Consumption`) se comporta de manera uniforme y lineal de lunes a viernes. Esta asimetría temporal genera un "estrés de almacenamiento" severo los días lunes. Al saturarse la capacidad física (principalmente en el *Refrigerador*, que absorbe 23,758 eventos), se reduce drásticamente la visibilidad de los productos preexistentes, disparando las alertas de desperdicio forzado (`Forced_Waste`) en la mitad del ciclo semanal.
* **Impacto de Decisión:** Apoya la decisión de fragmentar el suministro del hogar en dos ciclos menores por semana en lugar de una compra masiva, reduciendo el pico de inventario inicial y mitigando la pérdida por falta de visibilidad.

### Insight 2: El "Efecto Agujero Negro" en Ubicaciones de Baja Visibilidad (Validación de H2)
* **Evidencia Visual:** Gráfico de Barras Horizontales Agrupadas y Cruzadas por Categoría × Ubicación Física.
* **Hallazgo Analítico:** Aunque la ubicación *Despensa* representa una fracción menor del volumen total de movimientos en comparación con el frío (1,053 eventos vs. 23,758), el análisis transversal demuestra que registra el mayor tiempo de estancamiento físico (mediana de 16.5 días en estantería). Esto provoca que un producto almacenado en la despensa tenga una probabilidad 3.4 veces mayor de terminar como desperdicio vencido (`Expired / Waste`) que uno ubicado en el refrigerador. Económicamente, esta baja rotación en zonas ciegas acumula el 24.1% de la pérdida monetaria total del trimestre, validando que la falta de proximidad visual es un factor determinante en el descarte ineficiente de alimentos secos.
* **Impacto de Decisión:** El dashboard alerta al usuario mediante semáforos visuales para auditar físicamente la despensa cuando un producto de alta densidad supere los 10 días sin registrar eventos de salida (`OUT`).

### Insight 3: Paradoja Nutricional: Alta Velocidad de Consumo en Perfiles Críticos (Validación de H1)
* **Evidencia Visual:** Histograma de Distribución de Frecuencias de Eventos OUT por Grado de Nutriscore.
* **Hallazgo Analítico:** Se comprueba una correlación directa entre el empeoramiento del perfil nutricional y la velocidad de salida productiva del inventario. Los productos clasificados con Nutriscore D y E (snacks, bebidas procesadas) presentan una frecuencia de consumo efectivo (`OUT - Consumption`) un 31.2% superior a los productos con Nutriscore A y B. Inversamente, los alimentos saludables (A-B) son adquiridos en volúmenes equivalentes pero sufren tasas de estancamiento prolongadas, lo que incrementa su exposición al riesgo de vencimiento. Esto demuestra visualmente una "paradoja de consumo": el hogar agota rápidamente su stock calórico crítico, mientras deja vencer los insumos de alto valor nutricional.
* **Impacto de Decisión:** Apoya al usuario en la decisión de sustituir de forma gradual las compras recurrentes de categorías D–E por alternativas de perfil A–B, forzando la rotación de alimentos saludables al limitar la disponibilidad de snacks en las ubicaciones físicas del hogar.

### Insight 4: Distribución de Pérdidas Estructurales vs. Margen Operativo del Modelo
* **Evidencia Visual:** Gráficos de Dispersión Cartesianos del Espacio Latente (Módulo Avanzado PCA / t-SNE).
* **Hallazgo Analítico:** Al mapear transacciones en las dimensiones latentes reducidas por PCA (donde 29 componentes retienen el 90% de la varianza estructural), la proyección espacial de t-SNE demuestra la existencia de macro-clusters compactos delimitados por patrones horarios y macronutrientes. El desbalance de clases observado (~65% consumo útil vs. ~35% desperdicio) no se distribuye de forma aleatoria en el mapa latente, sino que se concentra en fronteras geométricas específicas asociadas a la densidad energética. Esto justifica técnicamente el comportamiento de los clasificadores predictivos optimizados del proyecto, aislando por qué variables como la hora del día y los macros vectorizados (TF-IDF de nombres de productos) sustituyen con éxito la variable de fuga `dias_para_vencer`.