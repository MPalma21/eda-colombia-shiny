# Analisis Exploratorio en Datos Abiertos

> Plataforma analitica interactiva para el portal nacional [datos.gov.co](https://www.datos.gov.co/), desarrollada con **Shiny for Python** bajo los estandares oficiales de ingenieria de software y diseno de UI de **Posit PBC**.

**Autor:** Miguelangel Palma  
- **LinkedIn:** [miguelangelpr](https://www.linkedin.com/in/miguelangelpr)  
- **GitHub:** [MPalma21](https://github.com/MPalma21)  
- **Despliegue:** [Posit Connect Cloud](https://connect.posit.cloud)  

---

## Tabla de Contenidos

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Estructura del Repositorio](#estructura-del-repositorio)
3. [Flujo de Funcionamiento de la Aplicacion](#flujo-de-funcionamiento-de-la-aplicacion)
4. [Modulos y Capacidades Analiticas](#modulos-y-capacidades-analiticas)
5. [Integracion con la API de datos.gov.co](#integracion-con-la-api-de-datosgovco)
6. [Patrones de Reactividad y Rendimiento](#patrones-de-reactividad-y-rendimiento)
7. [Instalacion y Ejecucion](#instalacion-y-ejecucion)
8. [Suite de Pruebas Automatizadas](#suite-de-pruebas-automatizadas)
9. [Configuracion y Personalizacion](#configuracion-y-personalizacion)

---

## Arquitectura del Sistema

La aplicacion implementa una estricta separacion de responsabilidades en 4 capas:

```
[ Navegador / Cliente ]
        │
        ▼ (Peticiones HTTP / WebSockets)
[ Capa de Presentacion: app.py + www/styles.css ]
        │
        ├─ Ensambla el layout global (ui.page_sidebar)
        ├─ Orquesta modulos con identificadores unicos
        │
        ▼
[ Capa de Controladores Reactivos: modules/ ]
        │
        ├─ mod_loader.py       -> Aislamiento de eventos y seleccion de datasets
        ├─ mod_summary.py      -> Metricas globales e integridad de datos
        ├─ mod_table.py        -> Filtrado reactivo en memoria
        ├─ mod_distributions.py-> Computacion de densidades y boxplots
        ├─ mod_correlations.py -> Matrices de asociacion lineal
        ├─ mod_comparisons.py  -> Agrupacion categorica vs cuantitativa
        ├─ mod_timeseries.py   -> Remuestreo temporal y medias moviles
        └─ mod_stats.py        -> Pruebas de hipotesis (Shapiro-Wilk)
        │
        ▼ (Invocacion de funciones puras de Python)
[ Capa de Servicios y Logica de Negocio: services/ ]
        │
        ├─ api_service.py   -> Conexion HTTP a Socrata, parseo y casteo de tipos
        ├─ scope_service.py -> Filtro temporal y muestra reproducible de las filas cargadas
        ├─ table_service.py -> Filtros tabulares y exportacion CSV segura
        └─ stats_service.py -> Algoritmos matematicos y diagnostico estadistico
```

### Principios Fundamentales
- **Desacoplamiento de la logica analitica**: Las transformaciones matematicas y las consultas HTTP no dependen del contexto reactivo de Shiny. Viven en `services/` y pueden ejecutarse de forma aislada en scripts, notebooks o pipelines CI/CD.
- **Grafo reactivo no redundante**: Se utiliza `@reactive.calc` para memorizar calculos costosos (como matrices de correlacion o clasificaciones de columnas), evitando que multiples salidas computen la misma operacion repetidamente.
- **Aislamiento con `@reactive.event`**: Las descargas de datos solo se activan cuando el usuario presiona explicitamente el boton "Cargar Dataset", previniendo peticiones innecesarias mientras se escribe en los campos de texto.
- **Encapsulamiento de espacios de nombres (`@module.ui` y `@module.server`)**: Cada modulo aísla sus entradas y salidas, eliminando colisiones de identificadores y garantizando modularidad.

---

## Estructura del Repositorio

```text
Shiny APP Python/
│
├── app.py                     Punto de entrada minimalista (< 75 lineas).
├── config.py                  Constantes, endpoints, limites de filas y datasets muestra.
├── pyproject.toml             Definicion formal del paquete, dependencias y pytest.
├── requirements.txt           Dependencias fijadas para entornos pip tradicionales.
├── README.md                  Documentacion tecnica del sistema.
│
├── services/                  Capa de logica pura no reactiva (100% testeable).
│   ├── __init__.py
│   ├── api_service.py         Cliente REST para la API Socrata con validacion de URLs y IDs.
│   ├── scope_service.py       Periodo y muestra reproducible sobre datos descargados.
│   ├── table_service.py       Filtros de tabla y exportacion CSV segura.
│   └── stats_service.py       Funciones puras de diagnostico, clasificacion y estadistica.
│
├── modules/                   Modulos Shiny (componentes UI + Server encapsulados).
│   ├── __init__.py
│   ├── mod_loader.py          Panel lateral: selector de datasets, input de ID y disparador.
│   ├── mod_summary.py         Panel: Metricas del dataset, metadatos oficiales y nulos.
│   ├── mod_table.py           Panel: Vista tabular con busqueda textual y filtro categorico.
│   ├── mod_distributions.py   Panel: Histogramas con curva KDE, boxplots, violines y ECDF.
│   ├── mod_correlations.py    Panel: Heatmap de correlacion y matriz de dispersion.
│   ├── mod_comparisons.py     Panel: Comparaciones bivariadas cuantitativas vs categoricas.
│   ├── mod_timeseries.py      Panel: Series de tiempo, remuestreo y tendencias suavizadas.
│   └── mod_stats.py           Panel: Tablas descriptivas completas y prueba Shapiro-Wilk.
│
├── www/                       Recursos estaticos y estilos visuales.
│   └── styles.css             Hoja de estilo profesional con paleta Positron IDE.
│
└── tests/                     Suite de pruebas automatizadas con pytest.
    ├── __init__.py
    └── test_services.py       Pruebas unitarias sobre servicios sin dependencias de servidor.
```

---

## Flujo de Funcionamiento de la Aplicacion

1. **Seleccion o Entrada del Recurso**:
   - El usuario puede elegir un dataset de ejemplo precargado (hospitales, colegios, medicamentos, transito) o pegar cualquier URL / ID de recurso de `datos.gov.co` (por ejemplo, `gt2j-8ykr`).
   - Se puede aplicar una busqueda de texto en el recurso antes de descargar y especificar el limite de registros (desde 50 hasta 50,000). El modo de carga puede tomar las primeras filas por ID o repartir el limite entre cinco bloques distribuidos por el recurso.
2. **Descarga y Casteo Tipologico Inteligente**:
   - Al pulsar "Cargar y Analizar Datos", `services/api_service.py` consulta la API Socrata con `$limit` y orden estable por `:id`. El modo inicial usa `$offset=0`; la cobertura distribuida consulta el total y reparte el limite entre cinco offsets. Si se indica una busqueda, usa `$q` antes del limite.
   - El servicio descarga simultaneamente los metadatos oficiales del recurso (nombre de entidad emisora, descripcion publica, fecha de corte).
   - Se consultan los tipos declarados en los metadatos para convertir numeros y fechas sin perder codigos de texto ni sustituir fechas invalidas por nulos. Sin metadatos se aplica una inferencia conservadora.
   - Una consulta separada intenta obtener el total de filas que cumplen el filtro. Si falla, la carga de datos continua y se informa que el total no esta disponible.
3. **Distribucion Reactiva del Dataset**:
   - `mod_loader.py` emite las variables reactivas `df_react` y `meta_react`.
   - Todos los modulos suscritos reciben la actualizacion y ejecutan sus calculos reactivos. La descarga se ejecuta fuera del hilo principal con `ExtendedTask`, para mantener la interfaz responsiva.
   - Tras descargar, el panel lateral permite elegir una columna y un periodo de fechas, y seleccionar una muestra aleatoria reproducible de las filas descargadas. El alcance elegido se aplica a todas las vistas y a la exportacion.
   - La cabecera integra el contexto del recurso: numero de filas analizadas, total conocido y alcance del periodo o muestra. Los creditos del autor y sus enlaces aparecen en texto pequeno junto al titulo. La carga distribuida mejora la cobertura por ID, pero sus bloques no constituyen una muestra aleatoria simple. Una muestra posterior corresponde solo a las filas descargadas, no al recurso completo.

---

## Modulos y Capacidades Analiticas

La navegacion sigue una secuencia de EDA: contexto y calidad del recurso, estadisticas descriptivas, comportamiento temporal, distribuciones y relaciones entre variables y, al final, inspeccion de los registros.

### 1. Panel de Resumen (`mod_summary.py`)
- **Tarjetas de diagnostico rapido**: Muestran el recuento total de registros, total de variables, numero de variables cuantitativas y porcentaje general de valores faltantes.
- **Metadatos oficiales**: Informacion provista por la entidad que publica el dataset en `datos.gov.co`.
- **Diagnostico por columna**: Tabla detallada con el tipo de dato inferido, recuento de valores unicos y porcentaje exacto de nulos por columna.
- **Grafico de valores faltantes**: Grafica de barras en escala de grises/rojo que ordena visualmente que columnas presentan deficiencias de completitud.

### 2. Estadisticas Descriptivas (`mod_stats.py`)
- **Tabla Descriptiva Cuantitativa**: Conteo, media, desviacion, minimo, percentiles (5%, 25%, 50%, 75%, 95%) y maximo.
- **Resumen Categorico**: Cardinalidad, moda y frecuencia relativa del elemento dominante.
- **Diagnostico posterior de normalidad**: Prueba Shapiro-Wilk sobre hasta 5,000 registros, con estadistico W, p-valor y decision de rechazo de la hipotesis de normalidad. Un p-valor alto no demuestra que la distribucion sea normal.

### 3. Series de Tiempo y Tendencias (`mod_timeseries.py`)
- Deteccion automatica de columnas temporales.
- Agregacion configurable: Suma, Promedio, Conteo o Maximo. La sugerencia inicial usa promedio para medidas generales y suma para nombres de magnitudes aditivas.
- Remuestreo automatico segun la extension del periodo (diario o mensual).
- Inclusion de **Media Movil Suavizada** para identificar tendencias subyacentes.

### 4. Distribuciones Univariadas (`mod_distributions.py`)
- Visualizaciones interactivas construidas con Plotly:
  - **Histograma con curva KDE**: Estimacion de densidad Kernel sobrepuesta.
  - **Diagrama de Caja (Box Plot)**: Deteccion de valores atipicos (outliers) y cuartiles.
  - **Grafico de Violin**: Densidad bivariada combinada con dispersion interna.
  - **Curva Empirica Acumulada (ECDF)**: Funcion de distribucion acumulada.
- Tarjetas de momentos estadisticos al pie del grafico: Media, Mediana, Desviacion Estandar y Sesgo (Skewness).

### 5. Matriz de Correlacion y Dispersion (`mod_correlations.py`)
- Calculo parametrico de matrices de correlacion admitiendo metodos: **Pearson**, **Spearman** y **Kendall**.
- **Mapa de Calor (Heatmap)** con escala de color centrada y valores numericos anotados.
- **Matriz de Dispersion (Scatter Matrix)** para observar simultaneamente cruces bidimensionales entre variables continuas.
- La matriz de dispersion usa hasta 1,500 filas completas seleccionadas de forma reproducible; la correlacion se calcula sobre todas las filas cargadas.

### 6. Comparaciones por Categoria (`mod_comparisons.py`)
- Cruce bivariado entre una variable cuantitativa continua y una variable cualitativa discreta.
- Permite calcular promedios comparativos, conteos de frecuencia y distribuciones agrupadas en diagramas de caja o violin.
- Incluye control de limite de categorias para no saturar el eje horizontal con variables de alta cardinalidad.

### 7. Vista de Datos (`mod_table.py`)
- **Busqueda textual instantanea**: Filtra dinamicamente filas que contengan el termino ingresado en cualquier columna.
- **Descarga CSV**: Exporta las filas resultantes de la busqueda y el filtro categorico activos. Los textos que podrian interpretarse como formulas en hojas de calculo se exportan como texto.
- **Filtro categórico**: Permite elegir cualquier columna categorica y buscar por texto entre todos sus valores, sin limitar el selector a las primeras 50 categorias.
- **Control de paginacion**: Permite regular cuantas filas renderizar simultaneamente para optimizar la respuesta del navegador.

---

## Integracion con la API de datos.gov.co

La aplicacion utiliza el endpoint estandar de la API Socrata (SODA):
```text
GET https://www.datos.gov.co/resource/{resource_id}.json?$limit={n}&$offset=0&$order=:id
```

### Como encontrar un dataset:
1. Ingrese a [datos.gov.co](https://www.datos.gov.co/).
2. Localice cualquier conjunto de datos publico.
3. El ID del recurso es el codigo alfanumerico de 8 o 9 caracteres (ejemplo: `gt2j-8ykr` o `cfw2-7bit`) que aparece en la URL del conjunto de datos o en el boton "API".
4. Puede ingresar tanto el ID corto (`gt2j-8ykr`) como una URL HTTPS de `datos.gov.co` que termine en el identificador. El analizador valida el dominio y el formato del ID.

---

## Patrones de Reactividad y Rendimiento

1. **Cero trabajo pesado en el hilo de renderizado**:
   Todas las transformaciones de Pandas, filtros y computos de SciPy se ejecutan en funciones de servicio independientes.
2. **Memorizacion de calculos (`@reactive.calc`)**:
   Los modulos que consumen agregaciones o matrices computan el resultado una unica vez por ciclo de actualizacion. Si el usuario cambia un filtro estetico que no altera los datos fuente, el calculo se reutiliza desde cache.
3. **Manejo de memoria en sesion**:
   El estado se mantiene en objetos `reactive.value()` pertenecientes al contexto de cada sesion individual, impidiendo la contaminacion de memoria entre diferentes usuarios.
4. **Diseno CSS desacoplado**:
   El archivo `www/styles.css` es servido como asset estatico nativo por el servidor ASGI, sin inyectar bloques pesados de HTML o strings embebidos en el codigo de Python.

---

## Instalacion y Ejecucion

### Requisitos previos
- Python 3.10 o superior instalado.

### 1. Clonar o acceder a la carpeta del proyecto
```bash
cd "Shiny APP Python"
```

### 2. Instalar dependencias
Puede instalar via `requirements.txt`:
```bash
pip install -r requirements.txt
```
O utilizando el paquete editable configurado en `pyproject.toml`:
```bash
pip install -e .
```

### 3. Iniciar la aplicacion
```bash
shiny run app.py --port 8000 --reload
```
Acceda en su navegador web a:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Suite de Pruebas Automatizadas

La arquitectura permite ejecutar pruebas de extremo a extremo sobre la logica de negocio en milisegundos mediante `pytest`, sin necesidad de simular navegadores web ni levantar servidores:

```bash
pytest -v
```

Casos de prueba cubiertos en `tests/test_services.py`:
- `test_extract_resource_id_from_url`: Verifica la extraccion de IDs desde URLs directas, URLs de vistas y cadenas simples.
- `test_classify_columns_mixed_dataframe`: Verifica la correcta tipificacion de variables mixtas.
- `test_compute_dataset_overview`: Verifica las metricas de completitud y recuento celular.
- `test_compute_correlation_matrix`: Verifica la matriz de correlacion de Pearson.
- `test_compute_normality_tests`: Valida la ejecucion de la prueba Shapiro-Wilk sobre distribuciones sinteticas.
- `test_compute_categorical_summary`: Valida la identificacion de modas y conteos de frecuencia.

---

## Configuracion y Personalizacion

Para modificar parametros globales, edite el archivo `config.py`:
- `DEFAULT_FETCH_ROWS`: Numero predeterminado de filas a consultar (por defecto: 5,000).
- `DEFAULT_MAX_ROWS`: Limite maximo de seguridad permitido para evitar saturar memoria (por defecto: 50,000).
- `API_TIMEOUT_SECONDS`: Tiempo de espera en segundos para las peticiones HTTP a datos.gov.co (por defecto: 30 segundos).
- `SAMPLE_DATASETS`: Diccionario con los conjuntos de datos sugeridos que aparecen en el selector inicial.
