"""
---------------- GUARDAR NUEVAS SIMULACIONES EN EL CSV -------------------

"""

import os
import pandas as pd


class DataManager:
    def __init__(self, keys, csv_path):
        keys.append("n")
        self.input_keys = keys
        self.csv_path = csv_path
        self._setup_csv()

    def _setup_csv(self):
        """Crea el archivo CSV con sus cabeceras si no existe todavía."""
        if not os.path.exists(self.csv_path):
            # Definimos las columnas de nuestra base de datos CSV (Variables Input + Variables Objetivo)
            columnas = self.input_keys + ["gam", "om_r", "gam_var", "om_r_var"] + [
                "tipo_inestabilidad", "modo_m", "pos_radial", "diff_m"]

            df_vacio = pd.DataFrame(columns=columnas)
            df_vacio.to_csv(self.csv_path, index=False)
            print(f"[*] Creado nuevo archivo de base de datos: {self.csv_path}")

    def save_simulation(self, inputs, escalares, etiqueta):
        """
        Guarda los resultados como una fila nueva dentro del CSV
        """
        # 1. Construir la fila de datos plana
        fila_datos = {}

        # Insertar cada parámetro de entrada en su propia columna
        for key in self.input_keys:
            fila_datos[key] = inputs.get(key)

        # Insertar los resultados estadísticos
        fila_datos.update({
            "gam": escalares.get('gam'),
            "om_r": escalares.get('om_r'),
            "gam_var": escalares.get('gam_var'),
            "om_r_var": escalares.get('om_r_var')
        })

        # Insertar resultados de ETIQUETA
        fila_datos.update({
            "tipo_inestabilidad": etiqueta.get('tipo_inestabilidad'),
            "modo_m": etiqueta.get('modo_m'),
            "pos_radial": etiqueta.get('pos_radial'),
            "diff_m": etiqueta.get('diff_m')
        })

        # Guardar en el CSV (mode='a' es append, es decir, añade al final sin borrar lo anterior)
        df_nueva_fila = pd.DataFrame([fila_datos])
        columnas_ordenadas = self.input_keys + [
            "gam", "om_r", "gam_var", "om_r_var"
        ] + ["tipo_inestabilidad", "modo_m", "pos_radial", "diff_m"]
        df_nueva_fila[columnas_ordenadas].to_csv(self.csv_path, mode='a', header=False, index=False)
        df_nueva_fila[columnas_ordenadas].to_csv()

        print("       [+] NUEVA SIMULACIÓN GUARDADA EN CSV")
