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
import shutil

CARPETA_RAIZ = os.path.dirname(os.path.abspath(__file__))


def build():
    print("=== Empaquetando NEXO MIDI Synth para Windows ===")

    # Comprobar pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("❌ Error: PyInstaller no está instalado.")
        print("Instalalo ejecutando: pip install pyinstaller")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NEXO_MIDI_Synth",
        "--noconsole",  # Ocultar ventana de comandos (consola)
        "--onedir",     # Carpeta ejecutable limpia (arranca más rápido que --onefile)
        "--clean",
        "--add-data=core;core",
        "--add-data=gui;gui",
        "main.py"
    ]

    print(f"Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=CARPETA_RAIZ)

    if result.returncode == 0:
        print("\n✅ ¡Empaquetado exitoso!")
        print("El ejecutable fue generado en:")
        print(os.path.join(CARPETA_RAIZ, "dist", "NEXO_MIDI_Synth", "NEXO_MIDI_Synth.exe"))
        print("\nRECORDATORIO: Asegurate de que en esa misma carpeta estén:")
        print("  1) El archivo SoundFont (.sf2)")
        print("  2) Las DLLs de FluidSynth (.dll)")
    else:
        print("\n❌ Ocurrió un error durante el empaquetado.")


if __name__ == "__main__":
    build()
