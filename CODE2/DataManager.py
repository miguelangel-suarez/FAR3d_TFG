"""
---------------- GUARDAR NUEVAS SIMULACIONES EN EL CSV -------------------


"""

import os
import pandas as pd


class DataManager:
    def __init__(self, grid_bounds, csv_path="./simulations_results.csv"):
        """
        :param grid_bounds: Diccionario con los valores mínimo y máximo de cada variable.
                            Ejemplo: {'bet0_f': (0.0, 0.002), 'spe1': (1, 2)}
        """
        self.grid_bounds = grid_bounds
        self.input_keys = [grid_bounds.keys(), "n"]
        self.csv_path = csv_path
        self._setup_csv()

    def _setup_csv(self):
        """Crea el archivo CSV con sus cabeceras si no existe todavía."""
        if not os.path.exists(self.csv_path):
            # Definimos las columnas de nuestra base de datos CSV
            columnas = self.input_keys + [
                "gam", "om_r", "gam_var", "om_r_var"
            ]
            df_vacio = pd.DataFrame(columns=columnas)
            df_vacio.to_csv(self.csv_path, index=False)
            print(f"[*] Creado nuevo archivo de base de datos: {self.csv_path}")

    def save_simulation(self, inputs, escalares):
        """
        Guarda los resultados como una fila nueva dentro del CSV "simulations_results.csv"
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

        # Guardar en el CSV (mode='a' es append, es decir, añade al final sin borrar lo anterior)
        df_nueva_fila = pd.DataFrame([fila_datos])
        # Usamos las columnas de la clase para asegurar el orden correcto
        columnas_ordenadas = self.input_keys + [
            "gam", "om_r", "gam_var", "om_r_var"
        ]
        df_nueva_fila[columnas_ordenadas].to_csv(self.csv_path, mode='a', header=False, index=False)
        df_nueva_fila[columnas_ordenadas].to_csv()

        print("       [+] NUEVA SIMULACIÓN GUARDADA EN CSV")