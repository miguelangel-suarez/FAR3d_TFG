import os
import pandas as pd

def extract_matrix(filename, work_dir):
    """
    Lee archivos de matrices 2D (como nf_0000 o phi_0000) y los devuelve como arrays de NumPy.
    """
    filepath = os.path.join(work_dir, filename)
    if not os.path.exists(filepath):
        print("No se encontro el archivo")
        return None

    try:
        # loadtxt es rapidísimo para leer matrices de texto plano con valores numéricos
        df = pd.read_csv(filepath, header=0, delimiter="\t")
        df.to_csv(os.path.join(work_dir, "nf_0000.csv"), index=False)
    except Exception as e:
        print(f"    [!] Error al leer {filename}: {e}")
        return None

if __name__ == "__main__":
    extract_matrix("nf_0000", "./")