import subprocess
import os
import csv
import itertools
import numpy as np
from visualizar_auto import graficar_nf, graficar_pr, graficar_phi
from visualizar_plots import graficar_omr_gam
from lectura_archivos import leer_farprt, crear_input_model

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS Y CARPETAS
# ==========================================
CARPETA_SIMULACION = "DIIID_1"
EJECUTABLE_WSL = "wsl"
EJECUTABLE_FAR3D = "./xfar3d"
TEMPLATE_FILE_PATH = os.path.join(CARPETA_SIMULACION, "Input_Model_Template")
INPUT_FILE_PATH = os.path.join(CARPETA_SIMULACION, "Input_Model")
OUTPUT_FILE_PATH = os.path.join(CARPETA_SIMULACION, "farprt")
CSV_PATH = "tasa_frecuencia_del_modo.csv"



# ==========================================
# FUNCIÓN DE EJECUCIÓN (CON WSL Y CWD)
# ==========================================
def ejecutar_programa():
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
            cwd=CARPETA_SIMULACION
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError en la simulación FAR3D. Salida de error:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("\nError: No se encontró el comando WSL o la ruta especificada.")
        return False


# ==========================================
# FUNCIONES DE BASE DE DATOS (CSV)
# ==========================================
def guardar_en_csv(csv_path, parametros, lista_resultados):
    """Guarda los resultados en formato largo (múltiples filas por ejecución)."""
    if not lista_resultados:
        return

    archivo_existe = os.path.exists(csv_path)
    cabeceras = list(parametros.keys()) + list(lista_resultados[0].keys())

    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cabeceras)

        if not archivo_existe or os.stat(csv_path).st_size == 0:
            writer.writeheader()

        for resultado in lista_resultados:
            fila_completa = {**parametros, **resultado}
            writer.writerow(fila_completa)


# ==========================================
# BUCLE PRINCIPAL
# ==========================================
def main():
    # --- MAPEO DE PARÁMETROS ---
    valores_s = ["5.e6"]
    valores_bet0_f = np.arange(0, 0.002, 0.0005)     # [0, 0.002]
    # valores_bet0_f = np.linspace(0.0001, 0.002, 2)
    valores_beam_temp = []

    print(f"Iniciando automatización. Usando carpeta objetivo: '{CARPETA_SIMULACION}'\n")
    for s_val, beta_val in itertools.product(valores_s, valores_bet0_f):
        parametros_actuales = {
            "s": s_val,
            "bet0_f": beta_val
        }

        print(f"Lanzando simulación con: {parametros_actuales} ... ", end="", flush=True)

        # 1. Crear el Input_Model.txt dentro de DIIID
        crear_input_model(parametros_actuales, TEMPLATE_FILE_PATH, INPUT_FILE_PATH)

        # 2. Ejecutar FAR3d dentro de DIIID
        exito = ejecutar_programa()

        if exito:
            # 3. Leer el farprt generado
            lista_resultados = leer_farprt(OUTPUT_FILE_PATH)

            # CREAR GRÁFICAS DE LAS AUTOFUNCIONES (nf, pr, phi)
            if parametros_actuales["bet0_f"] == min(valores_bet0_f):
                valor = parametros_actuales["bet0_f"]
                graficar_nf(file_path="DIIID/nf_0000", file_name=f"grafica_nfmin", bet0_f=valor)
                graficar_pr(file_path="DIIID/pr_0000", file_name=f"grafica_prmin", bet0_f=valor)
                graficar_phi(file_path="DIIID/phi_0000", file_name=f"grafica_phimin", bet0_f=valor)

            elif parametros_actuales["bet0_f"] == max(valores_bet0_f):
                valor = parametros_actuales["bet0_f"]
                graficar_nf(file_path="DIIID/nf_0000", file_name=f"grafica_nfmax", bet0_f=valor)
                graficar_pr(file_path="DIIID/pr_0000", file_name=f"grafica_prmax", bet0_f=valor)
                graficar_phi(file_path="DIIID/phi_0000", file_name=f"grafica_phimax", bet0_f=valor)

            # 4. Escribir datos en el CSV raíz
            guardar_en_csv(CSV_PATH, parametros_actuales, lista_resultados)

            print(f"OK. Extraídas {len(lista_resultados)} variables.")

            # 5. Limpieza: borramos farprt para evitar lecturas fantasmas en caso de fallo futuro
            # if os.path.exists(OUTPUT_FILE_PATH):
            #   os.remove(OUTPUT_FILE_PATH)
        else:
            print("FALLO. Saltando a la siguiente combinación.")

    print(f"\nAutomatización completada. Resultados guardados en: {CSV_PATH}")

    print(f"\nGraficar Tasas de crecimiento y Frecuencias de los modos según la variable física")
    graficar_omr_gam(CSV_PATH)
    print(f"\nGráficas completadas. OK")


if __name__ == "__main__":
    main()