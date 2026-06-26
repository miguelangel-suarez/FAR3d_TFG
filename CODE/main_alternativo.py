"""
---------------- AUTOMATIZACIÓN DE FAR3D 2.0 -------------------
Bloque Orquestador Alternativo de FAR3d, donde la paralelización se realiza a nivel de cada n,
pudiendo desplegar un grupo numeroso de "workers" que trabajarán sobre sus propias carpetas de trabajo
para lanzar las simulaciones de FAR3d.

Tanto este archivo como el "main.py" realizan las mismas funciones finales, siendo simplemente distintos
medios para automatizar la generación de una base de datos masiva.

"""

import itertools
import os
import numpy as np
import pandas as pd
import concurrent.futures
import multiprocessing

from InputManager import InputManager
from ExecutionEngine import ExecutionEngine
from OutputParser import OutputParser
from DataManager import DataManager
from AutoLabeler import SimulationLabeler


# ---------------------------------------------------------
# 1. FUNCIÓN DEL TRABAJADOR
# ---------------------------------------------------------
def worker_una_simulacion(task_id, combinacion, n_val, mm_vals, all_keys, len_input, template_dir, csv_continuo_path):
    """
    Ejecuta UNA única combinación de parámetros.
    Retorna un diccionario con los inputs, los escalares de salida y la etiqueta.
    """
    # 1. Crear entorno aislado usando el ID del proceso del SO
    pid = multiprocessing.current_process().pid
    worker_dir = f"./n=2_workers/worker_{pid}"
    os.makedirs(worker_dir, exist_ok=True)

    # Preparamos el diccionario de resultados base
    resultado_final = {'task_id': task_id, 'n': n_val, 'mm': str(mm_vals), 'error': False}

    try:
        # 2. Separar la combinación en inputs para Input_Model y DATA.txt
        input_model_vals = combinacion[:len_input]
        data_txt_vals = combinacion[len_input:]
        dict_input = dict(zip(all_keys[:len_input], input_model_vals))
        dict_data = dict(zip(all_keys[len_input:], data_txt_vals))

        # Guardamos los inputs en el resultado
        resultado_final.update(dict_input)
        resultado_final.update(dict_data)

        # 3. Configurar archivos en la carpeta aislada
        manager = InputManager(template_dir=template_dir, output_dir=worker_dir)
        manager.copiar_archivos_vitales()
        manager.modify_input_model("Input_Model", "Input_Model", dict_input, n_val, mm_vals)
        manager.modify_data_txt("Data.txt", "Data.txt", dict_data)

        # 4. Ejecutar simulación FAR3d
        engine = ExecutionEngine(work_dir=worker_dir)
        engine.run_simulation()

        # 5. Parsear resultados
        parser = OutputParser(work_dir=worker_dir)
        resultados_raw = parser.parse_csv()

        # 6. Etiquetado automático
        df_continuo = pd.read_csv(csv_continuo_path) if os.path.exists(csv_continuo_path) else None
        escalares = resultados_raw.get("escalares")

        labeler = SimulationLabeler()
        etiqueta = labeler.generate_label(
            escalares=escalares,
            df_phi=resultados_raw.get("phi_0000"),
            df_continuo=df_continuo,
            df_prof=resultados_raw.get("profiles")
        )

        # 7. Combinar los resultados extraídos
        resultado_final.update({
            'gam': escalares.get('gam', 0.0),
            'om_r': escalares.get('om_r', 0.0),
            'gam_var': escalares.get('gam_var', 0.0),
            'om_r_var': escalares.get('om_r_var', 0.0),
        })
        resultado_final.update(etiqueta)

    except Exception as e:
        print(f"[!] Error en Task {task_id} (PID {pid}): {str(e)}")
        resultado_final['error'] = True

    return task_id, resultado_final


# ---------------------------------------------------------
# 2. HILO PRINCIPAL
# ---------------------------------------------------------
if __name__ == "__main__":

    # --- CONFIGURACIÓN DEL EXPERIMENTO ---
    # Modificar según las necesidades de los experimentos
    N_VAL = 2
    MM_VALS = [4, 5, 6, 7, 8, 9, 10]
    MAX_WORKERS = 8

    TEMPLATE_DIR = "./Templates_DIIID"
    CSV_CONTINUO = "./espectros_continuos_Alfven/df_continuo.csv"
    OUTPUT_CSV = "./n=2_workers/data.csv"

    # Crear carpeta de trabajadores
    os.makedirs("./n=2_workers", exist_ok=True)

    # --- DEFINICIÓN DE LA MALLA PARAMÉTRICA ---
    input_model_grid = {
        'bet0_f': np.linspace(0.001, 0.04, 11),
        'maxstp': [2500],
        'EP_dens_on': [1],
        'Bdens': [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8],
        'Adens': [0.5, 2, 4, 6, 8, 10]
    }

    data_txt_grid = {
        "Beam Ion Effective Temp(keV)": [0, 20, 40, 60, 80, 100]
    }

    # Procesar las claves
    all_keys = list(input_model_grid.keys()) + list(data_txt_grid.keys())
    all_values_lists = list(input_model_grid.values()) + list(data_txt_grid.values())

    todas_las_combinaciones = list(itertools.product(*all_values_lists))
    total_sims = len(todas_las_combinaciones)

    print(f"\n==================================================")
    print(f"[*] MODO: Barrido Paramétrico (n={N_VAL})")
    print(f"[*] Total de combinaciones generadas: {total_sims}")
    print(f"[*] Lanzando en {MAX_WORKERS} hilos simultáneos...")
    print(f"==================================================\n")

    # Inicializamos el gestor de datos principal para el CSV
    data_manager = DataManager(csv_path=OUTPUT_CSV, keys=all_keys)

    # --- LANZAMIENTO EN PARALELO ---
    simulaciones_ok = 0
    simulaciones_err = 0

    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 1. Enviar todos los trabajos al Pool
        futuros = {}
        for i, comb in enumerate(todas_las_combinaciones):
            futuro = executor.submit(
                worker_una_simulacion,
                i, comb, N_VAL, MM_VALS, all_keys, len(input_model_grid), TEMPLATE_DIR, CSV_CONTINUO
            )
            futuros[futuro] = i

        # 2. Recibir los resultados según vayan terminando
        for futuro in concurrent.futures.as_completed(futuros):
            task_id = futuros[futuro]
            try:
                # Obtenemos el diccionario resultante del trabajador
                task_id_res, resultado_dict = futuro.result()

                if resultado_dict.get('error'):
                    simulaciones_err += 1
                else:
                    # ESCRITURA SEGURA EN DISCO (Centralizada en el Hilo Main)
                    col_inputs = {"bet0_f", "maxstp", "EP_dens_on", "Bdens", "Adens", "Beam Ion Effective Temp(keV)"}
                    col_escalares = {"gam", "om_r", "gam_var", "om_r_var"}
                    col_etiqueta = {"tipo_inestabilidad", "modo_m", "pos_radial", "diff_m"}

                    # 2. Creamos los 3 diccionarios usando comprensión
                    inputs = {k: resultado_dict[k] for k in col_inputs if k in resultado_dict}
                    inputs["n"] = N_VAL
                    escalares = {k: resultado_dict[k] for k in col_escalares if k in resultado_dict}
                    etiqueta = {k: resultado_dict[k] for k in col_etiqueta if k in resultado_dict}
                    data_manager.save_simulation(inputs=inputs, escalares=escalares, etiqueta=etiqueta)
                    simulaciones_ok += 1

                print(
                    f"[{simulaciones_ok + simulaciones_err}/{total_sims}] Simulación {task_id_res} completada. (Estabilidad: {resultado_dict.get('tipo_inestabilidad', 'N/A')})")

            except Exception as exc:
                print(f"[!] Tarea {task_id} generó una excepción crítica: {exc}")
                simulaciones_err += 1

    print(f"\n--- BARRIDO COMPLETADO ---")
    print(f"[*] Éxitos: {simulaciones_ok}")
    print(f"[*] Fallos: {simulaciones_err}")
    print(f"[*] Base de datos guardada en: {OUTPUT_CSV}")
