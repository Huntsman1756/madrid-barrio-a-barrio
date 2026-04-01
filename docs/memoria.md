# Memoria — Madrid, barrio a barrio

**Premio Reutilización de Datos Abiertos · Ayuntamiento de Madrid 2026**  
Categoría: Servicios web, aplicaciones y visualizaciones  
Fecha de entrega: 4 de mayo de 2026

---

## Descripción del proyecto

Madrid tiene 131 barrios y docenas de indicadores urbanos públicos. Lo que no existe es una herramienta que permita a un ciudadano entender **por qué** un barrio aparece antes que otro, qué peso tiene cada criterio, y qué ocurre cuando un dato está incompleto o es un proxy distrital.

*Madrid, barrio a barrio* es un comparador explicable de calidad urbana. No produce una recomendación opaca: produce un ranking cuya fórmula está escrita en pantalla, cuyos pesos elige la persona usuaria, y cuyos límites metodológicos están señalados en la propia ficha de cada barrio.

El proyecto usa cinco datasets oficiales del Portal de Datos Abiertos del Ayuntamiento —Panel de indicadores de distritos y barrios, SIVCA, superficies de zonas verdes, estaciones acústicas y geometría de barrios— procesados con un pipeline reproducible y auditable. Los 131 barrios se comparan sobre seis criterios: entorno socioeconómico, transporte, zonas verdes, tranquilidad, equipamientos cotidianos y salud.

Los perfiles predefinidos —Familias, Mayores, Sin coche— reflejan necesidades urbanas distintas con pesos distintos. El modo personalizado permite ajustar cada criterio de 0 a 10. El ranking se reordena en tiempo real. La URL codifica el estado completo: perfil, pesos y barrio seleccionado son compartibles.

La apuesta de fondo es que la transparencia metodológica tiene valor ciudadano propio. Un ciudadano que entiende por qué un barrio aparece primero puede cuestionar ese resultado, cambiar los pesos y llegar a una conclusión propia. Eso no es posible con una herramienta que no muestra sus cálculos.

---

## 1. Problema ciudadano

Existen herramientas para comparar barrios de Madrid. El problema no es la ausencia
de datos, sino la ausencia de explicación: la mayoría produce una recomendación opaca
sin decir qué peso tiene cada criterio, qué fuentes usa exactamente, ni qué ocurre
cuando un dato no está disponible o solo existe a nivel distrital.

Esa opacidad tiene consecuencias concretas. Una familia con hijos no tiene las mismas
prioridades que una persona mayor que necesita moverse sin coche. Si los pesos están
fijos e invisibles, el resultado no es neutral: es una decisión tomada por el diseñador
sin que el usuario lo sepa.

Este proyecto parte de una premisa distinta: **el ranking no es una verdad objetiva,
es una suma ponderada**. Hacerla visible —la fórmula, los pesos, las fuentes, los
límites— es el valor ciudadano del proyecto. No ayuda solo a elegir barrio; ayuda a
entender qué hay detrás de cualquier comparador que no muestre sus cálculos.

---

## 2. Datos reutilizados

El proyecto usa **cinco conjuntos de datos oficiales** del Portal de Datos Abiertos del Ayuntamiento de Madrid, todos bajo licencia CC BY 4.0:

| Dataset | ID en portal | Uso |
|---|---|---|
| Panel de indicadores de distritos y barrios | 300087-0 | Base troncal: socioeconómico, transporte, equipamientos, salud |
| Superficies de zonas verdes y parques | 300266-0 | Criterio verde (proxy distrital) |
| Contaminación acústica — datos diarios SIVCA | 215885-0 | Criterio tranquilidad |
| Estaciones acústicas | 211346-0 | Georreferenciación de estaciones SIVCA |
| Geometría de barrios de Madrid | 300496-0 | Centroides para el mapa |

El Panel de indicadores es el dataset troncal. Viene en formato largo con columnas `cod_barrio`, `barrio`, `ano`, `indicador_completo`, `valor_indicador`, lo que requiere un paso de pivotado documentado en `scripts/build_dataset.py`.

---

## 3. Metodología y normalización

### Pipeline de datos

```text
fetch_datasets.py → data/raw/ (5 ficheros, descarga directa)
inspect_columns.py → column_report.txt (auditoría de esquemas reales)
build_dataset.py → barrios-madrid.json (131 barrios, 6 criterios)
validate_dataset.py → PASS/FAIL
```

### Normalización

```text
vᵢ = (x - min(X)) / (max(X) - min(X)) · 10
```

Para ruido la normalización se invierte (mayor ruido → menor score de tranquilidad).

### Scoring

```text
score(b, w) = Σ(wᵢ · vᵢ) / Σwᵢ · 10
```

Los criterios con valor nulo se excluyen del denominador.

### Años de datos

| Indicador | Año |
|---|---|
| Renta media | 2023 |
| Tasa de paro | 2025 |
| Estudios superiores | 2024 |
| Proxy de movilidad | 2023 |
| Equipamientos | 2024–2025 |
| Esperanza de vida | 2023 |
| Zonas verdes | 2024 |
| Ruido SIVCA | 2024 |

---

## 4. Perfiles beneficiarios

| Perfil | Énfasis |
|---|---|
| **Familias** | Equipamientos (9), verde (8), tranquilidad (8) |
| **Mayores** | Salud (10), tranquilidad (9), transporte (9), equipamientos (9) |
| **Sin coche** | Transporte (10), equipamientos (8) |
| **Personalizado** | Todos los sliders libres, pesos 0–10 |

---

## 5. Diferencia frente a herramientas similares

**Madriwa** (Premio Reutilización 2024, categoría aplicaciones) es la referencia más
cercana: también compara barrios de Madrid y también usa datos del portal municipal.
La diferencia no es de escala —Madriwa usa más de 50 fuentes— sino de modelo:
Madriwa produce una recomendación; este proyecto produce una explicación.

Las diferencias concretas:

| Aspecto | Madriwa | Madrid, barrio a barrio |
|---|---|---|
| Pesos de los criterios | Fijos, no visibles | Configurables por el usuario, 0–10 por criterio |
| Fórmula de scoring | No publicada | Escrita en la interfaz: `Σ(wᵢ·vᵢ)/Σwᵢ·10` |
| Fuentes por criterio | Listadas en blog, no en la UI | Citadas bajo cada slider y en la ficha del barrio |
| Proxies y cobertura parcial | No declarados en la UI | Señalados con ⚠ en la ficha y en el README |
| Pipeline reproducible | No público | `git clone` + 4 comandos Python |
| Perfil de uso | Usuario generalista | Perfiles explícitos: Familias, Mayores, Sin coche |

La apuesta es que la transparencia metodológica tiene valor ciudadano independiente
del número de fuentes. Un ciudadano que entiende por qué un barrio aparece primero
puede cuestionar ese resultado, ajustar los pesos y llegar a una conclusión propia.
Eso no es posible con una caja negra, aunque la caja negra use 50 datasets.

---

## 6. Límites metodológicos declarados

1. **Ruido:** cobertura parcial. Solo 27 de 131 barrios tienen estación acústica en el SIVCA.
2. **Transporte:** proxy del índice de vulnerabilidad de movilidad, no aforo de paradas ni frecuencia de servicio.
3. **Zonas verdes:** dato distrital. Todos los barrios del mismo distrito comparten el mismo valor.
4. **Salud:** dato distrital (esperanza de vida al nacer desagregada solo a nivel de distrito).
5. **Normalización min-max:** el score depende del conjunto completo; añadir barrios desplaza todos los scores.

---

## 7. Tecnología y reproducibilidad

```bash
python scripts/fetch_datasets.py
python scripts/build_dataset.py
python scripts/validate_dataset.py
python -m http.server 4173
```

No hay servidor, no hay base de datos, no hay API de terceros. Frontend HTML/CSS/JS sin framework ni build step.

**Stack:** Python 3 + pandas · HTML/CSS/JS vanilla · Leaflet 1.9 · Chart.js 4.4 · GitHub Pages

---

## 8. URL pública y repositorio

- **Demo en vivo:** https://huntsman1756.github.io/madrid-barrio-a-barrio/
- **Repositorio:** https://github.com/Huntsman1756/madrid-barrio-a-barrio
- **Datos originales:** https://datos.madrid.es

Dos cosas pendientes antes de la entrega del 4 de mayo:

- GitHub Pages: git push + activar Pages desde main /root → sustituir los dos [pendiente] en ambos documentos con la URL real.
- Formulario oficial: el Ayuntamiento pide la memoria en su propio formulario web, no solo en Markdown. Cuando lo abras, los 8 bloques de memoria.md tienen correspondencia directa con las secciones del formulario.

---

## Argumento oral de 30 segundos

Hay herramientas que te dicen qué barrio te conviene. La nuestra hace algo distinto: te muestra **por qué** cambia el ranking cuando cambian tus prioridades, y qué parte de ese resultado depende de datos incompletos o proxies que nunca te iban a decir.

La fórmula está escrita en pantalla. Los pesos los eliges tú. Los límites están en la ficha, no en la letra pequeña.

No es un buscador de vivienda. Es una herramienta para leer Madrid con tus propios criterios.
