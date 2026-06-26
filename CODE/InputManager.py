"""
---------------- REALIZAR CAMBIOS EN LOS ARCHIVOS INPUT, PREVIOS A LA SIMULACIÓN -------------------
Modificación de los archivos "Data.txt" y "Input_Model" según los parámetros indicados a cambiar

Para futuras líneas de desarrollo, implementar nuevas lecturas de los archivos de entrada puede ser
un punto importante de partida (junto con el OutputParser.py)

"""

import os
import re
import shutil


class InputManager:
    def __init__(self, template_dir, output_dir):
        """
        Inicializa el gestor de entradas
        """
        self.template_dir = template_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def modify_input_model(self, template_filename, output_filename, variables, nn_val, mm_vals):
        """
        Modifica variables escalares en el Input_Model, ej: {'bet0_f': 0.002}
        """
        # 1. Preparar las listas de modos
        mm_desc = sorted(mm_vals, reverse=True)
        num_dyn = len(mm_desc)
        num_eq = 11  # 11 modos de equilibrio iniciales

        # 2. Construir las cadenas exactas para Fortran
        mm_pos_str = ",".join(map(str, mm_desc)) + ","
        mm_neg_str = ",".join(map(lambda x: str(-x), mm_desc)) + ","
        mm_eq_str = "0,1,2,3,4,5,6,7,8,9,10"

        # Formato de repetición de Fortran: ej. "4*1,4*-1,11*0"
        nn_str = f"{num_dyn}*{nn_val},{num_dyn}*{-nn_val},{num_eq}*0"

        # 3. Calcular la dimensión real de la malla (ldim y lplots)
        ldim = (num_dyn * 2) + num_eq
        lplots = (num_dyn * 2)
        variables["ldim"] = ldim
        variables["lplots"] = lplots
        variables["nn"] = nn_str
        template_path = os.path.join(self.template_dir, template_filename)
        output_path = os.path.join(self.output_dir, output_filename)

        with open(template_path, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith('!!!!!!!!!!! mm:'):
                lines[i + 1] = f"{mm_pos_str}\n"
                lines[i + 2] = f"{mm_neg_str}\n"
                lines[i + 3] = f"{mm_eq_str}\n"
            # Buscar líneas que definen una variable (empiezan con !!!!!!!!!!!)
            if line.startswith('!!!!!!!!!!!'):
                match = re.match(r'!!!!!!!!!!!\s*([^:]+):', line)
                if match:
                    var_name = match.group(1).strip()
                    # Si la variable está en nuestro diccionario de cambios, modificamos la siguiente línea
                    if var_name in variables:
                        lines[i + 1] = f"{variables[var_name]}\n"

        with open(output_path, 'w') as f:
            f.writelines(lines)

        print(f"[*] {output_filename} generado con éxito.")

    def modify_data_txt(self, template_filename, output_filename, column_multipliers):
        """
        Aplica multiplicadores a columnas específicas en la tabla final de Data.txt,
        ej: {'Beam Ion Effective Temp(keV)': 10}
        """
        template_path = os.path.join(self.template_dir, template_filename)
        output_path = os.path.join(self.output_dir, output_filename)

        with open(template_path, 'r') as f:
            lines = f.readlines()

        out_lines = []
        in_table = False
        headers = []

        for line in lines:
            # Detectar el inicio de la tabla por su cabecera
            if "Rho(norml. sqrt. toroid. flux)" in line:
                in_table = True
                # Limpiar y guardar los nombres de las columnas
                headers = [h.strip() for h in line.split(',')]
                out_lines.append(line)
                continue

            # Si estamos dentro de la tabla y la línea tiene datos
            if in_table and line.strip() and not line.startswith('['):
                parts = line.split()

                # Nos aseguramos de que la línea tiene el mismo número de elementos que la cabecera
                if len(parts) == len(headers):
                    for col_name, multiplier in column_multipliers.items():
                        if col_name in headers:
                            idx = headers.index(col_name)
                            # SUMAR y formatear para mantener el estilo
                            original_val = float(parts[idx])
                            new_val = original_val + multiplier
                            # Usamos %g para evitar ceros innecesarios o notación científica extrema si no es requerida
                            parts[idx] = f"{new_val:g}"

                            # Reconstruir la línea uniendo con espacios
                    out_lines.append(" " + " ".join(parts) + "  \n")
                else:
                    out_lines.append(line)
            else:
                out_lines.append(line)

        with open(output_path, 'w') as f:
            f.writelines(out_lines)

        print(f"[*] {output_filename} generado con éxito.")

    def copiar_archivos_vitales(self):
        archivos_extra = ["xfar3d", "Eq_DIIID_RS"]

        for archivo in archivos_extra:
            ruta_origen = os.path.join(self.template_dir, archivo)
            ruta_destino = os.path.join(self.output_dir, archivo)

            if os.path.exists(ruta_origen):
                shutil.copy2(ruta_origen, ruta_destino)
            else:
                print(f"Advertencia: No se encontró el archivo '{archivo}' en la carpeta de templates.")