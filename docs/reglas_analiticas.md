# Documento de Reglas de Métricas, Segmentos y Parámetros Analíticos

**Proyecto:** Smart Kitchen Intelligence (SKI)  
**Curso:** Data Visualization (UPC)  
**Hito:** Entrega 4 — Semana 11  

Este documento constituye el artefacto metodológico oficial del proyecto SKI. Su propósito es formalizar las reglas de negocio, ecuaciones matemáticas, criterios de segmentación y la lógica analítica implementada sobre el dataset procesado (25,819 registros) para su consumo directo en Tableau Desktop, garantizando la consistencia de las agregaciones y la reproducibilidad del dashboard.

---

## 1. Estructura Analítica Relacional y Control de Duplicados

Para cumplir con los criterios mínimos de aprobación del hito, el equipo define una arquitectura basada en un **Modelo en Estrella (Star Schema)** implementado mediante el motor de **Relaciones Lógicas (Relationships / VizQL)** de Tableau, en lugar de joins físicos a nivel de base de datos.

* **Tabla de Hechos Central (`fact_inventory`):** Contiene 25,819 registros transaccionales que representan los movimientos de inventario (`IN` / `OUT`). Su granularidad es el evento transaccional único por timestamp.
* **Tablas de Dimensiones Atómicas:**
    * `Dim_Producto`: 50 productos únicos con sus atributos nutricionales indexados por `product_id`.
    * `Dim_Hogar`: 10 hogares independientes indexados por `household_id`.
    * `Dim_Tiempo`: Grano diario para los 90 días cronológicos de la simulación.

### Mecanismo de Control de Duplicidad:
Al mapear estas tablas mediante relaciones lógicas en Tableau (utilizando las llaves `product_id` y `household_id`), el motor VizQL genera consultas SQL dinámicas que se ejecutan al nivel de detalle adecuado de la visualización (*Contextual Granularity*). Esto garantiza que al calcular promedios nutricionales (ej. proteínas o calorías promedio por producto) o sumatorias transaccionales de volumen (`quantity`), Tableau **no duplique de forma artificial los valores del catálogo**, eliminando el sesgo clásico de los joins físicos desnormalizados.

---

## 2. Reglas Técnicas de Métricas Derivadas

Se han estructurado dos métricas analíticas derivadas fundamentales en la fuente procesada para responder a las preguntas de negocio del proyecto:

### A. Métrica de Proximidad al Vencimiento (`dias_para_vencer`)
* **Objetivo:** Determinar la ventana de vida útil remanente de un producto en el momento exacto de una transacción.
* **Regla de Cálculo (Computada en Python / Polars):**
    $$dias\_para\_vencer = \text{expiry\_date} - \text{timestamp}$$
* **Unidad de Medida:** Días enteros (Integer).
* **Lógica de Interpretación:** * $dias\_para\_vencer > 0$: El producto está fresco y apto para el consumo seguro.
    * $dias\_para\_vencer \le 0$: El producto ha alcanzado su fecha de caducidad. Si el registro coincide con una salida ineficiente (`classification` ∈ {`Waste`, `Forced_Waste`}), se contabiliza como merma real.

### B. Métrica de Impacto Financiero de Pérdida (`costo_perdida`)
* **Objetivo:** Cuantificar monetariamente el impacto del desperdicio alimentario por ubicación.
* **Regla de Cálculo (Campo Calculado en Tableau):**
    ```excel
    IF [classification] = "Waste" OR [classification] = "Forced_Waste" THEN [quantity] * [estimated_price] ELSE 0 END
    ```
* **Unidad de Medida:** Unidad monetaria continua (Float).
* **Lógica de Interpretación:** Aisla los eventos donde el alimento no fue consumido productivamente y calcula el costo hundido. Permite al usuario identificar qué zonas físicas (ej. fondo de despensa) acumulan mayor pérdida económica.

---

## 3. Estrategia de Segmentación Operativa y Técnica

Para permitir un análisis granular sin añadir ruido algebraico a las pantallas de Tableau, se establecen dos niveles de segmentación:

### A. Segmento Técnico: Núcleo Familiar (`household_id`)
* **Criterio:** Variable categórica nominal discreta que fragmenta el volumen transaccional en 10 subconjuntos independientes (IDs del 0 al 9).
* **Propósito Analítico:** Funciona como el eje de control transversal. Permite al jurado evaluar cómo se comportan las tasas de desperdicio entre hogares con diferentes hábitos de compra, aislando los patrones estocásticos de una familia respecto a las demás.

### B. Segmento Operacional: Rango de Criticidad de Inventario (`rango_criticidad`)
* **Criterio:** Clasificación ordinal condicional calculada a partir de la métrica de proximidad.
* **Lógica de Negocio (Expresada en sintaxis de Tableau):**
    ```excel
    IF [dias_para_vencer] <= 0 THEN "Crítico (Vencido)"
    ELSEIF [dias_para_vencer] > 0 AND [dias_para_vencer] <= 3 THEN "Alerta (Consumo Prioritario)"
    ELSE "Seguro (Estable)"
    END
    ```
* **Propósito Analítico:** Alimenta los mapas de color condicionales (semáforos analíticos) en el dashboard, permitiendo al responsable de la cocina priorizar el consumo de la ventana de las próximas 72 horas.

---

## 4. Parámetros y Lógica Analítica Interactiva

### A. Parámetro de Selección Dinámica de Control (`Param_Hogar`)
* **Configuración:** Parámetro de tipo entero en Tableau que toma como lista de valores admitidos el rango del segmento `household_id` (0 a 9).
* **Lógica Analítica:** Al ser accionado por el usuario en la interfaz web, propaga un filtro global síncrono que recalcula las tasas de consumo útil vs. descarte en las 8 hojas analíticas del dashboard de forma nativa a través del motor VizQL.

### B. Lógica de Aislamiento de Leakage (Fuga de Datos)
* **Regla de Control de Calidad:** La variable `dias_para_vencer` y el segmento `rango_criticidad` se declaran como **exclusivos de la capa de visualización y monitoreo operativo de Tableau**. 
* **Justificación:** Se aislaron por completo del pipeline de entrenamiento de los modelos predictivos de Machine Learning (Entrega 3) debido a que introducían un sesgo artificial perfecto ($F1 = 1.0$) al ser la variable con la que el simulador determinaba las etiquetas. Su presencia en Tableau es estrictamente analítica para la toma de decisiones del usuario final, garantizando la honestidad científica del proyecto.