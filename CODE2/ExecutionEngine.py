"""
---------------- EJECUTAR FAR3d -------------------


"""

import subprocess
import os


class ExecutionEngine:
    def __init__(self, work_dir):
        """
        Inicializa el motor de ejecución.
        :param work_dir: Directorio donde debe ejecutarse el comando (ej. './DIIID')
        """
        self.work_dir = os.path.abspath(work_dir)

    def run_simulation(self, run_id=1, timeout_seconds=6000):
        """
        Lanza la simulación mediante WSL y espera a que termine.
        :param run_id: Identificador de la simulación actual (para los logs).
        :param timeout_seconds: Tiempo máximo de ejecución en segundos antes de abortar.
        :return: Diccionario con el estado de la ejecución.
        """
        # El comando que lanzarías en tu terminal
        command = ["wsl", "./xfar3d"]

        print(f"    [>] Ejecutando: {' '.join(command)} en {self.work_dir}...")

        try:
            # cwd (Current Working Directory) asegura que el comando se lanza DENTRO de la carpeta DIIID
            # capture_output=True guarda lo que el programa "imprime"
            # text=True nos devuelve strings en lugar de bytes crudos
            result = subprocess.run(
                command,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )

            # Verificamos si el código de salida de xfar3d es 0 (éxito en Linux/C)
            if result.returncode == 0:
                print(f"    [+] Simulación {run_id} completada con éxito.")
                status = "SUCCESS"
            else:
                print(f"    [-] Simulación {run_id} falló con código de salida: {result.returncode}")
                status = "FAILED"

            return {
                "status": status,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired as e:
            print(
                f"    [!] ALERTA: La simulación {run_id} excedió el tiempo límite de {timeout_seconds}s y fue abortada.")
            return {
                "status": "TIMEOUT",
                "return_code": None
            }
        except FileNotFoundError:
            print("    [!] ERROR CRÍTICO: No se encontró 'wsl' en el sistema o el ejecutable './xfar3d'.")
            return {
                "status": "ERROR",
                "stdout": "",
                "stderr": "wsl o ./xfar3d no encontrados",
                "return_code": None
            }