# Runbook — SKI

Guía para reproducir el estado del proyecto en la Entrega 1.

## 1. Configuración del entorno

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .\.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## 2. Ingesta del catálogo

```bash
python src/ingestion.py
```

Descarga productos desde la API de OpenFoodFacts y genera
`data/raw/catalog_raw.csv`. Ante errores 5xx o timeouts, cae
automáticamente al catálogo de emergencia.

## 3. Simulación de movimientos

```bash
python src/simulation.py
```

Lee el catálogo generado en el paso anterior y produce
`data/raw/movements_raw.csv` con eventos simulados IN/OUT
distribuidos entre las cuatro ubicaciones.

## 4. Perfilado inicial

```bash
jupyter notebook notebooks/01_perfilado.ipynb
```

Carga ambos CSV, verifica volúmenes, integridad referencial
básica y produce las cifras reportadas en `data_dictionary.md`.

## 5. Próximos pasos (Entrega 2)

- Enriquecer el catálogo con nutrientes adicionales.
- Ampliar la simulación a 90 días y ≥2,500 eventos.
- Perfilado formal completo y limpieza documentada en `changelog_data.md`.
