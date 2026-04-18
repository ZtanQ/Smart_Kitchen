# Smart Kitchen Intelligence (SKI)

Proyecto integrador del curso de **Data Visualization** — UPC.

## Pregunta analítica

> ¿Qué categorías de productos y ubicaciones de almacenamiento concentran
> el mayor riesgo de desperdicio y los peores perfiles nutricionales, y
> cómo varía esa concentración en el tiempo?

## Usuario objetivo

Responsable de compras y planificación de comidas de un hogar de 2–4
personas, que consulta el dashboard semanalmente antes de hacer la lista
de compras.

## Producto final esperado

Dashboard en **Tableau** sustentado en un pipeline reproducible en
**Python**, que cruza el catálogo nutricional de OpenFoodFacts con un
registro de movimientos de cocina (entradas y salidas por ubicación).

## Estructura del repositorio

```text
proyecto-final/
├── data/
│   ├── raw/          # Catálogo (API) y movimientos (simulación)
│   ├── interim/      # Limpieza intermedia (Entrega 2+)
│   └── processed/    # Datos finales para Tableau
├── notebooks/        # Análisis por fase
├── outputs/          # CSVs exportados para Tableau
├── tableau/          # Workbooks .twbx
├── docs/             # Propuesta, diccionario, bitácora, ficha
├── src/              # ingestion.py, simulation.py, preprocessing.py
├── requirements.txt
└── README.md
```

## Fuentes de datos

| Capa | Origen | Licencia | Volumen actual |
|---|---|---|---|
| Catálogo | API OpenFoodFacts | ODbL | 50 productos × 7 variables |
| Movimientos | Simulación (`src/simulation.py`) | Interna | 1,000 eventos × 30 días |

El detalle de cobertura, limitaciones y estrategia de fallback está en
[`docs/source_inventory.md`](docs/source_inventory.md).

## Cómo reproducir

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/ingestion.py      # → data/raw/catalog_raw.csv
python src/simulation.py     # → data/raw/movements_raw.csv
jupyter notebook notebooks/01_perfilado.ipynb
```

Pasos completos en [`docs/runbook.md`](docs/runbook.md).

## Estado de entregas

- [x] **Entrega 1** — Propuesta del proyecto *(semana 3)*
- [ ] Entrega 2 — Perfilado, diccionario y limpieza inicial *(semana 5)*
- [ ] Entrega 3 — Análisis exploratorio y selección de gráficos *(semana 7)*
- [ ] Entrega 4 — Modelado, métricas y dashboard alpha *(semana 11)*
- [ ] Entrega 5 — Storytelling, accesibilidad y módulos temporal/transversal *(semana 13)*
- [ ] Entrega 6 — Trabajo final y defensa *(semana 15)*

## Documentación de la Entrega 1

- [Propuesta](docs/proposal.md) — pregunta, usuario, hipótesis, justificación, riesgos
- [Inventario de fuentes](docs/source_inventory.md)
- [Diccionario de datos preliminar](docs/data_dictionary.md)
- [Nota de ética](docs/ethics_note.md)
- [Runbook](docs/runbook.md)
