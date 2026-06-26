# 🔬 Automatización y Gemelo Digital para FAR3d (TFG)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458.svg)](https://pandas.pydata.org/)
[![Fortran](https://img.shields.io/badge/Fortran-FAR3d-734F96.svg)](#)

Repositorio oficial del Trabajo Fin de Grado (TFG) de [Miguel Ángel Suárez](https://github.com/miguelangel-suarez). 

Este proyecto desarrolla una plataforma integral en Python para la automatización, paralelización (HPC), visualización y etiquetado físico de simulaciones del código MHD **FAR3d** (código de simulación de plasmas de fusión). La herramienta actúa como un **Gemelo Digital**, permitiendo realizar barridos paramétricos masivos y clasificar topológicamente las inestabilidades de Alfvén (TAE, BAE, RSAE, GAE, etc.) preparándolas para futuros modelos de Machine Learning.

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
El código FAR3d es una potente herramienta escrita en Fortran para estudiar inestabilidades magnetohidrodinámicas en reactores de fusión. Sin embargo, su uso manual y el análisis de sus salidas de texto complican los estudios a gran escala.

Este proyecto resuelve ese cuello de botella proporcionando:
* **Paralelización Inteligente:** Arquitectura *Worker-Dispatcher* para lanzar decenas de simulaciones simultáneas evitando colisiones de disco.
* **Orquestación Paramétrica:** Modificación dinámica del espectro de ondas (modos poloidales $m$ y toroidales $n$).
* **Etiquetado Físico Autónomo:** Un algoritmo que cruza la matriz de la autofunción con la nube de puntos del **espectro del continuo**, detectando amortiguamiento (Continuum Damping), calculando el gap topológico y diagnosticando automáticamente el tipo de inestabilidad (TAE, BAE, RSAE, etc.).
* **Dashboard Interactivo:** Interfaz web para analizar hipercubos de datos mediante Mapas de Calor (Heatmaps) y lanzar simulaciones locales al instante.

---

## 📂 Estructura del Repositorio

La totalidad del desarrollo de software de este TFG se encuentra dentro del directorio **`CODE/`**.

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
