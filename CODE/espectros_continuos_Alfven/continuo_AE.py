"""
Archivo AUXILIAR para leer el archivo TXT del continuo de frecuencias, limpiar el archivo,
y generar tanto el Dataframe final como las gráficas del continuo de cada n

"""
from math import sqrt
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('out_n=1.txt', sep='\t', header=None)

# Transformar los datos según las normas establecidas
df = df[(df < 500).all(axis=1)]
df[0] = df[0].apply(sqrt)
df[5] = df[4]
df.to_csv("df_continuo.csv")

# Extraer el eje X (primera columna, índice 0)
x = df.iloc[:, 0]

# Extraer el eje Y
columna_y = 5
y = df.iloc[:, columna_y]


plt.figure(figsize=(10, 6))
plt.scatter(x, y, alpha=0.5, s=3, label=f'n = {y}')

plt.xlabel('Posición radial en DIII-D')
plt.ylabel('Frecuencias del continuo')
plt.title(f'Espectro del continuo de Alfvén del modo n={columna_y}')
plt.grid(True)
plt.tight_layout()

# Guardar gráfica
plt.savefig(f'espectros_continuos_Alfven/continuo_n={columna_y}.png')
plt.show()