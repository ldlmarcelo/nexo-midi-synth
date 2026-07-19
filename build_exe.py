"""
Script de empaquetado autónomo para Windows usando PyInstaller.

Uso en la máquina Windows:
    pip install pyinstaller
    python build_exe.py

Genera el ejecutable en la carpeta dist/NEXO_MIDI_Synth/
"""

import os
import sys
import subprocess

CARPETA_RAIZ = os.path.dirname(os.path.abspath(__file__))


def build():
    print("=== Empaquetando NEXO MIDI Synth ===")

    # Comprobar pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("❌ Error: PyInstaller no está instalado en Python.")
        print("Instalalo ejecutando en tu consola: pip install pyinstaller")
        sys.exit(1)

    # Usar el separador de rutas nativo del OS (';' en Windows, ':' en Linux)
    sep = os.pathsep

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NEXO_MIDI_Synth",
        "--noconsole",
        "--onedir",
        "--clean",
        f"--add-data=core{sep}core",
        f"--add-data=gui{sep}gui",
        "main.py"
    ]

    print(f"Ejecutando comando PyInstaller:\n  {' '.join(cmd)}\n")
    
    # Ejecutar mostrando salida en tiempo real
    result = subprocess.run(cmd, cwd=CARPETA_RAIZ)

    if result.returncode == 0:
        exe_path = os.path.join(CARPETA_RAIZ, "dist", "NEXO_MIDI_Synth", "NEXO_MIDI_Synth.exe")
        print("\n✅ ¡Empaquetado completado exitosamente!")
        print(f"📍 El ejecutable se encuentra en:\n   {exe_path}\n")
        print("⚠️ RECORDATORIO IMPORTANTE:")
        print("Asegurate de copiar en esa misma carpeta (dist/NEXO_MIDI_Synth/):")
        print("  1. El archivo SoundFont (.sf2)")
        print("  2. Las DLLs de FluidSynth (.dll)")
    else:
        print("\n❌ PyInstaller terminó con errores.")


if __name__ == "__main__":
    build()
