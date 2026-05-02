import requests
import pandas as pd
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

def fetch_from_openfoodfacts(product_name):
    """Consulta OpenFoodFacts API para obtener nutrición real."""
    # Limpiamos el nombre para mejorar la búsqueda
    clean_query = product_name.replace("Organic", "").replace("organic", "").strip()

    # OpenFoodFacts utiliza búsqueda en URL
    url = f"https://world.openfoodfacts.org/api/v0/product_name_search.json"
    params = {
        "search_terms": clean_query,
        "page_size": 1,
        "json": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])

            if products:
                product = products[0]

                # Extraer nutrientes de OpenFoodFacts
                # Buscar en nutriments (por 100g)
                nutrients = product.get('nutriments', {})

                res = {
                    'calories_100g': nutrients.get('energy-kcal_100g') or nutrients.get('energy_100g'),
                    'proteins_100g': nutrients.get('proteins_100g'),
                    'carbs_100g': nutrients.get('carbohydrates_100g'),
                    'fat_100g': nutrients.get('fat_100g'),
                    'fiber_100g': nutrients.get('fiber_100g'),
                    'nutriscore_grade': product.get('nutriscore_grade', 'E').upper()
                }

                # Filtrar None values
                return {k: v for k, v in res.items() if v is not None}
    except Exception as e:
        print(f"⚠️ Error consultando OpenFoodFacts para '{clean_query}': {str(e)}")
        pass

    return None

def build_catalog_from_movements():
    print("1. Analizando movimientos y recuperando nombres desde patrones...")

    # Cargar movimientos (solo tienen IDs)
    movements_path = "data/raw/movements_raw.csv"
    if not os.path.exists(movements_path):
        raise FileNotFoundError("Ejecuta simulation.py primero.")

    movements = pd.read_csv(movements_path)
    unique_ids = movements['product_id'].unique()

    # Cargar patrones para recuperar el nombre (mapeo ID -> Nombre)
    patterns_path = "data/raw/instacart_patterns.json"
    if not os.path.exists(patterns_path):
        raise FileNotFoundError("Falta archivo de patrones.")

    with open(patterns_path, "r") as f:
        patterns = json.load(f)

    # Crear un diccionario de búsqueda rápida {id: nombre, dept}
    id_to_name = {p['product_id']: p['product_name'] for p in patterns['top_50_productos']}
    id_to_dept = {p['product_id']: p['department_id'] for p in patterns['top_50_productos']}

    print(f"Detectados {len(unique_ids)} productos únicos. Consultando OpenFoodFacts API...")

    catalog_list = []
    success_count = 0

    for i, p_id in enumerate(unique_ids, 1):
        p_name = id_to_name.get(p_id, "Unknown Product")
        p_dept = id_to_dept.get(p_id, 0)

        print(f"[{i}/{len(unique_ids)}] Buscando: {p_name} (ID: {p_id})...")
        openfoodfacts_data = fetch_from_openfoodfacts(p_name)

        if openfoodfacts_data:
            openfoodfacts_data.update({
                "product_id": p_id,
                "product_name": p_name,
                "category": p_dept
            })
            catalog_list.append(openfoodfacts_data)
            success_count += 1
        else:
            # Fallback: registro con datos faltantes (será limpiado después)
            catalog_list.append({
                "product_id": p_id,
                "product_name": p_name,
                "category": p_dept,
                "calories_100g": None,
                "proteins_100g": None,
                "carbs_100g": None,
               