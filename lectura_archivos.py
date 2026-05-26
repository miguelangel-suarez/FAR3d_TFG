import os
import re
import csv

# ==========================================
# FUNCIONES DE MANEJO DE ARCHIVOS
# ==========================================


# 1. LECTURA DE ARCHIVOS DE ENTRADA Y SALIDA
# ------------------------------------------

def leer_farprt(filepath):
    """Extrae TODAS las variables (m, n, gam, om_r) usando Regex."""
    resultados_lista = []

    if not os.path.exists(filepath):
        print(f"Advertencia: No se encontró el archivo de salida en {filepath}")
        return resultados_lista

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


# 2. CREACIÓN DE ARCHIVOS AUXILIARES
# ------------------------------------------

def crear_input_model(parametros, template_path, output_path):
    """Sustituye los valores en la plantilla conservando el formato exacto."""
    with open(template_path, 'r', encoding='utf-8') as f_in:
        lineas = f_in.readlines()

    with open(output_path, 'w', encoding='utf-8') as f_out:
        i = 0
        while i < len(lineas):
            linea = lineas[i]
            f_out.write(linea)

            if linea.startswith('!!!!!!!!!!!'):
                partes = linea.split(':')
                if len(partes) > 1:
                    nombre_variable = partes[0].replace('!!!!!!!!!!!', '').strip()
                    if nombre_variable in parametros:
                        f_out.write(f"{parametros[nombre_variable]}\n")
                        i += 1
            i += 1


# 3. GUARDAR BASE DE DATOS (CSV)
# --------------------------------------

def guardar_en_csv(csv_path, parametros, lista_resultados):
    """Guarda los resultados en formato largo (múltiples filas por ejecución)."""
    if not lista_resultados:
        return

    archivo_existe = os.path.exists(csv_path)
    cabeceras = list(parametros.keys()) + list(lista_resultados[0].keys())

    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cabeceras)

        if not archivo_existe or os.stat(csv_path).st_size == 0:
            writer.writeheader()

        for resultado in lista_resultados:
            fila_completa = {**parametros, **resultado}
            writer.writerow(fila_completa)