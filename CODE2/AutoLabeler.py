import pandas as pd
import numpy as np
import re

class SimulationLabeler:
    def __init__(self, umbral_gamma=5e-3, umbral_var=1e-4, umbral_om_r=1,
                 margen_gae_khz = 0.5, margen_rsae = 0.05):
        self.umbral_gamma = umbral_gamma
        self.umbral_var = umbral_var
        self.umbral_om_r = umbral_om_r
        self.margen_gae = margen_gae_khz
        self.margen_rsae = margen_rsae

    def _check_instability(self, gam, om_r, gam_var, om_r_var):
        """Paso 1: Comprobar umbrales de inestabilidad."""
        if (abs(gam) < self.umbral_gamma or gam_var > self.umbral_var or
                om_r_var > self.umbral_var or om_r < self.umbral_om_r):
            return 0  # Estable / Ruido
        return 1  # Inestable

    def _clean_mode_str(self, raw_str):
        """Extrae el m y n puros de cadenas como 'R  3/ 2' o 'Im 10/3'."""
        # Busca el patrón de números separados por barra
        match = re.search(r'(\d+)\s*/\s*(\d+)', str(raw_str))
        if match:
            m = int(match.group(1))
            n = int(match.group(2))
            clean_str = f"{m}/{n}"
            return clean_str, m, n
        return raw_str, None, None

    def _get_dominant_modes(self, df_phi, umbral_acoplamiento=0.5):
        """
        Paso 2: Obtener el modo dominante (m/n, m, n, pos_radial_max, diff).
        Buscar otros modos m con amplitud comparable para calcular la diferencia entre ellos.
        """
        col_r = df_phi.columns[0]
        df_datos = df_phi.drop(columns=[col_r])

        # Máximos absolutos por columna ordenados de mayor a menor
        max_vals = df_datos.abs().max().sort_values(ascending=False)

        # --- MODO DOMINANTE PRINCIPAL ---
        dom1_raw = max_vals.index[0]
        amp_max_ref = max_vals.iloc[0]  # Amplitud de referencia
        dom1_clean, m1, n1 = self._clean_mode_str(dom1_raw)

        # Obtener r_max a partir de la fila donde el modo dominante tiene su pico
        idx_max_1 = df_datos[dom1_raw].abs().idxmax()
        r_max = df_phi.loc[idx_max_1, col_r]

        # --- BÚSQUEDA DEL MODO ACOPLADO ---
        modos_candidatos = []

        # Recorremos el resto de modos ordenados por amplitud
        for col_raw, amp in max_vals.items():
            if col_raw == dom1_raw:
                continue

            clean_str, m_curr, n_curr = self._clean_mode_str(col_raw)

            # 1. Descartar la otra paridad del modo dominante (mismo m/n)
            if clean_str == dom1_clean:
                continue

            # 2. Descartar si m_curr no se pudo leer
            if m_curr is None or m1 is None:
                continue

            # 3. Comprobar si la amplitud es "parecida/comparable"
            if amp >= (umbral_acoplamiento * amp_max_ref):
                diff_m = abs(m_curr - m1)
                modos_candidatos.append({
                    'm': m_curr,
                    'amp': amp,
                    'diff_m': diff_m
                })

        # --- SELECCIÓN LÓGICA DEL ACOPLAMIENTO ---
        if not modos_candidatos:
            # No hay ningún modo con amplitud comparable
            return dom1_clean, m1, n1, r_max, 0

        elif len(modos_candidatos) == 1:
            # Solo hay un modo comparable
            acoplado = modos_candidatos[0]
            return dom1_clean, m1, n1, r_max, acoplado['diff_m']

        else:
            # Varios modos comparables: Elegimos el que tenga MAYOR diferencia en 'm'
            # (En caso de empate en diff_m, max() devolverá el primero que encuentre,
            # que será el de mayor amplitud al estar la lista original ordenada)
            acoplado_max = max(modos_candidatos, key=lambda x: x['m'])
            acoplado_min = min(modos_candidatos, key=lambda x: x['m'])
            diff_m = abs(acoplado_max["m"] - acoplado_min["m"])

            return dom1_clean, m1, n1, r_max, diff_m

    def _get_q_min_radius(self, df_prof):
        """Paso 3: Obtener posición del q mínimo."""
        col_r = df_prof.columns[0]
        col_q = 'q' if 'q' in df_prof.columns else df_prof.columns[1]
        idx_qmin = df_prof[col_q].idxmin()
        return df_prof.loc[idx_qmin, col_r]

    def _process_continuum(self, df_continuo, r_max, n_val):
        """
        Paso 4: Aproximar radio, filtrar por 'n', y obtener lista ordenada de frecuencias del gap.
        """
        # Identificar la columna del radio (ignorando 'Unnamed: 0' si existe al importar CSVs)
        col_r = df_continuo.columns[1] if 'Unnamed: 0' in df_continuo.columns else df_continuo.columns[0]
        idx_r = df_continuo.columns.get_loc(col_r)

        # Aproximar r_max a la posición radial más cercana que exista en el dataframe
        radios_unicos = df_continuo[col_r].unique()
        r_aprox = radios_unicos[np.argmin(np.abs(radios_unicos - r_max))]

        # Quedarnos solo con la "rodaja" de ese radio exacto
        df_rodaja = df_continuo[df_continuo[col_r] == r_aprox]

        # Identificar la columna del modo 'n'
        # Asumimos que si col_r es el índice 0, n=1 es el índice 1, n=2 es el índice 2, etc.
        idx_n = idx_r + n_val

        if idx_n >= len(df_continuo.columns):
            # Fallback de seguridad si el n_val es mayor a las columnas disponibles
            frecuencias_brutas = df_rodaja.iloc[:, -1].values
        else:
            frecuencias_brutas = df_rodaja.iloc[:, idx_n].values

        # Limpiar ceros y ordenar para obtener las ramas que delimitan los gaps
        ramas_gap = np.sort(frecuencias_brutas[frecuencias_brutas > self.umbral_om_r])

        # Consolidar ramas muy juntas (filtro anti-ruido numérico)
        ramas_limpias = []
        tolerancia = 5.0  # Agrupar ramas que estén a menos de 5 kHz
        for f in ramas_gap:
            if not ramas_limpias or (f - ramas_limpias[-1] > tolerancia):
                ramas_limpias.append(f)

        # Calcular también el mínimo absoluto del continuo (para la regla GAE)
        datos_todas_freqs = df_continuo.iloc[:, idx_n].values.flatten()
        min_continuo_global = np.min(datos_todas_freqs[datos_todas_freqs > self.umbral_om_r])

        return ramas_limpias, r_aprox, min_continuo_global

    def _classify_in_gaps(self, om_r, ramas_limpias, r_max, r_qmin, min_continuo_global, diff):
        """
        Paso 5: Asignar etiqueta cruzando frecuencia con la lista de ramas y las reglas GAE/RSAE.
        """
        # --- REGLA GAE (cerca al mínimo global del continuo y sólo un modo dominante)---
        if ((min_continuo_global - self.margen_gae) <= om_r <= (min_continuo_global + self.margen_gae)) and diff == 0:
            return "GAE"

        # Si no hay ramas válidas, devolvemos lo genérico
        if len(ramas_limpias) == 0:
            return "AE"

        # --- CLASIFICACIÓN de AE (TAE, EAE, NAE): Modos Acoplados y Frecuencia del Continuo ---
        # Priorizar clasificación por acoplamiento de modos m y m+i antes que el espectro del continuo
        if om_r < ramas_limpias[0]:
            if r_max >= 0.8:
                tipo_base = "Estable/Ruido"
            else:
                tipo_base = "BAE"

        elif ramas_limpias[0] <= om_r < ramas_limpias[1]:
            # --- REGLA RSAE ---
            if r_qmin is not None and abs(r_max - r_qmin) <= self.margen_rsae:
                tipo_base = "RSAE"
            else:
                if diff == 0:
                    tipo_base = "BAE"
                else:
                    tipo_base = "TAE"

        elif ramas_limpias[1] <= om_r < ramas_limpias[2]:
            if diff == 1:
                tipo_base = "TAE"
            else:
                tipo_base = "EAE"

        elif ramas_limpias[2] <= om_r:
            if diff == 2:
                tipo_base = "EAE"
            else:
                tipo_base = "NAE"
        else:
            tipo_base = "AE"

        return tipo_base

    def generate_label(self, escalares, df_phi, df_continuo, df_prof):
        """Orquestador principal."""
        gam = escalares.get('gam', 0.0)
        om_r = escalares.get('om_r', 0.0)
        gam_var = escalares.get('gam_var', 1.0)
        om_r_var = escalares.get('om_r_var', 1.0)

        etiqueta = {
            "om_r": om_r,
            "gamma": gam,
            "es_inestable": 0,
            "tipo_inestabilidad": "Estable/Ruido",
            "modo_dominante_str": None,
            "modo_m": None,
            "pos_radial": None,
            "r_qmin": None,
            "r_continuo_aprox": None,
            "diff_m": 0,
            "min_continuo_global": None,
            "ramas": None
        }

        # 1. Modos dominantes y r_max
        modo_dom_str, modo_m, n1, r_max, diff = self._get_dominant_modes(df_phi)
        etiqueta["modo_dominante_str"] = modo_dom_str
        etiqueta["modo_m"] = modo_m
        etiqueta["pos_radial"] = r_max
        etiqueta["diff_m"] = diff

        # 2. Mínimo de q
        r_qmin = None
        if df_prof is not None and not df_prof.empty:
            r_qmin = self._get_q_min_radius(df_prof)
            etiqueta["r_qmin"] = r_qmin

        # 3 y 4. Procesamiento del Continuo y Clasificación
        ramas, r_aprox, min_global = self._process_continuum(df_continuo, r_max, n1)
        etiqueta["r_continuo_aprox"] = r_aprox
        etiqueta["min_continuo_global"] = min_global
        etiqueta["ramas"] = ramas

        # 5. ¿Hay inestabilidad?
        if self._check_instability(gam, om_r, gam_var, om_r_var):
            tipo = self._classify_in_gaps(om_r, ramas, r_max, r_qmin, min_global, diff)
            etiqueta["tipo_inestabilidad"] = tipo

        # 6. Determinar si es estable o no
        if etiqueta["tipo_inestabilidad"] == "Estable/Ruido":
            etiqueta["es_inestable"] = 0
        else:
            etiqueta["es_inestable"] = 1

        return etiqueta