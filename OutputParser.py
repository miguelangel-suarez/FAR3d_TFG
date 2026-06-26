"""
---------------- PARSEAR LOS ARCHIVOS OUTPUT (DEVOLVER DATAFRAMES Y ESCALARES) -------------------
Leer los archivos de salida de FAR3d según los requisitos del problema original y parsearlos en un Dataframe
sencillo de leer.

Para futuras expansiones de la automatización de la herramienta, expandir los archivos a leer para manejar mayor
información en proyectos que lo requieram.

"""

import os
import re
import numpy as np
import pandas as pd

FACTOR_DE_CONVERSION_FREQ = 0.5998134E+03

class OutputParser:
    def __init__(self, work_dir):
        self.work_dir = os.path.abspath(work_dir)

    def transformar_a_amplitud(self, df_raw):
        """
        Toma el DataFrame con columnas formato "R  1/ 1" o "I  3/ 1"
        y devuelve un DataFrame con la Amplitud de cada familia "m/n".
        """
        if df_raw is None or df_raw.empty:
            return None

        df_out = pd.DataFrame()
        col_radio = 'r'

        # 1. Conservar el eje X (radio)
        if col_radio in df_raw.columns:
            df_out[col_radio] = df_raw[col_radio]

        cols_datos = [c for c in df_raw.columns if c != col_radio]

        # Diccionario para organizar las parejas: {'1/1': {'R': 'R  1/ 1', 'I': 'I  1/ 1'}, ...}
        familias = {}

        # 2. Expresión regular para detectar las columnas:
        # ^([RI])   : Empieza por R o I (Grupo 1)
        # \s+       : Seguido de 1 o más espacios en blanco
        # (\d+\s*/\s*\d+) : Un número, barra (con o sin espacios) y otro número (Grupo 2)
        patron = re.compile(r"^([RI])\s+(\d+\s*/\s*\d+)$", re.IGNORECASE)

        for col in cols_datos:
            match = patron.match(col.strip())
            if match:
                tipo = match.group(1).upper()
                familia_raw = match.group(2)
                familia_clean = familia_raw.replace(" ", "")

                if familia_clean not in familias:
                    familias[familia_clean] = {}

                familias[familia_clean][tipo] = col
            else:
                df_out[col] = df_raw[col]

        # 3. Calcular la amplitud para cada familia
        for fam_clean, columnas in familias.items():
            col_R = columnas.get('R')
            col_I = columnas.get('I')

            if col_R and col_I:
                # Módulo de la onda compleja: sqrt(Re^2 + Im^2)
                df_out[fam_clean] = np.sqrt(df_raw[col_R] ** 2 + df_raw[col_I] ** 2)
            elif col_R:
                # Si por algún motivo solo hay parte real
                df_out[fam_clean] = np.abs(df_raw[col_R])
            elif col_I:
                # Si solo hay parte imaginaria
                df_out[fam_clean] = np.abs(df_raw[col_I])

        return df_out

    import os

    def extract_gam_omr(self, file="farprt"):
        """
        Extrae los valores medios y varianzas de gam y om_r directamente
        del sumario al final del archivo farprt, calculados por FAR3d.
        """
        farprt_path = os.path.join(self.work_dir, file)

        # Valores por defecto
        resultados = {
            'gam': 0.0,
            'om_r': 0.0,
            'gam_var': 0.0,
            'om_r_var': 0.0
        }

        if not os.path.exists(farprt_path):
            print(f"[!] Advertencia: Archivo {farprt_path} no encontrado.")
            return resultados

        with open(farprt_path, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        for i, linea in enumerate(lineas):
            # 1. Buscar la cabecera indicadora
            if "Avg. gam:" in linea and "Avg. om_r:" in linea:

                # 2. Leer la línea inmediatamente siguiente (n, gam_mean, om_r_mean)
                if i + 1 < len(lineas):
                    partes_medias = lineas[i + 1].split()
                    if len(partes_medias) >= 3:
                        resultados['gam'] = float(partes_medias[1])
                        resultados['om_r'] = float(partes_medias[2]) * FACTOR_DE_CONVERSION_FREQ

                # 3. Leer la línea de varianzas
                # Buscamos en las siguientes 4 líneas para ser inmunes a los saltos de línea (espacios en blanco)
                for j in range(i + 2, min(i + 6, len(lineas))):
                    partes_var = lineas[j].split()

                    # La línea de varianzas es inconfundible: tiene exactamente 2 bloques de texto
                    if len(partes_var) == 2:
                        try:
                            resultados['gam_var'] = float(partes_var[0])
                            resultados['om_r_var'] = float(partes_var[1])
                            break  # Una vez encontrados los 2 valores, dejamos de buscar
                        except ValueError:
                            continue

                # Una vez procesado el bloque, salimos del bucle principal
                break

        return resultados

    def extract_profiles(self, filename="profiles.dat"):
        """
        Lee el archivo de perfiles 1D y lo devuelve como un DataFrame de Pandas.
        Ideal para archivos estructurados en columnas.
        """
        filepath = os.path.join(self.work_dir, filename)
        if not os.path.exists(filepath):
            return None

        try:
            df = pd.read_csv(filepath, sep=r'\s+')
            return df
        except Exception as e:
            print(f"    [!] Error al leer {filename}: {e}")
            return None

    def extract_matrix(self, filename):
        """
        Lee archivos de matrices 2D (como nf_0000 o phi_0000) y los devuelve como arrays de NumPy.
        """
        filepath = os.path.join(self.work_dir, filename)
        if not os.path.exists(filepath):
            return None

        try:
            df = pd.read_csv(filepath, header=0, delimiter="\t")
            return df
        except Exception as e:
            print(f"    [!] Error al leer {filename}: {e}")
            return None

    def extract_data_txt_matrix(self, filename="Data.txt"):
        """
        Extrae la matriz de datos de Data.txt buscando la cabecera específica
        y devolviendo un DataFrame con todas las columnas y sus respectivos valores.
        """
        filepath = os.path.join(self.work_dir, filename)
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            table_started = False
            headers = []
            data_rows = []
            for line in lines:
                # 1. Identificar la fila de cabeceras
                if "Rho(norml. sqrt. toroid. flux)" in line:
                    table_started = True
                    headers = [h.strip() for h in line.split(',')]
                    continue

                # 2. Extraer los números
                if table_started and line.strip():
                    parts = line.split()
                    row_values = []

                    # Forzamos la conversión a float de cada elemento separado por espacios
                    for part in parts:
                        try:
                            row_values.append(float(part))
                        except ValueError:
                            pass
                    if len(row_values) == len(headers):
                        data_rows.append(row_values)

            # Generar el DataFrame con todos los datos recogidos
            df = pd.DataFrame(data_rows, columns=headers)
            if df.empty:
                print(
                    f"    [!] Advertencia: Se encontraron las cabeceras de {filename} pero no se leyeron filas válidas.")
            return df

        except Exception as e:
            print(f"    [!] Error crítico extrayendo matriz de Data.txt: {e}")
            return None

    def extract_farprt(self, filename="farprt"):
        filepath = os.path.join(self.work_dir, filename)
        return filepath

    def parse_csv(self):
        """
        Función para sólo ejecuta las extracciones para guardar en el CSV las filas (sin Dataframes)
        """
        print("    [>] Extrayendo datos de la simulación...")
        datos_extraidos = {
            'escalares': self.extract_gam_omr("farprt"),
            'phi_0000': self.extract_matrix("phi_0000"),
            'profiles': self.extract_profiles("profiles.dat")
        }
        return datos_extraidos

    def parse_all(self):
        """
        Función maestra que ejecuta todas las extracciones de una sola vez (para Visualización Local de la Interfaz Web)
        """
        print("    [>] Extrayendo datos de la simulación...")
        datos_extraidos = {
            'escalares': self.extract_gam_omr("farprt"),
            'farprt': self.extract_farprt("farprt"),
            'profiles': self.extract_profiles("profiles.dat"),
            'profiles_ex': self.extract_profiles("profiles_ex.dat"),
            'nf_0000': self.extract_matrix("nf_0000"),
            'phi_0000': self.extract_matrix("phi_0000"),
            'psi_0000': self.extract_matrix("psi_0000"),
            'pr_0000': self.extract_matrix("pr_0000"),
            'data_matrix': self.extract_data_txt_matrix("Data.txt")
        }
        return datos_extraidos