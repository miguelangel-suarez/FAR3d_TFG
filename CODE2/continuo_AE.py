import pandas as pd
import matplotlib.pyplot as plt

# 1. Cargar los datos
df = pd.read_csv('out_n=1.txt', sep='\t', header=None)

# 2. Eliminar la primera fila (para quitar el valor gigante E+10)
df = df[(df < 1e9).all(axis=1)]

# 3. Extraer el eje X (primera columna, índice 0)
x = df.iloc[:, 0]

# 4. Extraer el eje Y
columna_y = 1
y = df.iloc[:, columna_y]

# 5. Configurar la figura
plt.figure(figsize=(10, 6))

# 6. Dibujar la gráfica usando scatter (dispersión)
# alpha=0.6 hace los puntos un poco transparentes para ver dónde se solapan
# s=10 controla el tamaño del punto
plt.scatter(x, y, alpha=0.5, s=3, label=f'n = {y}')

# 7. Personalizar la gráfica
plt.xlabel('Posición radial en DIII-D')
plt.ylabel('Frecuencias del continuo')
plt.title(f'Espectro del continuo de Alfvén del modo n={columna_y}')
plt.grid(True)
plt.tight_layout()

# 8. Mostrar la gráfica
plt.savefig(f'espectros_continuos_Alfven/continuo_n={columna_y}.png')
plt.show()