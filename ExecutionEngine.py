"""
---------------- EJECUTAR FAR3d -------------------


"""

import subprocess
import os


class ExecutionEngine:
    def __init__(self, work_dir):
        self.work_dir = os.path.abspath(work_dir)

    def run_simulation(self, run_id=1, timeout_seconds=6000):
        """
        Lanza la simulación mediante WSL y espera a que termine.
        """
        command = ["wsl", "./xfar3d"]

        print(f"    [>] Ejecutando: {' '.join(command)} en {self.work_dir}...")

        try:
            result = subprocess.run(
                command,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )

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