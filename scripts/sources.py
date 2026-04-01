"""
Contract: five official datos.madrid.es endpoints.
Edit only the URLs here; the rest of the pipeline reads this file.
"""

SOURCES = {
    "panel_indicadores": {
        "url": "https://datos.madrid.es/dataset/300087-0-indicadores-distritos/resource/300087-0-indicadores-distritos-csv/download/300087-0-indicadores-distritos-csv.csv",
        "target": "data/raw/panel_indicadores.csv",
        "format": "csv",
        "notes": (
            "Formato LARGO. Columnas clave esperadas: cod_distrito, distrito, cod_barrio, barrio, "
            "ano, categoria_1, categoria_2, indicador_nivel1, indicador_nivel2, "
            "indicador_nivel3, indicador_completo, valor_indicador. "
            "Requiere pivot/filtrado antes de normalizar."
        ),
    },
    "zonas_verdes": {
        "url": "https://datos.madrid.es/dataset/300266-0-arbolado-superficie/resource/300266-19-arbolado-superficie-csv/download/300266-19-arbolado-superficie-csv",
        "target": "data/raw/zonas_verdes.csv",
        "format": "csv",
        "notes": (
            "Superficie de arbolado y zonas verdes por distrito 2024. "
            "Resolucion DISTRITAL: si no hay columna barrio homogenea se usa como proxy "
            "y se documenta en la ficha del producto."
        ),
    },
    "sivca_ruido_diario": {
        "url": "https://datos.madrid.es/egob/catalogo/215885-10749127-contaminacion-ruido.csv",
        "target": "data/raw/sivca_ruido_diario.csv",
        "format": "csv",
        "notes": (
            "Mediciones diarias de ruido por estacion acustica. "
            "No incluye coordenadas propias: debe cruzarse con sivca_estaciones "
            "para asignar cada medicion a un barrio."
        ),
    },
    "sivca_estaciones": {
        "url": "https://datos.madrid.es/dataset/211346-0-estaciones-acusticas/resource/211346-4-estaciones-acusticas-csv/download/211346-4-estaciones-acusticas-csv.csv",
        "target": "data/raw/sivca_estaciones.csv",
        "format": "csv",
        "notes": (
            "Catalogo de estaciones acusticas con coordenadas y barrio/distrito. "
            "JOIN obligatorio con sivca_ruido_diario sobre el id de estacion."
        ),
    },
    "barrios_geo": {
        "url": "https://datos.madrid.es/dataset/300496-0-barrios-madrid/resource/300496-3-barrios-madrid/download/300496-3-barrios-madrid.zip",
        "target": "data/raw/barrios_geo.zip",
        "format": "zip",
        "notes": (
            "ZIP con shapefile o GeoJSON de los 128 barrios de Madrid. "
            "Extraer y leer para obtener centroides (lat/lng) y geometria para el mapa."
        ),
    },
}
