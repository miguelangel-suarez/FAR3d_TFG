"""
---------------- AUTOMATIZACIÓN DE FAR3D -------------------
Bloque Orquestados para Generar de forma automática y en paralelo las distintas simulaciones
con FAR3d. Se implementa el Pipeline completo de los datos y su guardado en distintas
bases de datos (una por cada n)

"""

import itertools
import os
import numpy as np
import pandas as pd
import concurrent.futures

from InputManager import InputManager
from ExecutionEngine import ExecutionEngine
from OutputParser import OutputParser
from DataManager import DataManager
from AutoLabeler import SimulationLabeler


# ---------------------------------------------------------
# FUNCIÓN DEL TRABAJADOR (Ejecutada en paralelo)
# ---------------------------------------------------------
def worker_simulacion_por_n(n, mm_vals, combinaciones, all_keys, len_input, template_dir, csv_continuo):
    """
    Este worker se encarga de procesar TODAS las combinaciones de la malla
    pero única y exclusivamente para un valor de 'n' específico.
    Trabaja en su propia carpeta aislada (ej: "DIIID_4" para n=4)
    """
    # Definimos el entorno aislado para este 'n'
    target_directory = f"./DIIID_{n}"
    db_csv = os.path.join(target_directory, "data.csv")

    # Instanciamos los módulos apuntando EXCLUSIVAMENTE a la carpeta del worker
    manager = InputManager(template_dir=template_dir, output_dir=target_directory)
    engine = ExecutionEngine(work_dir=target_directory)
    parser = OutputParser(work_dir=target_directory)
    data_manager = DataManager(csv_path=db_csv, keys=all_keys)
    labeler = SimulationLabeler()

    print(f"[*] Worker [n={n}] INICIADO en {target_directory} -> Procesará {len(combinaciones)} simulaciones.")

    for run_id, combinacion_actual in enumerate(combinaciones):
        # Separar las variables del Input_Model y del Data_txt
        current_input_vars = dict(zip(all_keys[:len_input], combinacion_actual[:len_input]))
        current_data_vars = dict(zip(all_keys[len_input:], combinacion_actual[len_input:]))

        # MÓDULO 1: PREPARACIÓN DE ENTRADAS
        manager.modify_input_model('Input_Model', 'Input_Model', current_input_vars, nn_val=n, mm_vals=mm_vals)
        manager.modify_data_txt('Data.txt', 'Data.txt', current_data_vars)

        # MÓDULO 2: EJECUCIÓN
        exec_result = engine.run_simulation(run_id=run_id, timeout_seconds=1800)

        if exec_result['status'] == "SUCCESS":

            # MÓDULO 3: EXTRACCIÓN DE RESULTADOS
            datos_simulacion = parser.parse_csv()
            escalares = datos_simulacion.get("escalares", {})
            df_phi = datos_simulacion.get("phi_0000")
            df_profile = datos_simulacion.get("profiles")
            df_continuo = pd.read_csv(csv_continuo)

            # MÓDULO 4: ASIGNAR ETIQUETA
            etiqueta = labeler.generate_label(
                escalares=escalares,
                df_phi=df_phi,
                df_continuo=df_continuo,
                df_prof=df_profile
            )

            # MÓDULO 5: GUARDADO EN EL CSV PROPIO DEL WORKER
            input_summary = {**current_input_vars, **current_data_vars, "n": n}
            data_manager.save_simulation(input_summary, escalares, etiqueta)

            print(f"    [+] [n={n}] Simulación {run_id} EXITOSA: Freq={etiqueta.get('om_r')}, Tasa={etiqueta.get('gamma')} "
                  f"Inestabilidad={etiqueta.get('tipo_inestabilidad')}")

        else:
            print(f"    [!] [n={n}] Simulación {run_id} OMITIDA (Fallo ejecución).")

    return f"[OK] Worker [n={n}] ha terminado todas sus simulaciones."


# ---------------------------------------------------------
# ORQUESTADOR PRINCIPAL
# ---------------------------------------------------------
def main():
    TEMPLATE_DIR = "./Templates_DIIID"
    CSV_CONTINUO = "./espectros_continuos_Alfven/df_continuo.csv"

    # Definimos el "espacio de búsqueda"
    input_model_grid = {
        'bet0_f': np.linspace(0.001, 0.04, 11),
        'maxstp': [2500],
        'EP_dens_on': [1],
        'Bdens': [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8],
        'Adens': [0.5, 2, 4, 6, 8, 10]
    }

    data_txt_grid = {
        'Beam Ion Effective Temp(keV)': [0, 20, 40, 60, 80, 100]
    }

    # --- MODOS TOROIDALES Y POLOIDALES ---
    nn = [1, 2, 3, 4, 5]
    dicc_nm = {
        1: [2, 3, 4, 5],
        2: [4, 5, 6, 7, 8, 9, 10],
        3: [6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        4: [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        5: [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
    }

    # --- Preparamos las combinaciones ---
    all_keys = list(input_model_grid.keys()) + list(data_txt_grid.keys())
    all_values_lists = list(input_model_grid.values()) + list(data_txt_grid.values())
    todas_las_combinaciones = list(itertools.product(*all_values_lists))

    print(f"[*] Total de combinaciones base a ejecutar: {len(todas_las_combinaciones)}")
    print(f"[*] Iniciando 5 procesos paralelos (uno por cada valor de n)...\n")

    # --- LANZAMIENTO EN PARALELO ---
    with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
        futuros = []

        for n in nn:
            modos_m = dicc_nm[n]
            futuro = executor.submit(
                worker_simulacion_por_n,
                n,
                modos_m,
                todas_las_combinaciones,
                all_keys,
                len(input_model_grid),
                TEMPLATE_DIR,
                CSV_CONTINUO
            )
            futuros.append(futuro)

        # Esperamos a que todos terminen y mostramos su mensaje de finalización
        for futuro in concurrent.futures.as_completed(futuros):
            print(futuro.result())

    print("\n[✔] TODAS LAS SIMULACIONES HAN FINALIZADO.")


if __name__ == '__main__':
    main()