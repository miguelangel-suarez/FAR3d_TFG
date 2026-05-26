import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def graficar_omr_gam(file_path):
    GAM_DIRECTORY = "./Graficas_gam"
    OMR_DIRECTORY = "./Graficas_omr"

    # 1. Cargar los datos
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{file_path}'")
        return

    # Asegurarnos de que 'm' se trate como una categoría para la leyenda
    df['m'] = df['m'].astype(str)

    # 2. Identificar las variables_eigen únicas
    variables_eigen = df['variable_eigen'].unique()
    print(f"Se han detectado {len(variables_eigen)} variables eigen: {variables_eigen}")

    # Configuración estética de Seaborn
    sns.set_theme(style="whitegrid")

    # GRAFICAS PARA GAM
    for var in variables_eigen:
        plt.figure(figsize=(10, 6))

        # Filtrar el dataframe para la variable actual
        subset = df[df['variable_eigen'] == var]

        # Crear la gráfica de líneas
        # x = bet0_f, y = gam, hue = m (leyenda)
        qual_palette = sns.color_palette("pastel", 4)
        plot = sns.lineplot(
            data=subset,
            x='bet0_f',
            y='gam',
            hue='m',
            marker='o',
            palette=qual_palette
        )

        # Personalización del gráfico
        plt.title(f'Evolución de tasa_crecimiento vs bet0_f (Variable Eigen: {var})', fontsize=14)
        plt.xlabel('bet0_f', fontsize=12)
        plt.ylabel('gam', fontsize=12)
        plt.legend(title='Valor de m', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Ajustar diseño para que no se corte la leyenda
        plt.tight_layout()

        # 4. Guardar la gráfica
        filename = f"{GAM_DIRECTORY}/grafica_gam_{var}.png"
        plt.savefig(filename, dpi=300)
        print(f"Guardado: {filename}")

        # Cerrar la figura para liberar memoria
        plt.close()

        # GRAFICAS PARA OM_R
        for var in variables_eigen:
            plt.figure(figsize=(10, 6))

            # Filtrar el dataframe para la variable actual
            subset = df[df['variable_eigen'] == var]

            # Crear la gráfica de líneas
            # x = bet0_f, y = om_r, hue = m (leyenda)
            qual_palette = sns.color_palette("pastel", 4)
            plot = sns.lineplot(
                data=subset,
                x='bet0_f',
                y='om_r',
                hue='m',
                marker='o',
                palette=qual_palette
            )

            # Personalización del gráfico
            plt.title(f'Evolución de frecuencia vs bet0_f (Variable Eigen: {var})', fontsize=14)
            plt.xlabel('bet0_f', fontsize=12)
            plt.ylabel('om_r', fontsize=12)
            plt.legend(title='Valor de m', bbox_to_anchor=(1.05, 1), loc='upper left')

            # Ajustar diseño para que no se corte la leyenda
            plt.tight_layout()

            # 4. Guardar la gráfica
            filename = f"{OMR_DIRECTORY}/grafica_omr_{var}.png"
            plt.savefig(filename, dpi=300)
            print(f"Guardado: {filename}")

            # Cerrar la figura para liberar memoria
            plt.close()