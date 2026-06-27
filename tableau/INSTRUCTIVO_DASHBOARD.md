# Instructivo Tableau Desktop — Smart Kitchen Intelligence

Tiempo estimado: **15-20 min**. El `.twb` ya trae las 8 conexiones de datos listas. Solo construyes las hojas y el dashboard.

## 0. Iniciar Tableau desde cero (workbook nuevo)

> **Importante:** NO abrir el `Sem12_Dashboard_SmartKitchen.twb` actual — está dañado por intentos previos de generarlo programáticamente. Vamos a construir uno nuevo desde Tableau Desktop, que es la única vía confiable.

1. Abre **Tableau Desktop** sin archivo (icono del programa, no doble clic en .twb).
2. En la pantalla de inicio, sección "Conectar" → **Archivo de texto** → navega a `C:\Users\gabri\Documents\Upc\Data Visualization\proyecto-final\tableau\datos_finales\` y selecciona **`kpi_por_hogar.csv`**. Tableau crea automáticamente el workbook nuevo con esa conexión.
3. Para agregar las otras fuentes: menú **Datos → Nueva fuente de datos** → Archivo de texto → repite con cada uno de estos:
   - `agg_temporal_ubicacion.csv`
   - `agg_ubicacion_nutriscore.csv`
   - `insights_prescriptivos.csv`
   - `fact_con_precio.csv`
   - Desde `..\..\outputs\`: `tsne_sample_tableau.csv`, `pca_components_tableau.csv`, `pca_variance_table.csv`
4. Verifica en el panel izquierdo que aparecen las 8 fuentes.
5. Guarda inmediatamente como **`Sem12_Dashboard_SmartKitchen.twb`** en `tableau/` (sobrescribe el actual roto). Menú **Archivo → Guardar como**.

## 1. Los 4 BANs (KPIs)

Selecciona la fuente **`kpi_por_hogar`** en el panel izquierdo. Crea 4 hojas nuevas (clic derecho en pestaña inferior → Nueva hoja). Repite este patrón:

| Hoja | Campo a Texto | Agregación | Formato (clic derecho píldora → Formato → Números) |
|---|---|---|---|
| `BAN1 - Mermas` | `kpi1_costo_perdido_soles` | SUMA | Moneda personalizada: prefijo `S/ `, 0 decimales |
| `BAN2 - Desperdicio` | `kpi2_tasa_desperdicio` | PROMEDIO | Porcentaje, 1 decimal |
| `BAN3 - Nutriscore` | `kpi3_pct_nutriscore_DE` | PROMEDIO | Porcentaje, 1 decimal |
| `BAN4 - Días` | `kpi4_dias_prom_vencer` | PROMEDIO | Personalizado: `0.0" días"` |

En cada hoja: marca **Texto**, arrastra el campo a Texto, aumenta tamaño a 48pt, negrita. Apaga el título de hoja (`Hoja de trabajo → Mostrar título`).

## 2. Hoja Longitudinal — Evolución Temporal por Ubicación

Fuente: **`agg_temporal_ubicacion`**. Nueva hoja `Longitudinal`.

- **Columnas**: `Semana Iso`
- **Filas**: `Costo Perdido` (SUMA)
- **Color** (panel Marcas): `Location`
- Marca: Línea
- Título: *"¿Cuándo y dónde se pierde dinero?"*

## 3. Hoja Transversal — Ubicación × Nutriscore

Fuente: **`agg_ubicacion_nutriscore`**. Nueva hoja `Transversal`.

- **Filas**: `Location`, luego `Tipo Salida`
- **Columnas**: `Eventos` (SUMA)
- **Color**: `Nutriscore Grupo` (paleta semáforo: A-B verde, C ámbar, D-E rojo)
- Marca: Barra
- Título: *"¿Qué calidad nutricional se pierde por ubicación?"*

## 4. Hoja Insights Prescriptivos

Fuente: **`insights_prescriptivos`**. Nueva hoja `Insights`.

- **Filas**: `Eje`, luego `Titulo`
- **Texto** (Marcas): `Mensaje`
- Marca: Texto
- Habilita "Justificar texto en celdas".

## 5. Hoja KPIs por Hogar (tabla)

Fuente: **`kpi_por_hogar`**. Nueva hoja `Tabla por Hogar`.

- **Filas**: `Household Id`, `Segmento Hogar`
- **Columnas**: `Measure Names`
- **Texto**: `Measure Values`
- Arrastra a "Measure Values" solo los 4 kpi fields (`kpi1...`, `kpi2...`, `kpi3...`, `kpi4...`).
- Formato: aplica a cada Measure el formato correspondiente (S/, %, días).

## 6. Hojas del Anexo (PCA / t-SNE)

Solo si quieres mantener el componente metodológico exigido por la rúbrica:

- Fuente `tsne_sample_tableau`: nueva hoja `Clusters t-SNE`. Cols=`tsne_1`, Filas=`tsne_2`, Color=`Location`, Marca=Forma.
- Fuente `pca_components_tableau`: nueva hoja `Mapa PCA`. Cols=`PC1`, Filas=`PC2`, Color=`Location`, Marca=Forma.
- Fuente `pca_variance_table`: nueva hoja `Energia PCA`. Cols=`Componente`, Filas=`Varianza Acumulada`, Marca=Barra.

## 7. Dashboard Principal — Smart Kitchen Intelligence

Menú **Dashboard → Nuevo Dashboard**. Tamaño: **Personalizado 1500×1000**. Mantén modo **Mosaico** (no Flotante).

### Banda 1 — Cabecera
Arrastra un **Objeto Texto** arriba (alto ~60px), fondo azul oscuro `#1d2b4f`, escribe:
> **SMART KITCHEN INTELLIGENCE (SKI)**
> *Pregunta: ¿Qué impacto tiene la ubicación física en la pérdida económica y de salud del hogar?  —  10 hogares, 90 días, 25,819 eventos.*

### Banda 2 — 4 BANs en fila
Arrastra `BAN1`, `BAN2`, `BAN3`, `BAN4` en una fila horizontal debajo del título. Aplica fondos semáforo:
- BAN1 fondo `#fde2e2` (rojo claro)
- BAN2 fondo `#fce7c8` (ámbar)
- BAN3 fondo `#fff5cc` (amarillo)
- BAN4 fondo `#d6e9d6` (verde)

### Banda 3 — Longitudinal + Insights
En la siguiente fila, arrastra `Longitudinal` ocupando 70% del ancho izquierdo. A su derecha (30%), arrastra `Insights`.

### Banda 4 — Transversal + Tabla
Última fila: `Transversal` 70% izquierda, `Tabla por Hogar` 30% derecha.

### Filtro global
Clic derecho en `Household Id` dentro del `Longitudinal` → **Mostrar filtro**. Luego sobre el filtro que apareció → **Aplicar a hojas de trabajo → Todas las que usen esta fuente de datos**. Repite el procedimiento desde `Transversal` y desde `Insights` para cubrir las 3 fuentes.

### Footer
Texto al final del dashboard:
> *Fuente: pipeline reproducible Smart Kitchen (Python + Tableau). Cobertura 2026-W06 a 2026-W17. UPC | Data Visualization.*

## 8. Dashboard Anexo (opcional)

Nuevo Dashboard `Anexo Metodológico`. Tamaño 1500×900. Arrastra `Mapa PCA`, `Clusters t-SNE`, `Energia PCA` (50%/50% arriba, 100% abajo) con texto explicativo: *"Soporte técnico exigido por la cátedra. NO responde la pregunta de negocio del dashboard principal."*

## 9. Ocultar hojas componentes

Cuando todo funcione: clic derecho en cada pestaña componente (`BAN1`, `BAN2`, `BAN3`, `BAN4`, `Longitudinal`, `Transversal`, `Insights`, `Tabla por Hogar`, `Clusters t-SNE`, `Mapa PCA`, `Energia PCA`) → **Ocultar hoja**. Solo deben quedar visibles los 2 dashboards.

## 10. Guardar

`Archivo → Guardar` (sobrescribe `Sem12_Dashboard_SmartKitchen.twb`). Para entrega: `Archivo → Exportar como archivo empaquetado` → `Sem12_Dashboard_SmartKitchen.twbx` (incluye todos los CSVs y se puede compartir como un solo archivo).

## 11. Historia (3-5 pantallas)

Menú **Historia → Nueva Historia**. Arrastra:
1. Dashboard `Smart Kitchen Intelligence` — subtítulo: *"Contexto general"*
2. Hoja `Longitudinal` — subtítulo: *"S/ 37,568 acumulados en el Refrigerador"*
3. Hoja `Transversal` — subtítulo: *"19.3% del desperdicio es Nutriscore D-E"*
4. Hoja `Tabla por Hogar` — subtítulo: *"−2.7 días al OUT: se vencen antes de salir"*
5. Hoja `Insights` — subtítulo: *"Acciones prescriptivas por hogar"*
