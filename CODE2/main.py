"""
---------------- CREAR BASE DE DATOS (CSV) LANZANDO SIMULACIONES -------------------


"""

import itertools

import numpy as np

from InputManager import InputManager
from ExecutionEngine import ExecutionEngine
from OutputParser import OutputParser
from DataManager import DataManager

# --- Inicializamos nuestros módulos ---
target_directory = "./DIIID"
template_directory = "./Templates_DIIID"
db_csv = "./simulations_results.csv"
manager = InputManager(template_dir=template_directory, output_dir=target_directory)
engine = ExecutionEngine(work_dir=target_directory)
parser = OutputParser(work_dir=target_directory)

# Definimos el "espacio de búsqueda"
input_model_grid = {
    'bet0_f': np.linspace(0.001, 0.02, 11),
    'maxstp': [2500],
    'EP_dens_on': [0],
    'Bdens': [0.1],
    'Adens': [7]
}

data_txt_grid = {
    'Beam Ion Effective Temp(keV)': [0, 10, 20, 30, 40, 50]
    # 'Ion Temp(keV)': [0],
    # 'Thermal Pressure(kPa)': [0],
    # 'Tor Rot(km/s)': [0]
}

# Calcular automáticamente los límites (mínimo, máximo) de todas las variables
grid_bounds = {}
for k, v_list in {**input_model_grid, **data_txt_grid}.items():
    grid_bounds[k] = (min(v_list), max(v_list))

# --- MODOS TOROIDALES Y POLOIDALES ---
nn = [1,2,3,4,5]
dicc_nm = {1: [1,2,3,4,5],
           2: [4,5,6,7,8,9,10],
           3: [6,7,8,9,10,11,12,13,14,15],
           4: [8,9,10,11,12,13,14,15,16,17,18,19,20],
           5: [10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]
           }


# --- Preparamos las combinaciones ---
# Juntamos todos los nombres (keys) y todas las listas de valores (values)
# itertools.product genera todas las combinaciones posibles
all_keys = list(input_model_grid.keys()) + list(data_txt_grid.keys())
all_values_lists = list(input_model_grid.values()) + list(data_txt_grid.values())
todas_las_combinaciones = list(itertools.product(*all_values_lists))

# Inicializar el DataManager
data_manager = DataManager(csv_path=db_csv, keys=all_keys)

print(f"[*] Total de simulaciones: {len(todas_las_combinaciones)} x {len(nn)} (por cada modo n) \n")

# --- Bucle de ejecución automatizada ---
for run_id, combinacion_actual in enumerate(todas_las_combinaciones):

    current_input_vars = dict(zip(all_keys[:len(input_model_grid)], combinacion_actual[:len(input_model_grid)]))
    current_data_vars = dict(zip(all_keys[len(input_model_grid):], combinacion_actual[len(input_model_grid):]))

    # Lanzar 1 simulación por cada n
    for n in nn:
        print(f"--- [Iniciando Simulación {run_id}] ---")

        # PREPARACIÓN DE ENTRADAS
        mm = dicc_nm[n]    # Coger los modos poloidales correspondientes
        manager.modify_input_model('Input_Model', 'Input_Model', current_input_vars, nn_val=n, mm_vals=mm)
        manager.modify_data_txt('Data.txt', 'Data.txt', current_data_vars)

        # EJECUCIÓN
        # Le ponemos un timeout de 180 segundos por ejemplo
        exec_result = engine.run_simulation(run_id=run_id, timeout_seconds=180)

        if exec_result['status'] == "SUCCESS":
            print(f"    [*] Procediendo a la extracción de datos...")

            # MÓDULO 3: EXTRACCIÓN DE RESULTADOS
            datos_simulacion = parser.parse_csv()

            # Comprobación de seguridad
            escalares = datos_simulacion['escalares']
            if escalares:
                print(
                    f"    [+] Datos extraídos para n= {n}: gam = {escalares.get('gam', 'N/A')}, om_r = {escalares.get('om_r', 'N/A')},"
                    f" gam_var = {escalares.get('gam_var', 'N/A')}, om_r_var = {escalares.get('om_r_var', 'N/A')}")
            else:
                print("    [-] La simulación terminó, pero no se encontraron las variables gam/om_r en farprt.")


            # ASIGNAR ETIQUETA



            # GUARDADO EN BASE DE DATOS / CSV
            input_summary = {**current_input_vars, **current_data_vars, "n": n}
            data_manager.save_simulation(input_summary, escalares)
            print(f"    [OK] Simulación {run_id} registrada")
        else:
            print(f"    [!] Simulación omitida en BD debido a un fallo. Revisa los logs.")

        print("-" * 50 + "\n")