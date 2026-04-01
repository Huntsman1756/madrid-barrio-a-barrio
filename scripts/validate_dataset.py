"""
Validates data/processed/barrios-madrid.json against the schema contract.
Run after build_dataset.py succeeds.
Exit code 0 = PASS, 1 = FAIL.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITERIA = ["socioeconomico", "transporte", "verde", "ruido", "equipamientos", "salud"]
MIN_BARRIOS = 128


def check(condition: bool, message: str) -> bool:
    if not condition:
        print(f"  FAIL: {message}")
    return condition


def main() -> None:
    path = ROOT / "data/processed/barrios-madrid.json"
    if not path.exists():
        print("FAIL: barrios-madrid.json no encontrado. Ejecuta build_dataset.py primero.")
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    barrios = data.get("barrios", [])
    meta = data.get("meta", {})
    failures = 0

    print("=== validate_dataset.py ===")
    print(f"  total barrios: {len(barrios)}")
    print(f"  meta keys: {list(meta.keys())}")

    if not check(len(barrios) >= MIN_BARRIOS, f"esperados >= {MIN_BARRIOS}, hay {len(barrios)}"):
        failures += 1
    if not check("madrid_means" in meta, "meta.madrid_means ausente"):
        failures += 1
    if not check(set(meta.get("madrid_means", {}).keys()) == set(CRITERIA), "claves de madrid_means no coinciden con criterios"):
        failures += 1

    for barrio in barrios:
        bid = barrio.get("id", "?")
        if not check("district" in barrio and barrio["district"], f"{bid}: district ausente"):
            failures += 1

        values = barrio.get("values", {})
        if not check(set(values.keys()) == set(CRITERIA), f"{bid}: claves de values incorrectas"):
            failures += 1
        for key in CRITERIA:
            value = values.get(key)
            if value is not None and not check(0.0 <= value <= 10.0, f"{bid}: {key}={value} fuera de [0,10]"):
                failures += 1

        crit_list = barrio.get("criteria", [])
        if not check(len(crit_list) == len(CRITERIA), f"{bid}: criteria tiene {len(crit_list)} items"):
            failures += 1
        for item in crit_list:
            if not check("delta_vs_mean" in item, f"{bid}: delta_vs_mean ausente"):
                failures += 1

        if not check(set(barrio.get("sources", {}).keys()) == set(CRITERIA), f"{bid}: claves de sources incorrectas"):
            failures += 1

        if barrio.get("lat") is None:
            print(f"  WARN: {bid} ({barrio.get('name', '?')}): sin centroide lat")

    if failures:
        print(f"\nFAIL: {failures} comprobacion(es) fallida(s).")
        sys.exit(1)

    print(f"\nPASS: {len(barrios)} barrios validados.")


if __name__ == "__main__":
    main()
