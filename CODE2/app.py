import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import shutil


from InputManager import InputManager
from ExecutionEngine import ExecutionEngine
from OutputParser import OutputParser

# --- 1. CONFIGURACIONES GLOBALES
TARGET_DIR = "./DIIID"
TEMPLATE_DIR = "./Templates_DIIID"
DIR_GUARDADAS = "./simulaciones_guardadas"

# --- 2. CONFIGURACIÓN DE LA PÁGINA Y ESTADO ---
st.set_page_config(page_title="Dashboard FAR3d", layout="wide")
os.makedirs(DIR_GUARDADAS, exist_ok=True)

if 'capa_actual' not in st.session_state:
    st.session_state.capa_actual = "Global"
if 'inputs_locales' not in st.session_state:
    st.session_state.inputs_locales = {}

# --- NAVEGACIÓN SUPERIOR ---
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🌐 Capa Global (Análisis)", use_container_width=True):
        st.session_state.capa_actual = "Global"
        st.rerun()
with col2:
    if st.button("🔍 Capa Local (Simulador)", use_container_width=True):
        st.session_state.capa_actual = "Local"
        st.rerun()
with col3:
    if st.button("📁 Simulaciones Guardadas", use_container_width=True):
        st.session_state.capa_actual = "Guardadas"
        st.rerun()

st.markdown("---")


# --- 2. FUNCIONES AUXILIARES (Lectura de CSV, extraer número, renderizar graficas y resultados locales)---
@st.cache_data
def load_data(csv_path="simulations_results.csv"):
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    return pd.read_csv(csv_path)


df = load_data()
excluidas = ['gam', 'om_r', 'gam_var', 'om_r_var']
input_vars = [c for c in df.columns if c not in excluidas] if not df.empty else []


def extraer_numero(valor):
    """Limpia el valor para asegurar que sea un float puro."""
    try:
        if isinstance(valor, set):
            return float(list(valor)[0])
        elif hasattr(valor, '__iter__') and not isinstance(valor, str):
            return float(valor[0])
        return float(valor)
    except (ValueError, TypeError, IndexError):
        return 0.0


def renderizar_resultados_locales(res, prefijo_widget="local"):
    """Renderiza las métricas y la gráfica. Se usa tanto en Capa Local como en Guardadas."""
    v_gam = extraer_numero(res.get('gam', 0))
    v_om_r = extraer_numero(res.get('om_r', 0))
    v_gam_var = extraer_numero(res.get('gam_var', 0))
    v_om_r_var = extraer_numero(res.get('om_r_var', 0))

    # Métricas
    st.markdown("### 📊 Resultados Analíticos")
    with st.container(border=True):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tasa de Crecimiento (gam)", f"{v_gam:.4e}")
        m2.metric("Frecuencia Real (om_r)", f"{v_om_r:.4e}")
        m3.metric("Varianza gam", f"{v_gam_var:.4e}", delta="Precisión" if v_gam_var < 1e-4 else "Dispersión",
                  delta_color="inverse")
        m4.metric("Varianza om_r", f"{v_om_r_var:.4e}", delta="Precisión" if v_om_r_var < 1e-4 else "Dispersión",
                  delta_color="inverse")

    # Gráficas
    st.divider()
    st.markdown("### 📈 Visualizador Radial de la Simulación")

    df_nf = res.get("df_nf")
    df_phi = res.get("df_phi")
    df_psi = res.get("df_psi")
    df_pr = res.get("df_pr")
    df_prof = res.get("df_prof")
    df_prof_ex = res.get("df_prof_ex")
    df_data = res.get("df_data")

    if df_nf is not None and not df_nf.empty and df_prof is not None and df_data is not None and df_prof_ex is not None:
        ctrl1, ctrl2 = st.columns(2)
        with ctrl1:
            opciones_matriz = []
            if df_nf is not None: opciones_matriz.append("nf_0000")
            if df_phi is not None: opciones_matriz.append("phi_0000")
            if df_psi is not None: opciones_matriz.append("psi_0000")
            if df_pr is not None: opciones_matriz.append("pr_0000")
            matriz_elegida = st.selectbox("Matriz Principal", opciones_matriz, key=f"matriz_{prefijo_widget}")

        with ctrl2:
            cols_prof = [c for c in df_prof.columns if c != df_prof.columns[0]]
            cols_data = [c for c in df_data.columns if "Rho" not in c]
            opciones_extra = cols_prof + cols_data

            vars_extra = st.multiselect(
                "Superponer variables adicionales (Máx 2)",
                options=opciones_extra,
                default=["q", "Beam Ion Density(10^20 m^-3)"] if "q" in opciones_extra else [],
                max_selections=2,
                key=f"vars_{prefijo_widget}"
            )

        fig_local = plt.figure(figsize=(12, 7))
        ax1 = fig_local.add_subplot(111)
        if len(vars_extra) == 2: fig_local.subplots_adjust(right=0.75)

        # Eje 1: Matriz Principal
        dicc_df = {"nf_0000": df_nf, "phi_0000": df_phi, "psi_0000": df_psi, "pr_0000": df_pr}
        df_main = dicc_df[matriz_elegida]


        armonicos = [c for c in df_main.columns if c != 'r']
        for col in armonicos:
            ax1.plot(df_main['r'], df_main[col], label=f"{matriz_elegida}: {col}", linewidth=1.5)
        ax1.set_xlabel('Radio Normalizado (r / Rho)')
        ax1.set_ylabel(f'Amplitud {matriz_elegida}', color='tab:blue')
        ax1.grid(True, linestyle=':', alpha=0.6)

        # Ejes Secundarios Dinámicos
        colores = ['black', 'tab:green']
        estilos = ['--', '-']
        marcadores = ['', '.']
        all_lines, all_labels = ax1.get_legend_handles_labels()

        for i, var in enumerate(vars_extra):
            ax_extra = ax1.twinx()
            if i == 1: ax_extra.spines.right.set_position(("axes", 1.15))

            df_src, col_x = (df_prof, df_prof.columns[0]) if var in df_prof.columns else (
            df_data, "Rho(norml. sqrt. toroid. flux)")
            l, = ax_extra.plot(df_src[col_x], df_src[var], color=colores[i], linestyle=estilos[i], marker=marcadores[i],
                               label=var)
            ax_extra.set_ylabel(var, color=colores[i])
            ax_extra.tick_params(axis='y', labelcolor=colores[i])
            all_lines.append(l)
            all_labels.append(var)

        ax1.legend(all_lines, all_labels, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)
        st.pyplot(fig_local)
        plt.close(fig_local)
    else:
        st.info("Datos insuficientes para generar la gráfica (Faltan DataFrames).")


# --- FUNCIÓN DE EJECUCIÓN DEL PROGRAMA ---
def ejecutar_simulacion_real(inputs, nn_val, mm_vals):
    """
    EJECUTA LA HERRAMIENTA DE FAR3d:
        - Modifica los archivos "Input_Model" y "Data.txt" para incluir los valores de las variables de entrada.
        - Lanza la simulación correspondiente con "wsl ./xfar3d".
        - Parsea los archivos output relevantes para devolver los Dataframes correspondientes.
        - Devuelve en un Diccionario toda la info + dataframes necesarios.
    """
    manager = InputManager(template_dir=TEMPLATE_DIR, output_dir=TARGET_DIR)
    engine = ExecutionEngine(work_dir=TARGET_DIR)
    parser = OutputParser(work_dir=TARGET_DIR)

    inputmodel_columns = ["bet0_f", "spe1", "s", "maxstp", "EP_dens_on", "Bdens", "Adens"]
    inputmodel_vars = {k: v for k, v in inputs.items() if k in inputmodel_columns}
    data_vars = {k: v for k, v in inputs.items() if k not in inputmodel_columns}

    # PREPARACIÓN DE ENTRADAS
    manager.modify_input_model('Input_Model', 'Input_Model', inputmodel_vars, nn_val, mm_vals)
    manager.modify_data_txt('Data.txt', 'Data.txt', data_vars)

    # LANZAR SIMULACIÓN
    exec_result = engine.run_simulation(run_id=9999, timeout_seconds=180)

    # EXTRACCIÓN DE RESULTADOS - OBTENER ESCALARES Y DATAFRAMES
    if exec_result['status'] == "SUCCESS":
        datos_simulacion = parser.parse_all()
        escalares = datos_simulacion['escalares']
        resultados = {
            "gam": {escalares.get('gam', 'N/A')}, "om_r": {escalares.get('om_r', 'N/A')},
            "gam_var": {escalares.get('gam_var', 'N/A')}, "om_r_var": {escalares.get('om_r_var', 'N/A')},
            "df_nf": datos_simulacion["nf_0000"], "df_prof": datos_simulacion["profiles"],
            "df_data": datos_simulacion["data_matrix"], "df_prof_ex": datos_simulacion["profiles_ex"],
            "df_phi": datos_simulacion["phi_0000"], "farprt_path": datos_simulacion["farprt"],
            "df_psi": datos_simulacion["psi_0000"], "df_pr": datos_simulacion["pr_0000"]
        }
        return resultados
    else:
        print("ERROR DURANTE LA SIMULACIÓN")


# =====================================================================
#                        CAPA GLOBAL
# =====================================================================
if st.session_state.capa_actual == "Global":
    st.title("🌐 Capa Global: Mallas de Estabilidad")

    if df.empty:
        st.error("No se encontró la base de datos CSV global.")
        st.stop()

    st.sidebar.header("⚙️ Ejes del Mapa")
    var_x = st.sidebar.selectbox("Eje X", input_vars, index=0)
    var_y = st.sidebar.selectbox("Eje Y", input_vars, index=1 if len(input_vars) > 1 else 0)

    st.sidebar.header("📊 Variable Representada")
    target_map = {
        "Tasa de Crecimiento (gam)": {"mean": "gam", "var": "gam_var", "cmap": "gnuplot2", "edge": "white"},
        "Frecuencia Real (om_r)": {"mean": "om_r", "var": "om_r_var", "cmap": "gnuplot2", "edge": "white"}
    }
    target_label = st.sidebar.radio("Variable", list(target_map.keys()))
    t_mean, t_var = target_map[target_label]["mean"], target_map[target_label]["var"]
    t_cmap, t_edge = target_map[target_label]["cmap"], target_map[target_label]["edge"]

    show_variance = st.sidebar.checkbox("Mostrar Varianza (Burbujas)", value=True)

    st.sidebar.header("📌 Filtros / Rebanada")
    df_filt = df.copy()
    vars_restantes = [v for v in input_vars if v not in [var_x, var_y]]

    for v in vars_restantes:
        valores_unicos = sorted(df_filt[v].dropna().unique())
        if len(valores_unicos) > 1:
            val_fijo = st.sidebar.selectbox(f"Fijar '{v}'", valores_unicos)
            df_filt = df_filt[df_filt[v] == val_fijo]
        elif len(valores_unicos) == 1:
            df_filt = df_filt[df_filt[v] == valores_unicos[0]]

    # Renderizado Global
    if df_filt.empty or var_x == var_y:
        st.warning("Selección inválida o sin datos.")
    else:
        pivot_mean = df_filt.pivot_table(index=var_y, columns=var_x, values=t_mean, aggfunc='mean')

        st.markdown(f"**Ajuste de Escala de Color ({t_mean})**")
        min_global, max_global = float(df[t_mean].min()), float(df[t_mean].max())
        vmin_user, vmax_user = st.slider("Rango de colores (vmin, vmax)", min_value=min_global, max_value=max_global,
                                         value=(min_global, max_global), format="%.4e")

        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.pcolormesh(pivot_mean.columns, pivot_mean.index, pivot_mean.values, shading='nearest', cmap=t_cmap,
                           vmin=vmin_user, vmax=vmax_user)
        fig.colorbar(im, ax=ax, label=target_label)

        if show_variance:
            pivot_var = df_filt.pivot_table(index=var_y, columns=var_x, values=t_var, aggfunc='mean')
            std_dev = np.nan_to_num(np.sqrt(pivot_var.values))
            max_std = np.max(std_dev) if np.max(std_dev) > 0 else 1.0
            sizes = (std_dev / max_std) * 500
            X, Y = np.meshgrid(pivot_mean.columns, pivot_mean.index)
            ax.scatter(X.flatten(), Y.flatten(), s=sizes.flatten(), facecolors='none', edgecolors=t_edge,
                       linewidths=1.5, alpha=0.8)

        ax.set_xlabel(var_x)
        ax.set_ylabel(var_y)
        st.pyplot(fig)

        # TABLA INTERACTIVA
        st.divider()
        st.subheader("Simulaciones del Corte Actual")
        cols_existentes = [c for c in ['run_id'] + input_vars + [t_mean] if c in df_filt.columns]
        evento = st.dataframe(df_filt[cols_existentes], on_select="rerun", selection_mode="single-row",
                              use_container_width=True)

        if len(evento.selection.rows) > 0:
            fila_seleccionada = df_filt.iloc[evento.selection.rows[0]]
            for var in input_vars:
                st.session_state.inputs_locales[var] = fila_seleccionada[var]
            st.session_state.capa_actual = "Local"
            st.rerun()

# =====================================================================
#                        CAPA LOCAL
# =====================================================================
elif st.session_state.capa_actual == "Local":
    st.title("🔍 Capa Local: Lanzador de Simulaciones")
    st.markdown("Modifica los parámetros de entrada manualmente o lánzalos desde la selección global.")

    # --- 1. Formulario de Parámetros de Entrada ---
    with st.form("form_inputs_locales"):
        st.subheader("Parámetros de Entrada")
        st.markdown("Especifica el valor y el **tipo de dato** (float o int) requerido por el simulador.")
        cols = st.columns(3)
        inputs_actuales = {}
        for i, var in enumerate(input_vars):
            valor_defecto = float(st.session_state.inputs_locales.get(var, 0.0))
            es_int_defecto = valor_defecto.is_integer()

            with cols[i % 3]:
                st.markdown(f"**{var}**")
                sub_col1, sub_col2 = st.columns([2, 1])
                with sub_col1:
                    val_raw = st.number_input(f"Valor {var}", value=valor_defecto, format="%.5f", key=f"val_{var}",
                                              label_visibility="collapsed")
                with sub_col2:
                    tipo_dato = st.selectbox(f"Tipo {var}", options=["float", "int"], index=1 if es_int_defecto else 0,
                                             key=f"tipo_{var}", label_visibility="collapsed")
                inputs_actuales[var] = int(val_raw) if tipo_dato == "int" else float(val_raw)

        st.markdown("---")
        # --- NUEVO: CONFIGURACIÓN DE MODOS ---
        st.subheader("Configuración de Modos (Espectro Toroidal/Poloidal)")
        st.markdown("Define las familias $m/n$ que se incluirán en esta ejecución.")
        col_n, col_m = st.columns([1, 2])

        with col_n:
            # Selector único para nn (1 a 5)
            nn_elegido = st.selectbox("Número Toroidal (nn)", options=[1, 2, 3, 4, 5], index=0)

        with col_m:
            # Multiselector para mm (permite múltiples valores)
            mm_elegidos = st.multiselect("Números Poloidales (mm)",
                                         options=list(range(1, 21)),  # De 1 a 20 como opciones disponibles
                                         default=[1, 2, 3, 4])  # Por defecto el caso clásico

        if not mm_elegidos:
            st.error("Debes seleccionar al menos un número poloidal (mm) para poder lanzar la simulación.")

        st.markdown("<br>", unsafe_allow_html=True)
        # Habilitar el botón solo si hay al menos un 'mm' seleccionado

        lanzar_simulacion = st.form_submit_button("🚀 EJECUTAR SIMULACIÓN", type="primary", disabled=(len(mm_elegidos)==0))

    if lanzar_simulacion:
        with st.spinner('Ejecutando simulación de FAR3d...'):
            st.session_state.resultados_locales = ejecutar_simulacion_real(inputs_actuales, nn_elegido, mm_elegidos)
            st.session_state.inputs_ejecutados = inputs_actuales  # Guardamos qué inputs se usaron
            st.session_state.modos_ejecutados = {"nn": nn_elegido, "mm": mm_elegidos}  # Guardar los modos elegidos

    # --- 2. Mostrar Resultados si existen en memoria ---
    if 'resultados_locales' in st.session_state:
        st.success("✅ Simulación completada.")
        renderizar_resultados_locales(st.session_state.resultados_locales, prefijo_widget="local")

        # --- LÓGICA DE GUARDADO ---
        st.divider()
        st.subheader("💾 Guardar Simulación")
        with st.form("form_guardar"):
            nombre_sim = st.text_input("Nombre para guardar esta simulación (ej. sim_caso_base_01)")
            btn_guardar = st.form_submit_button("Guardar Resultados")

            if btn_guardar:
                if not nombre_sim.strip():
                    st.error("Por favor, introduce un nombre válido.")
                else:
                    path_guardado = os.path.join(DIR_GUARDADAS, nombre_sim.strip())
                    if os.path.exists(path_guardado):
                        st.error(f"Ya existe una simulación guardada con el nombre '{nombre_sim}'.")
                    else:
                        os.makedirs(path_guardado)
                        res = st.session_state.resultados_locales

                        # 1. Guardar Metadatos e Inputs en JSON
                        metadata = {
                            "inputs": st.session_state.inputs_ejecutados,
                            "gam": extraer_numero(res.get('gam', 0)),
                            "om_r": extraer_numero(res.get('om_r', 0)),
                            "gam_var": extraer_numero(res.get('gam_var', 0)),
                            "om_r_var": extraer_numero(res.get('om_r_var', 0))
                        }
                        with open(os.path.join(path_guardado, "metadata.json"), "w") as f:
                            json.dump(metadata, f, indent=4)

                        # 2. Guardar DataFrames en CSV
                        if res.get("df_nf") is not None: res["df_nf"].to_csv(
                            os.path.join(path_guardado, "df_nf.csv"), index=False)
                        if res.get("df_phi") is not None: res["df_phi"].to_csv(
                            os.path.join(path_guardado, "df_phi.csv"), index=False)
                        if res.get("df_psi") is not None: res["df_psi"].to_csv(
                            os.path.join(path_guardado, "df_psi.csv"), index=False)
                        if res.get("df_pr") is not None: res["df_pr"].to_csv(
                            os.path.join(path_guardado, "df_pr.csv"), index=False)
                        if res.get("df_prof") is not None: res["df_prof"].to_csv(
                            os.path.join(path_guardado, "df_prof.csv"), index=False)
                        if res.get("df_prof_ex") is not None: res["df_prof_ex"].to_csv(
                            os.path.join(path_guardado, "df_prof_ex.csv"), index=False)
                        if res.get("df_data") is not None: res["df_data"].to_csv(
                            os.path.join(path_guardado, "df_data.csv"), index=False)
                        if res.get("farprt_path") is not None:
                            shutil.copy2(res['farprt_path'], os.path.join(path_guardado, "farprt"))

                        st.success(f"Simulación '{nombre_sim}' guardada correctamente en {DIR_GUARDADAS}.")


# =====================================================================
#                 CAPA SIMULACIONES GUARDADAS
# =====================================================================
elif st.session_state.capa_actual == "Guardadas":
    st.title("📁 Simulaciones Guardadas")
    st.markdown("Consulta el historial de simulaciones individuales guardadas.")

    simulaciones_disponibles = [d for d in os.listdir(DIR_GUARDADAS) if os.path.isdir(os.path.join(DIR_GUARDADAS, d))]

    if not simulaciones_disponibles:
        st.info("No hay ninguna simulación guardada todavía. Ve a la Capa Local para ejecutar y guardar una.")
    else:
        sim_elegida = st.selectbox("Selecciona una simulación para inspeccionar:", simulaciones_disponibles)

        path_sim = os.path.join(DIR_GUARDADAS, sim_elegida)
        path_meta = os.path.join(path_sim, "metadata.json")

        if os.path.exists(path_meta):
            with open(path_meta, "r") as f:
                metadata = json.load(f)

            # Reconstruir el diccionario 'res' a partir de los archivos guardados
            res_cargados = {
                "gam": metadata.get("gam", 0),
                "om_r": metadata.get("om_r", 0),
                "gam_var": metadata.get("gam_var", 0),
                "om_r_var": metadata.get("om_r_var", 0),
                "df_nf": pd.read_csv(os.path.join(path_sim, "df_nf.csv")) if os.path.exists(
                    os.path.join(path_sim, "df_nf.csv")) else None,
                "df_phi": pd.read_csv(os.path.join(path_sim, "df_phi.csv")) if os.path.exists(
                    os.path.join(path_sim, "df_phi.csv")) else None,
                "df_psi": pd.read_csv(os.path.join(path_sim, "df_psi.csv")) if os.path.exists(
                    os.path.join(path_sim, "df_psi.csv")) else None,
                "df_pr": pd.read_csv(os.path.join(path_sim, "df_pr.csv")) if os.path.exists(
                    os.path.join(path_sim, "df_pr.csv")) else None,
                "df_prof": pd.read_csv(os.path.join(path_sim, "df_prof.csv")) if os.path.exists(
                    os.path.join(path_sim, "df_prof.csv")) else None,
                "df_prof_ex": pd.read_csv(os.path.join(path_sim, "df_prof_ex.csv")) if os.path.exists(
                    os.path.join(path_sim, "df_prof_ex.csv")) else None,
                "df_data": pd.read_csv(os.path.join(path_sim, "df_data.csv")) if os.path.exists(
                    os.path.join(path_sim, "df_data.csv")) else None,
            }

            # Mostrar los inputs con los que se ejecutó
            st.markdown("### ⚙️ Parámetros de Entrada Usados")
            inputs_usados = metadata.get("inputs", {})
            st.json(inputs_usados, expanded=False)

            # Renderizar métricas y gráfica usando la función auxiliar común
            renderizar_resultados_locales(res_cargados, prefijo_widget="guardada")

        else:
            st.error("Los datos de esta simulación están corruptos o incompletos (Falta metadata.json).")