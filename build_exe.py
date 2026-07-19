"""
Script de empaquetado autónomo para Windows usando PyInstaller.

Uso en la máquina Windows:
    pip install pyinstaller
    python build_exe.py

Genera el ejecutable limpio en dist/NEXO_MIDI_Synth/ y purga la basura temporal (build/, .spec, etc.)
"""

import os
import sys
import subprocess
import shutil

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

    sep = os.pathsep
    build_dir = os.path.join(CARPETA_RAIZ, "build")
    dist_dir = os.path.join(CARPETA_RAIZ, "dist")
    spec_file = os.path.join(CARPETA_RAIZ, "NEXO_MIDI_Synth.spec")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NEXO_MIDI_Synth",
        "--noconsole",
        "--onedir",
        "--clean",
        f"--workpath={build_dir}",
        f"--distpath={dist_dir}",
        f"--add-data=core{sep}core",
        f"--add-data=gui{sep}gui",
        "main.py"
    ]

    print(f"Ejecutando PyInstaller:\n  {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=CARPETA_RAIZ)

    if result.returncode == 0:
        exe_path = os.path.join(dist_dir, "NEXO_MIDI_Synth", "NEXO_MIDI_Synth.exe")
        print("\n✅ ¡Empaquetado completado exitosamente!")
        print(f"📍 Ejecutable generado en:\n   {exe_path}\n")

        # Purga de basura de compilación intermedia
        print("🧹 Limpiando archivos temporales de compilación (build/, .spec)...")
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir, ignore_errors=True)
        if os.path.exists(spec_file):
            try:
                os.remove(spec_file)
            except OSError:
                pass

        print("✨ Limpieza completada. Solo conservamos dist/NEXO_MIDI_Synth/\n")
        print("⚠️ RECORDATORIO IMPORTANTE:")
        print("Asegurate de que en dist/NEXO_MIDI_Synth/ estén copiados:")
        print("  1. El archivo SoundFont (.sf2)")
        print("  2. Las DLLs de FluidSynth (.dll)")
    else:
        print("\n❌ PyInstaller terminó con errores.")


if __name__ == "__main__":
