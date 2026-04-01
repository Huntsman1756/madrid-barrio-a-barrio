# Madrid, barrio a barrio

**Comparador explicable de calidad urbana por barrio de Madrid.**

No te dice dónde vivir. Te muestra cómo cambia el ranking de los 131 barrios cuando
cambian tus prioridades, y qué parte de ese resultado depende de proxies, cobertura
parcial o datos que solo existen a nivel distrital.

La diferencia frente a otros comparadores: la fórmula está escrita en pantalla, los
pesos los elige la persona usuaria, cada criterio cita su fuente exacta, y los límites
metodológicos aparecen en la ficha del barrio, no solo en la documentación.

→ **Demo:** https://[pendiente-github-pages]  
→ **Datos:** https://datos.madrid.es · Licencia CC BY 4.0

---

## Qué hace

- **Ranking en tiempo real** de 131 barrios sobre 6 criterios urbanos
- **Perfiles predefinidos** (Familias, Mayores, Sin coche) y modo manual con sliders
- **Ficha de barrio** con radar chart, comparación vs. media de Madrid y fuente citada por criterio
- **Comparador** de hasta 3 barrios en paralelo
- **Mapa** con marcadores coloreados por score
- **URL con estado** compartible: perfil, pesos y barrio seleccionado en el hash

---

## Criterios y fuentes de datos

| Criterio | Fuente | Cobertura | Año(s) |
|---|---|---|---|
| Socioeconómico | Panel de indicadores de distritos y barrios (renta, paro, estudios) | 131/131 barrios | 2023–2025 |
| Transporte ⚠ | Panel de indicadores — proxy: índice de vulnerabilidad movilidad | 131/131 barrios | 2023 |
| Zonas verdes ⚠ | Superficies de zonas verdes y parques por distrito | 131/131 barrios | 2024 |
| Tranquilidad | SIVCA — contaminación acústica LAeq tipo D por barrio | 27/131 barrios | 2024 |
| Equipamientos | Panel de indicadores (mercados, deporte, escuelas, CMSC) | 122/131 barrios | 2024–2025 |
| Salud ⚠ | Panel de indicadores — esperanza de vida al nacer | 131/131 barrios | 2023 |

⚠ Proxy o granularidad distrital: el dato no llega a nivel de barrio en las fuentes oficiales actuales.  
Los barrios sin dato de ruido no penalizan al score: se excluyen del denominador.

---

## Límites metodológicos

1. El score depende de los pesos declarados. Con pesos distintos, el ranking cambia.
2. Ruido tiene cobertura parcial (27/131). Los 104 restantes salen "sin ruido" en la ficha.
3. Transporte y Salud son proxies distritales, no métricas de barrio independiente.
4. La normalización es min-max sobre el conjunto actual. Añadir o quitar barrios desplaza todos los scores.

---

## Estructura del proyecto

```text
madrid-barrio-a-barrio/
├── index.html # Frontend estático (todo en un fichero)
├── data/
│ ├── raw/ # CSVs descargados tal cual de datos.madrid.es
│ └── processed/
│ └── barrios-madrid.json # JSON limpio con 131 barrios y metadatos
├── scripts/
│ ├── sources.py # URLs de los 5 endpoints oficiales
│ ├── fetch_datasets.py # Descarga las 5 fuentes a data/raw/
│ ├── inspect_columns.py # Genera column_report.txt para auditoría
│ ├── build_dataset.py # Transforma, pivota y normaliza → JSON
│ └── validate_dataset.py # Comprueba ≥128 barrios, 6 criterios, rangos
└── docs/
└── memoria.md # Memoria del concurso
```

---

## Arrancar en local

```bash
# (Opcional) Regenerar el dataset desde cero
python scripts/fetch_datasets.py
python scripts/build_dataset.py
python scripts/validate_dataset.py  # debe imprimir PASS: 131 barrios validados

# Servir el frontend
python -m http.server 4173
# Abrir http://localhost:4173
```

---

## Fórmula de scoring

```text
score(b, w) = Σ(wᵢ · vᵢ) / Σwᵢ · 10
```

Los criterios con valor nulo se excluyen del denominador. Los pesos `wᵢ` son enteros 0–10 elegidos por la persona usuaria. Los valores `vᵢ` están normalizados en [0, 10] mediante min-max.

---

## Licencia de datos

Datos del Portal de Datos Abiertos del Ayuntamiento de Madrid bajo **Creative Commons Attribution 4.0**.
