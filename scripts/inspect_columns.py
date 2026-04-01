"""
Task 4.5: Inspect raw column schemas BEFORE writing build_dataset.py mappings.
Prints shape, dtypes, sample values, and unique values for key string columns.
Run AFTER fetch_datasets.py succeeds.

Output: data/raw/column_report.txt
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from sources import SOURCES

REPORT_PATH = ROOT / "data/raw/column_report.txt"
MAX_UNIQUES = 20


def read_csv_guess(path: Path) -> tuple[pd.DataFrame, str]:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            frame = pd.read_csv(path, encoding=enc, sep=None, engine="python", nrows=5000)
            return frame, enc
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Could not decode {path}")


def inspect_csv(name: str, path: Path) -> dict:
    print(f"\n--- {name} ({path.name}) ---")
    try:
        df, enc = read_csv_guess(path)
    except Exception as exc:
        print(f"  ERROR reading: {exc}")
        return {"error": str(exc)}

    info = {
        "file": path.name,
        "encoding_used": enc,
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "sample": df.head(2).to_dict(orient="records"),
        "string_columns_uniques": {},
        "null_counts": df.isnull().sum().to_dict(),
    }

    for col in df.select_dtypes(include=["object", "string"]).columns:
        uniques = df[col].dropna().astype(str).unique().tolist()
        preview = uniques[:MAX_UNIQUES]
        if len(uniques) > MAX_UNIQUES:
            preview.append("...")
        info["string_columns_uniques"][col] = preview

    print(f"  shape:   {df.shape}")
    print(f"  columns: {list(df.columns)}")
    for col, vals in info["string_columns_uniques"].items():
        print(f"  {col}: {vals[:8]}")

    return info


def inspect_geo(name: str) -> dict:
    extract_dir = ROOT / "data/raw/barrios_geo"
    if not extract_dir.exists():
        return {"error": "ZIP not yet extracted"}

    candidates = (
        list(extract_dir.rglob("*.geojson"))
        + list(extract_dir.rglob("*.json"))
        + list(extract_dir.rglob("*.shp"))
    )
    info = {"files_found": [str(p.relative_to(ROOT)) for p in candidates]}

    for gf in [p for p in candidates if p.suffix in (".geojson", ".json")][:1]:
        try:
            data = json.loads(gf.read_text(encoding="utf-8"))
            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                info["geojson_property_keys"] = list(props.keys())
                info["sample_feature"] = props
                print(f"  GeoJSON properties: {list(props.keys())}")
        except Exception as exc:
            info["geojson_error"] = str(exc)

    return info


def main() -> None:
    print("=== inspect_columns.py ===")
    report = {}

    for name, source in SOURCES.items():
        path = ROOT / source["target"]
        if not path.exists():
            print(f"[missing] {name}: run fetch_datasets.py first")
            report[name] = {"error": "file not found"}
            continue

        if source["format"] == "zip":
            report[name] = inspect_geo(name)
        else:
            report[name] = inspect_csv(name, path)

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\n=== Report written to {REPORT_PATH} ===")
    print("Key things to verify:")
    print("  1. panel_indicadores: nombres exactos de cod_barrio, indicador_completo, valor_indicador")
    print("  2. zonas_verdes: resolucion barrio o solo distrito")
    print("  3. sivca_ruido_diario + sivca_estaciones: clave de join (nombre columna id estacion)")
    print("  4. barrios_geo: clave de barrio que coincide con panel_indicadores")


if __name__ == "__main__":
    main()
