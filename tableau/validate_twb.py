"""Validacion estructural del .twb generado, sin necesitar Tableau Desktop.

Verifica:
- XML bien formado.
- Cada hoja referencia una fuente de datos que existe.
- Cada campo usado en filas/columnas/encodings de una hoja existe en las
  columnas reales declaradas de su fuente de datos.
- Cada zona de cada dashboard que referencia una hoja (`name=`) apunta a una
  hoja que existe.
- IDs de zona unicos dentro de cada dashboard.
- Zonas dentro de los limites del lienzo (x+w <= 100000, y+h <= 100000).

No sustituye abrir el archivo en Tableau Desktop (no se puede verificar
renderizado visual, tipos de marca, ni comportamiento de filtros/parametros
desde este entorno), pero atrapa la clase de error que impide que el archivo
abra (referencias rotas, campos inexistentes, XML invalido).
"""
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path

PATH = Path(__file__).resolve().parent / "Sem12_Dashboard_SmartKitchen.twb"


def main():
    try:
        tree = ET.parse(PATH)
    except ET.ParseError as e:
        print(f"XML PARSE ERROR: {e}")
        sys.exit(1)
    root = tree.getroot()
    print("XML bien formado: OK")

    ds_names, ds_columns = set(), {}
    for ds in root.find("./datasources").findall("./datasource"):
        name = ds.get("name")
        ds_names.add(name)
        cols = set()
        for rel in ds.findall(".//relation"):
            for col in rel.findall("./columns/column"):
                cols.add(col.get("name"))
        ds_columns[name] = cols

    ws_names = set(ws.get("name") for ws in root.findall("./worksheets/worksheet"))
    print(f"Fuentes de datos: {len(ds_names)} | Hojas: {len(ws_names)}")

    issues = []
    seen = set()
    for ws in root.findall("./worksheets/worksheet"):
        wsname = ws.get("name")
        for dsref in ws.findall(".//view/datasources/datasource"):
            dname = dsref.get("name")
            if dname not in ds_names:
                issues.append(f"{wsname}: referencia fuente de datos inexistente {dname}")
        blobs = []
        rows = ws.find(".//table/rows")
        cols = ws.find(".//table/cols")
        if rows is not None and rows.text:
            blobs.append(rows.text)
        if cols is not None and cols.text:
            blobs.append(cols.text)
        for enc in ws.findall(".//encodings/*"):
            c = enc.get("column")
            if c:
                blobs.append(c)
        for blob in blobs:
            for m in re.finditer(r"\[([^\]]+)\]\.\[([^\]]+)\]", blob):
                dsname, field = m.groups()
                parts = field.split(":")
                fieldname = parts[1] if len(parts) == 3 else (parts[0] if len(parts) == 1 else field)
                if fieldname in ("Measure Names", "Measure Values"):
                    continue
                key = (wsname, dsname, fieldname)
                if key in seen:
                    continue
                seen.add(key)
                if dsname in ds_columns and fieldname not in ds_columns[dsname]:
                    issues.append(f"{wsname}: campo '{fieldname}' NO existe en fuente {dsname}")

    for db in root.findall("./dashboards/dashboard"):
        dbname = db.get("name")
        ids = []
        for zone in db.findall(".//zone"):
            zname = zone.get("name")
            if zname and zname not in ws_names:
                issues.append(f"dashboard {dbname}: zona referencia hoja inexistente '{zname}'")
            zid = zone.get("id")
            if zid:
                ids.append(zid)
            x, y, w, h = (zone.get(k) for k in ("x", "y", "w", "h"))
            if all(v is not None for v in (x, y, w, h)):
                x, y, w, h = int(x), int(y), int(w), int(h)
                if x + w > 100000 or y + h > 100000 or x < 0 or y < 0:
                    issues.append(f"dashboard {dbname}: zona id={zid} fuera de lienzo (x={x} y={y} w={w} h={h})")
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            issues.append(f"dashboard {dbname}: ids de zona duplicados {dupes}")

    print()
    if issues:
        print(f"{len(issues)} PROBLEMA(S) ENCONTRADO(S):")
        for i in issues:
            print(" -", i)
        sys.exit(1)
    print("CLEAN: sin problemas de referencias/campos/ids/limites detectados.")


if __name__ == "__main__":
    main()
