"""
Transforms raw downloaded files -> data/processed/barrios-madrid.json

Run order:
1. python scripts/fetch_datasets.py
2. python scripts/inspect_columns.py
3. python scripts/build_dataset.py
4. python scripts/validate_dataset.py
"""

import json
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL_TARGET_YEAR = 2025
CRITERIA_KEYS = ["socioeconomico", "transporte", "verde", "ruido", "equipamientos", "salud"]


def normalize_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    text = text.replace("-", " ").replace("/", " ")
    return " ".join(text.split())


def normalize_code(value) -> str | None:
    if value is None or pd.isna(value):
        return None
    digits = "".join(char for char in str(value) if char.isdigit())
    if not digits:
        return None
    return digits.zfill(3)


def normalize_station_id(value) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().upper()
    if text.startswith("RF-"):
        suffix = "".join(char for char in text[3:] if char.isdigit())
        return f"RF-{suffix.zfill(2)}" if suffix else text
    digits = "".join(char for char in text if char.isdigit())
    if not digits:
        return text
    return f"RF-{digits.zfill(2)}"


def parse_es_number(value):
    if value is None or pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)
    text = str(value).strip()
    if not text:
        return np.nan
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return np.nan


def read_csv_guess(path: Path, dtype: dict | None = None) -> pd.DataFrame:
    last_exc = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return pd.read_csv(path, encoding=enc, sep=None, engine="python", dtype=dtype)
        except UnicodeDecodeError as exc:
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Could not read {path}")


def resolve_column(df: pd.DataFrame, *candidates: str) -> str:
    normalized = {normalize_text(col): col for col in df.columns}
    for candidate in candidates:
        key = normalize_text(candidate)
        if key in normalized:
            return normalized[key]
    raise KeyError(f"Missing expected column. Candidates={candidates}. Available={list(df.columns)}")


def latest_year(df: pd.DataFrame, year_col: str, target_year: int) -> int:
    years = sorted(pd.to_numeric(df[year_col], errors="coerce").dropna().astype(int).unique().tolist(), reverse=True)
    if not years:
        raise ValueError("No valid years found in panel dataset")
    return target_year if target_year in years else years[0]


def extract_indicator(panel: pd.DataFrame, year_col: str, indicator_col: str, value_col: str, match_text: str) -> tuple[pd.DataFrame, int | None]:
    key = normalize_text(match_text)
    subset = panel[panel["indicator_key"] == key].copy()
    if subset.empty:
        return subset, None
    years = sorted(pd.to_numeric(subset[year_col], errors="coerce").dropna().astype(int).unique().tolist(), reverse=True)
    best_year = years[0] if years else None
    if best_year is not None:
        subset = subset[pd.to_numeric(subset[year_col], errors="coerce").astype("Int64") == best_year].copy()
    subset["indicator_value"] = pd.to_numeric(subset[value_col].map(parse_es_number), errors="coerce")
    return subset, best_year


def load_panel(path: Path, year: int) -> tuple[pd.DataFrame, dict]:
    panel = read_csv_guess(path)
    barrio_code_col = resolve_column(panel, "cod_barrio")
    barrio_name_col = resolve_column(panel, "barrio")
    district_code_col = resolve_column(panel, "cod_distrito")
    district_name_col = resolve_column(panel, "distrito")
    year_col = resolve_column(panel, "año", "ano")
    indicator_col = resolve_column(panel, "indicador_completo")
    value_col = resolve_column(panel, "valor_indicador")

    panel["indicator_key"] = panel[indicator_col].map(normalize_text)
    panel["barrio_code"] = panel[barrio_code_col].map(normalize_code)
    panel["district_code"] = panel[district_code_col].map(normalize_code)
    panel["barrio_name"] = panel[barrio_name_col].astype(str).str.strip()
    panel["district_name"] = panel[district_name_col].astype(str).str.strip()
    panel["barrio_name_key"] = panel["barrio_name"].map(normalize_text)
    panel["district_name_key"] = panel["district_name"].map(normalize_text)

    best_year = latest_year(panel, year_col, year)
    print(f"  Panel: año {best_year} (solicitado {year})")
    panel_latest = panel[pd.to_numeric(panel[year_col], errors="coerce").astype("Int64") == best_year].copy()

    base = panel_latest[["barrio_code", "barrio_name", "district_code", "district_name", "barrio_name_key", "district_name_key"]].dropna(subset=["barrio_code"]).drop_duplicates()

    indicator_specs = {
        "raw_renta": "Renta media disponible por persona",
        "raw_paro": "Tasa absoluta de paro registrado (febrero)",
        "raw_estudios": "Población mayor/igual de 25 años con estudios superiores, licenciatura, arquitectura, ingeniería sup., estudios sup. no universitarios, doctorado, postgraduado",
        "raw_transporte_proxy": "Índice de vulnerabilidad medio ambiente urbano y movilidad",
        "raw_equip_cmsc": "Centros municipales de salud comunitaria (CMSC)",
        "raw_equip_mercados": "Mercados municipales",
        "raw_equip_deporte": "Centros deportivos municipales",
        "raw_equip_escuelas": "Escuelas infantiles municipales",
        "raw_equip_colegios": "Colegios públicos infantil y primaria",
        "raw_salud_h": "Esperanza de vida al nacer hombres",
        "raw_salud_m": "Esperanza de vida al nacer mujeres",
    }

    result = base.copy()
    indicator_years = {}
    for output_col, indicator_name in indicator_specs.items():
        subset, used_year = extract_indicator(panel, year_col, indicator_col, value_col, indicator_name)
        indicator_years[output_col] = used_year
        if output_col in {"raw_salud_h", "raw_salud_m"}:
            grouped = (
                subset.groupby("district_name_key", dropna=True)["indicator_value"]
                .mean()
                .reset_index()
                .rename(columns={"indicator_value": output_col})
            )
            result = result.merge(grouped, on="district_name_key", how="left")
        else:
            grouped = (
                subset.groupby("barrio_code", dropna=True)["indicator_value"]
                .mean()
                .reset_index()
                .rename(columns={"indicator_value": output_col})
            )
            result = result.merge(grouped, on="barrio_code", how="left")

    return result, {"base_year": best_year, "indicator_years": indicator_years}


def load_verde(path: Path) -> pd.DataFrame:
    verde = read_csv_guess(path)
    district_name_col = resolve_column(verde, "DISTRITO")
    verde_m2_col = resolve_column(verde, "m2 de ZONAS VERDES Y PARQUES en distrito")

    verde["district_name_key"] = verde[district_name_col].astype(str).map(normalize_text)
    verde["verde_m2_total"] = verde[verde_m2_col].map(parse_es_number)
    return verde[["district_name_key", "verde_m2_total"]].drop_duplicates()


def load_ruido(ruido_path: Path, est_path: Path) -> pd.DataFrame:
    estaciones = read_csv_guess(est_path)
    ruido = read_csv_guess(ruido_path)

    est_id_col = resolve_column(estaciones, "ESTACIÓN", "ESTACION")
    est_barrio_col = resolve_column(estaciones, "BARRIO")
    ruido_id_col = resolve_column(ruido, "NMT")
    ruido_tipo_col = resolve_column(ruido, "tipo")
    ruido_laeq_col = resolve_column(ruido, "LAeq")

    estaciones["barrio_name_key"] = estaciones[est_barrio_col].astype(str).map(normalize_text)
    estaciones[est_id_col] = estaciones[est_id_col].map(normalize_station_id)
    ruido[ruido_id_col] = ruido[ruido_id_col].map(normalize_station_id)
    ruido["laeq_num"] = ruido[ruido_laeq_col].map(parse_es_number)
    ruido = ruido[ruido[ruido_tipo_col].astype(str).str.upper() == "D"].copy()

    merged = ruido.merge(
        estaciones[[est_id_col, "barrio_name_key"]],
        left_on=ruido_id_col,
        right_on=est_id_col,
        how="left",
    )
    grouped = (
        merged.groupby("barrio_name_key", dropna=True)["laeq_num"]
        .mean()
        .reset_index()
        .rename(columns={"laeq_num": "raw_ruido_laeq"})
    )
    return grouped


def load_geo(shp_path: Path) -> pd.DataFrame:
    gdf = gpd.read_file(shp_path)
    code_col = resolve_column(gdf, "COD_BAR")
    district_col = resolve_column(gdf, "NOMDIS")
    barrio_col = resolve_column(gdf, "NOMBRE")
    gdf_metric = gdf.to_crs(25830)
    centroids = gpd.GeoSeries(gdf_metric.geometry.centroid, crs=25830).to_crs(4326)
    return pd.DataFrame(
        {
            "barrio_code": gdf[code_col].map(normalize_code),
            "district_name_key": gdf[district_col].map(normalize_text),
            "barrio_name_key": gdf[barrio_col].map(normalize_text),
            "centroid_lat": centroids.y,
            "centroid_lng": centroids.x,
        }
    )


def normalize_criteria(df: pd.DataFrame) -> pd.DataFrame:
    socio_cols = pd.concat(
        [
            normalize_minmax(df["raw_renta"]).rename("renta"),
            normalize_minmax(df["raw_paro"], reverse=True).rename("paro"),
            normalize_minmax(df["raw_estudios"]).rename("estudios"),
        ],
        axis=1,
    )
    df["comp_socioeconomico"] = socio_cols.mean(axis=1, skipna=True)

    equip_cols = pd.concat(
        [
            normalize_minmax(df["raw_equip_cmsc"]).rename("cmsc"),
            normalize_minmax(df["raw_equip_mercados"]).rename("mercados"),
            normalize_minmax(df["raw_equip_deporte"]).rename("deporte"),
            normalize_minmax(df["raw_equip_escuelas"]).rename("escuelas"),
            normalize_minmax(df["raw_equip_colegios"]).rename("colegios"),
        ],
        axis=1,
    )
    df["comp_equipamientos"] = equip_cols.mean(axis=1, skipna=True)

    salud_cols = pd.concat(
        [
            normalize_minmax(df["raw_salud_h"]).rename("salud_h"),
            normalize_minmax(df["raw_salud_m"]).rename("salud_m"),
        ],
        axis=1,
    )
    df["comp_salud"] = salud_cols.mean(axis=1, skipna=True)

    df["v_socioeconomico"] = normalize_minmax(df["comp_socioeconomico"])
    df["v_transporte"] = normalize_minmax(df["raw_transporte_proxy"], reverse=True)
    df["v_verde"] = normalize_minmax(df["verde_m2_total"])
    df["v_ruido"] = normalize_minmax(df["raw_ruido_laeq"], reverse=True)
    df["v_equipamientos"] = normalize_minmax(df["comp_equipamientos"])
    df["v_salud"] = normalize_minmax(df["comp_salud"])
    return df


def normalize_minmax(series: pd.Series, reverse: bool = False) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce")
    non_null = vals.dropna()
    if non_null.empty:
        return pd.Series([np.nan] * len(vals), index=vals.index)
    lo, hi = non_null.min(), non_null.max()
    if hi == lo:
        return pd.Series([5.0 if not pd.isna(v) else np.nan for v in vals], index=vals.index)
    scaled = (vals - lo) / (hi - lo)
    if reverse:
        scaled = 1 - scaled
    return (scaled * 10).round(2)


def build_output(df: pd.DataFrame, panel_meta: dict) -> dict:
    madrid_means = {k: round(float(df[f"v_{k}"].mean()), 2) for k in CRITERIA_KEYS}
    barrios = []
    for _, row in df.iterrows():
        values = {k: (None if pd.isna(row[f"v_{k}"]) else round(float(row[f"v_{k}"]), 2)) for k in CRITERIA_KEYS}
        criteria = []
        for key in CRITERIA_KEYS:
            value = values[key]
            criteria.append(
                {
                    "key": key,
                    "value": value,
                    "delta_vs_mean": None if value is None else round(value - madrid_means[key], 2),
                }
            )

        barrios.append(
            {
                "id": row["barrio_code"],
                "name": row["barrio_name"],
                "district": row["district_name"],
                "lat": None if pd.isna(row["centroid_lat"]) else round(float(row["centroid_lat"]), 5),
                "lng": None if pd.isna(row["centroid_lng"]) else round(float(row["centroid_lng"]), 5),
                "values": values,
                "criteria": criteria,
                "sources": {
                    "socioeconomico": "Panel de indicadores de distritos y barrios (renta, paro y estudios superiores)",
                    "transporte": "Panel de indicadores de distritos y barrios (proxy: índice de vulnerabilidad medio ambiente urbano y movilidad)",
                    "verde": "Superficies de zonas verdes y parques por distrito (proxy distrital)",
                    "ruido": "SIVCA - Vigilancia de contaminación acústica (LAeq tipo D, agregado por barrio)",
                    "equipamientos": "Panel de indicadores de distritos y barrios (mercados, deporte, escuelas, colegios y CMSC)",
                    "salud": "Panel de indicadores de distritos y barrios (esperanza de vida al nacer, hombres y mujeres)",
                },
                "proxy_flags": {
                    "verde_es_proxy_distrital": True,
                    "transporte_es_proxy_vulnerabilidad_movilidad": True,
                },
            }
        )

    return {
        "meta": {
            "generated_at": pd.Timestamp.now("UTC").isoformat(),
            "total_barrios": len(barrios),
            "panel_base_year": panel_meta["base_year"],
            "panel_indicator_years": panel_meta["indicator_years"],
            "madrid_means": madrid_means,
            "criteria": CRITERIA_KEYS,
        },
        "barrios": barrios,
    }


def main() -> None:
    print("=== build_dataset.py ===")
    panel, panel_meta = load_panel(ROOT / "data/raw/panel_indicadores.csv", PANEL_TARGET_YEAR)
    print(f"  panel base barrios: {len(panel)}")
    verde = load_verde(ROOT / "data/raw/zonas_verdes.csv")
    ruido = load_ruido(ROOT / "data/raw/sivca_ruido_diario.csv", ROOT / "data/raw/sivca_estaciones.csv")
    geo = load_geo(ROOT / "data/raw/barrios_geo" / "BARRIOS.shp")

    df = panel.merge(verde, on="district_name_key", how="left")
    df = df.merge(ruido, on="barrio_name_key", how="left")
    df = df.merge(
        geo[["barrio_name_key", "district_name_key", "centroid_lat", "centroid_lng"]],
        on=["barrio_name_key", "district_name_key"],
        how="left",
    )

    df = normalize_criteria(df)
    output = build_output(df, panel_meta)

    out_path = ROOT / "data/processed/barrios-madrid.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK {len(output['barrios'])} barrios -> {out_path}")


if __name__ == "__main__":
    main()
