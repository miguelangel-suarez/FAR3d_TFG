import os
import csv
import shutil
import subprocess
import itertools
import numpy as np
from visualizar_plots import graficar_omr_gam
from lectura_archivos import leer_farprt, crear_input_model, guardar_en_csv

# ==========================================
# 0. VARIABLES GLOBALES
# ==========================================

DIR_SIMULACION = "DIIID"
DIR_SIMULACIONES_GUARDADAS = "DIIID_0"
EJECUTABLE_WSL = "wsl"
EJECUTABLE_FAR3D = "./xfar3d"
TEMPLATE_FILE_PATH = os.path.join(DIR_SIMULACION, "Input_Model_Template")
INPUT_MODEL_PATH = os.path.join(DIR_SIMULACION, "Input_Model")
FARPRT_PATH = os.path.join(DIR_SIMULACION, "farprt")
CSV_PATH = "base_de_datos.csv"

# ==========================================
# 1. FUNCIONES PLACEHOLDER
# ==========================================

def ejecutar_FAR3d():
    """Ejecuta FAR3D a través de WSL dentro de la carpeta especificada."""
    try:
        comando = [EJECUTABLE_WSL, EJECUTABLE_FAR3D]

        # El parámetro cwd=CARPETA_SIMULACION le dice a WSL que se ubique
        # dentro de la carpeta DIIID antes de lanzar ./far3d
        subprocess.run(
            comando,
            capture_output=True,
            text=True,
            check=True,
            cwd=DIR_SIMULACION
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError en la simulación FAR3D. Salida de error:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("\nError: No se encontró el comando WSL o la ruta especificada.")
        return False


def es_configuracion_significativa(config, diccionario_params):
    """
    Determina si una configuración es significativa.
    Retorna True SOLO si TODOS los parámetros están en su valor mínimo o máximo.
    Si algún parámetro tiene un valor intermedio, retorna False.
    """
    for nombre, valor_actual in config.items():
        # Recuperamos la lista de todos los valores posibles para este parámetro
        valores_posibles = diccionario_params[nombre]

        # Obtenemos los extremos de esa lista
        valor_minimo = min(valores_posibles)
        valor_maximo = max(valores_posibles)

        # Comprobamos si el valor actual es un valor intermedio
        if valor_actual != valor_minimo and valor_actual != valor_maximo:
            return False  # Al encontrar un intermedio, descartamos toda la configuración

    # Si logramos salir del bucle, significa que todos los valores
    # de esta configuración estaban en los extremos (min o max)
    return True


# ==========================================
# 2. LÓGICA PRINCIPAL DE LA AUTOMATIZACIÓN
# ==========================================

def recolectar_parametros():
    """Genera el cuestionario por terminal para configurar las variables."""
    def valores(partes):
        vmin = float(partes[0].strip())
        vmax = float(partes[1].strip())
        num_valores = int(partes[2].strip())

        valores = np.linspace(vmin, vmax, num_valores)
        return [round(float(v), 4) for v in valores]  # Redondeo por limpieza

    print("=== CONFIGURACIÓN DE PARÁMETROS DE SIMULACIÓN ===")
    print("\n--- RANGOS DE PARÁMETROS---")
    parametros = {}
    for var in ["bet0_f", "s"]:
        entrada = input(f"{var} (MIN, MAX, NºVALORES) -> ")
        partes = entrada.split(",")
        parametros[var] = valores(partes)
        print(f"  -> Valores generados: {parametros[var]}")

    print("\n--- MULTIPLICIDAD DE PARÁMETROS---")
    for var in ["BEAM ION EFFECTIVE TEMP"]:
        entrada = input(f"{var}(FACTORES DE MULTIPLICIDAD) -> ")
        factores = [float(valor.strip()) for valor in entrada.split(',')]
        parametros[var] = factores
        print(f"  -> Valores generados: {parametros[var]}")

    return parametros


def main():
    # 1. Cuestionario en terminal
    diccionario_params = recolectar_parametros()

    nombres_params = list(diccionario_params.keys())
    listas_valores = list(diccionario_params.values())

    # Generar todas las combinaciones posibles (Grid)
    combinaciones = list(itertools.product(*listas_valores))
    print(f"\n[INFO] Se ejecutarán un total de {len(combinaciones)} simulaciones.")

    # Eliminar carpeta de simulaciones guardadas (para nuevas simulaciones)
    # if os.path.exists(DIR_SIMULACIONES_GUARDADAS):
        # os.remove(DIR_SIMULACIONES_GUARDADAS)

    # 4. Bucle principal de iteración
    for indice, combo in enumerate(combinaciones, start=1):
        # Emparejar nombres con valores actuales
        config_actual = dict(zip(nombres_params, combo))
        print(f"\n--- Ejecutando simulación {indice}/{len(combinaciones)} ---")
        print(f"Configuración: {config_actual}")

        # 1. Crear el Input_Model.txt dentro de DIIID
        crear_input_model(config_actual, TEMPLATE_FILE_PATH, INPUT_MODEL_PATH)
        
        # A. Lanzar simulación
        exito = ejecutar_FAR3d()
        
        if exito:
            # B. Leer resultados del output de la carpeta temporal
            lista_resultados = leer_farprt(FARPRT_PATH)
            # C. Guardar configuracion y resultados en CSV
            guardar_en_csv(CSV_PATH, config_actual, lista_resultados)
    
            # D. Guardar carpeta si es significativa
            if es_configuracion_significativa(config_actual, diccionario_params):
                # Crear un nombre único basado en los parámetros
                str_params = "_".join([f"{k}-{v}" for k, v in config_actual.items()])
                nombre_carpeta_dest = f"DIIID_{str_params}"
                ruta_dest = os.path.join(DIR_SIMULACIONES_GUARDADAS, nombre_carpeta_dest)
    
                # Si ya existe (raro si los params son únicos, pero por seguridad), la borramos
                if os.path.exists(ruta_dest):
                    shutil.rmtree(ruta_dest)
    
                # Copiar la carpeta temporal a la carpeta de guardado
                shutil.copytree(DIR_SIMULACION, ruta_dest)
                print(f"  [!] Simulación significativa guardada en: {ruta_dest}")
        else:
            print("FALLO. Saltando a la siguiente combinación.")

    # 5. Fase final: Graficar
    print("\n[INFO] Bucle de simulaciones terminado.")
    graficar_omr_gam(CSV_PATH)
    print(f"\n[INFO] Gráficas completadas. OK")


if __name__ == "__main__":
    main()