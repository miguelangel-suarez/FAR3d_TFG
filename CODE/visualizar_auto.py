import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def graficar_nf(file_path, file_name, bet0_f):
    NF_FILE = f"./Graficas_auto2/nf/{file_name}"

    try:
        column_names = ['r', 'R1', 'R2', 'R3', 'R4', 'I1', 'I2', 'I3', 'I4']
        df = pd.read_csv(file_path, sep=r'\s+', skiprows=1, names=column_names)
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return

    # 2. Configuración de la gráfica
    plt.figure(figsize=(12, 8))
    x = df['r']

    # 3. Definir paletas de colores
    # 'Blues' para las Reales, 'Reds' para las Imaginarias
    colores_reales = sns.color_palette("Blues_d", 4)
    colores_imag = sns.color_palette("Reds_d", 4)

    # 4. Graficar columnas Reales
    for i in range(1, 5):
        col_name = f'R{i}'
        plt.plot(x, df[col_name],
                 label=f'm = {i}',
                 color=colores_reales[i - 1],
                 linestyle='-',
                 linewidth=2)

    # 5. Graficar columnas Imaginarias
    for i in range(1, 5):
        col_name = f'I{i}'
        plt.plot(x, df[col_name],
                 label=f'm = -{i}',
                 color=colores_imag[i - 1],
                 linestyle='-',
                 linewidth=2)

    # 6. Estética profesional
    plt.title(f'Autofunción de la Densidad de las Partículas Rápidas (n=1 y bet0_f={bet0_f})', fontsize=14, pad=20)
    plt.xlabel('Radio en el reactor', fontsize=12)
    plt.ylabel('Densidad de las EP', fontsize=12)

    # Referencia visual: línea en cero
    plt.axhline(0, color='black', linewidth=0.8, alpha=0.3)

    plt.grid(True, which='both', linestyle=':', alpha=0.5)

    # Leyenda organizada
    plt.legend(title="Modos poloidales", loc='center left', bbox_to_anchor=(1, 0.5), frameon=True)

    plt.tight_layout()

    # 7. Guardar y mostrar
    plt.savefig(NF_FILE, dpi=300)



def graficar_phi(file_path, file_name, bet0_f):
    PHI_FILE = f"./Graficas_auto/phi/{file_name}"

    try:
        column_names = ['r', 'R1', 'R2', 'R3', 'R4', 'I1', 'I2', 'I3', 'I4']
        df = pd.read_csv(file_path, sep=r'\s+', skiprows=1, names=column_names)
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return

    # 2. Configuración de la gráfica
    plt.figure(figsize=(12, 8))
    x = df['r']

    # 3. Definir paletas de colores
    # 'Blues' para las Reales, 'Reds' para las Imaginarias
    colores_reales = sns.color_palette("Blues_d", 4)
    colores_imag = sns.color_palette("Reds_d", 4)

    # 4. Graficar columnas Reales
    for i in range(1, 5):
        col_name = f'R{i}'
        plt.plot(x, df[col_name],
                 label=f'm = {i}',
                 color=colores_reales[i - 1],
                 linestyle='-',
                 linewidth=2)

    # 5. Graficar columnas Imaginarias
    for i in range(1, 5):
        col_name = f'I{i}'
        plt.plot(x, df[col_name],
                 label=f'm = -{i}',
                 color=colores_imag[i - 1],
                 linestyle='-',
                 linewidth=2)

    # 6. Estética profesional
    plt.title(f'Autofunción del Potencial Electroestático del Plasma (n=1 y bet0_f={bet0_f})', fontsize=14, pad=20)
    plt.xlabel('Radio en el reactor', fontsize=12)
    plt.ylabel('Potencial del Plasma', fontsize=12)

    # Referencia visual: línea en cero
    plt.axhline(0, color='black', linewidth=0.8, alpha=0.3)

    plt.grid(True, which='both', linestyle=':', alpha=0.5)

    # Leyenda organizada
    plt.legend(title="Modos poloidales", loc='center left', bbox_to_anchor=(1, 0.5), frameon=True)

    plt.tight_layout()

    # 7. Guardar y mostrar
    plt.savefig(PHI_FILE, dpi=300)



def graficar_pr(file_path, file_name, bet0_f):
    PR_FILE = f"./Graficas_auto/pr/{file_name}"

    try:
        column_names = ['r', 'R1', 'R2', 'R3', 'R4', 'I1', 'I2', 'I3', 'I4']
        df = pd.read_csv(file_path, sep=r'\s+', skiprows=1, names=column_names)
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return

    # 2. Configuración de la gráfica
    plt.figure(figsize=(12, 8))
    x = df['r']

    # 3. Definir paletas de colores
    # 'Blues' para las Reales, 'Reds' para las Imaginarias
    colores_reales = sns.color_palette("Blues_d", 4)
    colores_imag = sns.color_palette("Reds_d", 4)

    # 4. Graficar columnas Reales
    for i in range(1, 5):
        col_name = f'R{i}'
        plt.plot(x, df[col_name],
                 label=f'm = {i}',
                 color=colores_reales[i - 1],
                 linestyle='-',
                 linewidth=2)

    # 5. Graficar columnas Imaginarias
    for i in range(1, 5):
        col_name = f'I{i}'
        plt.plot(x, df[col_name],
                 label=f'm = -{i}',
                 color=colores_imag[i - 1],
                 linestyle='-',
                 linewidth=2)

    # 6. Estética profesional
    plt.title(f'Autofunción de la Presión del Plasma Térmico (n=1 y bet0_f={bet0_f})', fontsize=14, pad=20)
    plt.xlabel('Radio en el reactor', fontsize=12)
    plt.ylabel('Presión (Temperatura y Densidad del plasma)', fontsize=12)

    # Referencia visual: línea en cero
    plt.axhline(0, color='black', linewidth=0.8, alpha=0.3)

    plt.grid(True, which='both', linestyle=':', alpha=0.5)

    # Leyenda organizada
    plt.legend(title="Modos poloidales", loc='center left', bbox_to_anchor=(1, 0.5), frameon=True)

    plt.tight_layout()

    # 7. Guardar y mostrar
    plt.savefig(PR_FILE, dpi=300)