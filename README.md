# 🔬 Automatización y Gemelo Digital para FAR3d (TFG)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458.svg)](https://pandas.pydata.org/)
[![Fortran](https://img.shields.io/badge/Fortran-FAR3d-734F96.svg)](#)

Este proyecto desarrolla una plataforma integral en Python para la automatización, paralelización (HPC), visualización y etiquetado físico de simulaciones del código MHD **FAR3d** (código de simulación de plasmas de fusión). La herramienta actúa como un **Gemelo Digital**, permitiendo realizar barridos paramétricos masivos y clasificar topológicamente las inestabilidades de Alfvén (TAE, BAE, RSAE, GAE, etc.) preparándolas para modelos de Machine Learning usados en la Detección de Inestabilidades de los Modos de ALfvén en el plasma en reactores nucleares de fusión, específicamente en el DIII-D.

---

## 📑 Índice
1. [Contexto del Proyecto](#-contexto-del-proyecto)
2. [Estructura del Repositorio](#-estructura-del-repositorio)
3. [Arquitectura del Sistema (`CODE/`)](#-arquitectura-del-sistema)
4. [Instalación y Requisitos](#-instalación-y-requisitos)
5. [Guía de Uso](#-guía-de-uso)
6. [Contacto y Autor](#-autor)

---

## 🌌 Contexto del Proyecto
El código FAR3d es una herramienta escrita en Fortran para estudiar inestabilidades magnetohidrodinámicas en reactores de fusión. Sin embargo, su uso manual y el análisis de sus salidas de texto complican los estudios a gran escala.

Este proyecto resuelve ese cuello de botella proporcionando:
* **Paralelización Inteligente:** Arquitectura *Worker-Dispatcher* para lanzar decenas de simulaciones simultáneas evitando colisiones de disco.
* **Orquestación Paramétrica:** Modificación dinámica del espectro de ondas (modos poloidales $m$ y toroidales $n$).
* **Etiquetado Físico Autónomo:** Un algoritmo que cruza la matriz de la autofunción con la nube de puntos del **espectro del continuo**, detectando amortiguamiento, calculando el gap topológico y diagnosticando automáticamente el tipo de inestabilidad (TAE, BAE, RSAE, etc.).
* **Dashboard Interactivo:** Interfaz web para analizar hipercubos de datos mediante Mapas de Calor (Heatmaps) y lanzar simulaciones locales al instante.

---

## 📂 Estructura del Repositorio

El desarrollo de software de este proyecto se encuentra dentro del directorio **`CODE/`**.

```text
FAR3d_TFG/
├── CODE/
│   ├── app.py                  # Frontend: Dashboard web interactivo (Streamlit)
│   ├── main.py                 # Orquestador HPC: Ejecución paralela masiva
│   ├── InputManager.py         # Generador dinámico de archivos Input_Model y DATA.txt
│   ├── OutputParser.py         # Extractor de amplitudes complejas, medias y varianzas
│   ├── AutoLabeler.py          # Motor de reglas físicas y clasificación de inestabilidades
│   ├── ExecutionEngine.py      # Gestor de llamadas de sistema al ejecutable FAR3d
│   ├── Visualization.py        # Módulo clásico de graficado Matplotlib (Heatmaps, Ejes Twin)
│   ├── simulaciones_guardadas/ # Repositorio de JSONs y CSVs de ejecuciones locales
│   └── templates/              # Archivos base (Input_Model_template, DATA_template.txt)
├── docs/                       # Documentación adicional y memoria del TFG
└── README.md                   # Este archivo
```

---

## ⚙️ Arquitectura del Sistema
El directorio CODE/ tiene los siguientes puntos vitales del desarrollo del proyecto de software:
- La Capa de Extracción (OutputParser.py): Utiliza expresiones regulares para identificar y unificar las partes reales e imaginarias de las ondas de las autofunciones, obteniendo el módulo/amplitud real de cada familia $m/n$. Extrae medias y varianzas de convergencia directamente de los volcados de Fortran. Todo esto para extraer los datos esenciales para el diagnóstico del plasma.
- La Capa de Etiquetado (AutoLabeler.py): Identifica el modo dominante y su acoplamiento ($\Delta m$). Luego, realiza una aproximación numérica y un slicing (rebanada) radial en el perfil del continuo de Alfvén para extraer el hueco del continuo donde cae dicha inestabilidad y clasificar la inestabilidad juntando esos 2 criterios.
- La Capa de Orquestación (main.py): Orquesta todo el pipeline de lanzamiento de las simulaciones de forma paralela entre distintos workers, leyendo datos, extrayendo los resultados y guardandolos en un archivo CSV global.
- La Capa de Interfaz (app.py): Un Dashboard iterativo compuesto por 3 capas:
-   Capa Global: Análisis de datos mediante Mallas de estabilidad (Heatmaps 2D interactivos) con superposición de varianza.
-   Capa Local: Interfaz para lanzar simulaciones individuales (modos $nn$ y $mm$), ejecutar FAR3d en segundo plano y graficar autofunciones dinámicamente.
-   Capa Simulaciones Guardadas: Repositorio JSON persistente que permite recuperar simulaciones históricas y re-visualizarlas de la misma forma que en la Capa Local.

---

## 🚀 Instalación y Requisitos
Para ejecutar este proyecto, necesitas Python 3.8 o superior. Se recomienda crear un entorno virtual para aislar las dependencias:

```Bash
# 1. Clonar el repositorio
git clone [https://github.com/miguelangel-suarez/FAR3d_TFG.git](https://github.com/miguelangel-suarez/FAR3d_TFG.git)
cd FAR3d_TFG/CODE

# 2. Crear entorno virtual (opcional pero recomendado)
python -m venv venv

# Activar el entorno virtual:
# En Linux/macOS:
source venv/bin/activate  
# En Windows:
venv\Scripts\activate

# 3. Instalar dependencias científicas y web
pip install pandas numpy matplotlib scipy streamlit
```
(Nota importante: Para poder ejecutar simulaciones de la herramienta FAR3d, debes tener disponible **WSL2 desde Windows** o trabajar desde un **entorno Linux**).

---

## 🖥️ Guía de Uso
5.1. Desplegar la Interfaz Web (Dashboard)
Para interactuar gráficamente con los datos, analizar cortes del espacio de parámetros o lanzar simulaciones individuales para observar el comportamiento de nf_0000 y phi_0000:

```Bash
cd CODE
streamlit run app.py
```
Esto iniciará un servidor local y abrirá automáticamente el Dashboard en tu navegador

5.2. Ejecutar un Barrido Paramétrico (Generación de Datos HPC)
Si deseas generar una base de datos masiva desde cero, configura las matrices de variables (input_model_grid y data_txt_grid), el número toroidal n y los modos poloidales m dentro del archivo main.py. Luego, ejecútalo:

```Bash
cd CODE
python main.py
```

---

## 👨‍💻 Contacto y Autor
Miguel Ángel Suárez: https://github.com/miguelangel-suarez/FAR3d_TFG
