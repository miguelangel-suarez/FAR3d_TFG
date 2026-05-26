"""
---------------- PARSEAR LOS ARCHIVOS OUTPUT (DEVOLVER DATAFRAMES Y ESCALARES) -------------------


"""

import os
import re
import numpy as np
import pandas as pd


class OutputParser:
    def __init__(self, work_dir):
        """
        Inicializa el parser de salidas.
        :param work_dir: Directorio donde se encuentran los archivos generados por la simulación.
        """
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
                tipo = match.group(1).upper()  # Extrae "R" o "I"
                familia_raw = match.group(2)  # Extrae "1/ 1", "3/ 1", etc.

                # Quitamos los espacios internos para que el nombre de la columna sea limpio ("1/1")
                familia_clean = familia_raw.replace(" ", "")

                if familia_clean not in familias:
                    familias[familia_clean] = {}

                familias[familia_clean][tipo] = col
            else:
                # Si hubiera alguna columna extra en el archivo (ej. una constante), la copiamos
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

    def extract_gam_omr(self, filename="farprt"):
        """
        Extrae las variables escalares finales (gam, om_r, etc.) del archivo farprt.
        Lee el archivo con una expresión regular para encontrar la tabla de resultados finales,
        y devuelve un diccionario con las medias y varianzas de gam y om_r.
        """

        def read_table(resultados_lista, filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                contenido = f.read()

                # Expresión regular para capturar la tabla de variables del eigenmodo
                patron = r"\s*([a-zA-Z]+)\s*:\s*m=\s*([+-]?\d+)\s*n=\s*([+-]?\d+)\s*gam=\s*([+-]?\d+\.\d+[Ee][+-]\d+)\s*om_r=\s*([+-]?\d+\.\d+[Ee][+-]\d+)"
                matches = re.findall(patron, contenido)

                for match in matches:
                    resultados_lista.append({
                        "variable_eigen": match[0],
                        "m": int(match[1]),
                        "n": int(match[2]),
                        "gam": float(match[3]),
                        "om_r": float(match[4])
                    })

            return resultados_lista

        filepath = os.path.join(self.work_dir, filename)
        resultados = []

        if not os.path.exists(filepath):
            print(f"    [!] Advertencia: No se encontró el archivo {filename}")
            return {"gam_mean": None, "om_r_mean": None, "gam_var": None, "om_r_var": None}

        # Extraemos la lista de diccionarios con las configuraciones
        lista_datos = read_table(resultados, filepath)
        if not lista_datos:
            print(f"    [!] Advertencia: La tabla no se encontró en {filename}")
            return {"gam_mean": None, "om_r_mean": None, "gam_var": None, "om_r_var": None}

        gams = [item["gam"] for item in lista_datos]
        om_rs = [item["om_r"] for item in lista_datos]

        # Usamos numpy para calcular medias y varianzas.
        # (ddof=1 calcula la varianza muestral, si prefieres la poblacional cambia a ddof=0)
        diccionario_estadistico = {
            "gam": float(np.mean(gams)),
            "om_r": float(np.mean(om_rs)),
            "gam_var": float(np.var(gams, ddof=1)) if len(gams) > 1 else 0.0,
            "om_r_var": float(np.var(om_rs, ddof=1)) if len(om_rs) > 1 else 0.0
        }

        return diccionario_estadistico

    def extract_profiles(self, filename="profiles.dat"):
        """
        Lee el archivo de perfiles 1D y lo devuelve como un DataFrame de Pandas.
        Ideal para archivos estructurados en columnas.
        """
        filepath = os.path.join(self.work_dir, filename)
        if not os.path.exists(filepath):
            return None

        try:
            # Asumimos que los datos están separados por espacios en blanco
            # Si el archivo tiene una cabecera con nombres, se usará automáticamente.
            # Si no, puedes añadir: names=['rho', 'q', 'te', ...]
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
            # Leer Tabla
            df = pd.read_csv(filepath, header=0, delimiter="\t")
            # Agrupar columnas (R + I) por cada onda
            df_limpio = self.transformar_a_amplitud(df)
            return df_limpio
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

                # 2. Si la tabla ha empezado, extraemos los números
                if table_started and line.strip():
                    parts = line.split()
                    row_values = []

                    # Forzamos la conversión a float de cada elemento separado por espacios
                    for part in parts:
                        try:
                            row_values.append(float(part))
                        except ValueError:
                            # Si hay texto mezclado u otra etiqueta, simplemente lo ignoramos
                            pass
                    # Si hemos conseguido extraer exactamente un número por cada cabecera, es una fila válida
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
            'escalares': self.extract_gam_omr("farprt")
        }
        return datos_extraidos

    def parse_all(self):
        """
        Función maestra que ejecuta todas las extracciones de una sola vez (para Visualización Local)
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