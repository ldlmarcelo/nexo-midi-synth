"""
Módulo de sonido MIDI virtual - convierte tu PC en un sound module GM
para tu Samson Carbon 49 (o cualquier teclado MIDI).

Escucha el teclado conectado por MIDI/USB y reproduce el sonido
en tiempo real usando un soundfont General MIDI a través de FluidSynth.

Mientras suena, podés escribir un número (0-127) + Enter en la
consola para cambiar de instrumento sin cortar el programa.

------------------------------------------------------------------
USO:
------------------------------------------------------------------
   python midi_sound_module.py
   - Elegí el dispositivo MIDI
   - Tocá el teclado
   - Escribí un número (0-127) + Enter para cambiar de instrumento
   - Escribí "lista" + Enter para ver todos los instrumentos de nuevo
   - Ctrl+C para salir
------------------------------------------------------------------
"""

import os
import sys
import threading
import time

CARPETA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
if hasattr(os, "add_dll_directory"):
    try:
        os.add_dll_directory(CARPETA_SCRIPT)
    except (FileNotFoundError, OSError):
        pass

try:
    import rtmidi
    import fluidsynth
except ImportError as e:
    print("Faltan librerías o no se encontró la DLL de FluidSynth.")
    print(f"Detalle: {e}")
    print()
    print("Verificá:")
    print("  1) pip install python-rtmidi pyfluidsynth")
    print("  2) Que las DLLs de FluidSynth estén en esta carpeta:")
    print(f"     {CARPETA_SCRIPT}")
    sys.exit(1)

SOUNDFONT_PATH = "FluidR3_GM_GS.sf2"  # cambiá el nombre si tu archivo se llama distinto
DEFAULT_INSTRUMENT = 0  # 0 = Acoustic Grand Piano (General MIDI)

NOTE_OFF = 0x80
NOTE_ON = 0x90
CONTROL_CHANGE = 0xB0
PROGRAM_CHANGE = 0xC0
PITCH_BEND = 0xE0

# Lista estándar de los 128 instrumentos General MIDI (número: nombre)
GM_INSTRUMENTS = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavinet",
    "Celesta", "Glockenspiel", "Music Box", "Vibraphone",
    "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ",
    "Reed Organ", "Accordion", "Harmonica", "Tango Accordion",
    "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)", "Electric Guitar (clean)",
    "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar", "Guitar Harmonics",
    "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2",
    "Violin", "Viola", "Cello", "Contrabass",
    "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani",
    "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2",
    "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit",
    "Trumpet", "Trombone", "Tuba", "Muted Trumpet",
    "French Horn", "Brass Section", "Synth Brass 1", "Synth Brass 2",
    "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax",
    "Oboe", "English Horn", "Bassoon", "Clarinet",
    "Piccolo", "Flute", "Recorder", "Pan Flute",
    "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)",
    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass+lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)",
    "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)",
    "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",
    "Sitar", "Banjo", "Shamisen", "Koto",
    "Kalimba", "Bagpipe", "Fiddle", "Shanai",
    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock",
    "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal",
    "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet",
    "Telephone Ring", "Helicopter", "Applause", "Gunshot",
]


def mostrar_lista_instrumentos():
    print("\n--- Instrumentos General MIDI (0-127) ---")
    for i, nombre in enumerate(GM_INSTRUMENTS):
        print(f"  {i:3d}  {nombre}")
    print("------------------------------------------\n")


def elegir_dispositivo_midi(midiin):
    puertos = midiin.get_ports()
    if not puertos:
        print("No se detectó ningún dispositivo MIDI. ¿Está conectado el Carbon 49?")
        sys.exit(1)

    print("\nDispositivos MIDI detectados:")
    for i, nombre in enumerate(puertos):
        print(f"  [{i}] {nombre}")

    while True:
        try:
            idx = int(input("\nElegí el número de tu Carbon 49: "))
            if 0 <= idx < len(puertos):
                return idx
        except ValueError:
            pass
        print("Opción inválida, probá de nuevo.")


def hilo_control_instrumentos(fs, sfid, estado):
    """Corre en un hilo aparte, escuchando comandos de texto sin bloquear el MIDI."""
    while True:
        try:
            entrada = input().strip().lower()
        except EOFError:
            return

        if entrada == "lista":
            mostrar_lista_instrumentos()
            continue

        try:
            num = int(entrada)
        except ValueError:
            print("Escribí un número del 0 al 127, o 'lista' para ver los instrumentos.")
            continue

        if 0 <= num <= 127:
            fs.program_select(0, sfid, 0, num)
            estado["instrumento"] = num
            print(f">> Instrumento cambiado a: [{num}] {GM_INSTRUMENTS[num]}")
        else:
            print("El número tiene que estar entre 0 y 127.")


def main():
    print("=== Módulo de sonido MIDI virtual ===")

    midiin = rtmidi.MidiIn()
    idx = elegir_dispositivo_midi(midiin)
    nombre_puerto = midiin.get_ports()[idx]
    midiin.open_port(idx)

    fs = fluidsynth.Synth()
    fs.start(driver="dsound")

    try:
        sfid = fs.sfload(SOUNDFONT_PATH)
    except Exception:
        print(f"No se pudo cargar el soundfont '{SOUNDFONT_PATH}'.")
        print("Verificá que el archivo .sf2 esté en esta misma carpeta.")
        sys.exit(1)

    fs.program_select(0, sfid, 0, DEFAULT_INSTRUMENT)
    estado = {"instrumento": DEFAULT_INSTRUMENT}

    def callback(evento, data=None):
        mensaje, _delta_tiempo = evento
        if not mensaje:
            return
        status = mensaje[0] & 0xF0

        if status == NOTE_ON and len(mensaje) >= 3:
            nota, vel = mensaje[1], mensaje[2]
            print(f"Nota: {nota}  Velocidad: {vel}")
            if vel > 0:
                fs.noteon(0, nota, vel)
            else:
                fs.noteoff(0, nota)
        elif status == NOTE_OFF and len(mensaje) >= 3:
            fs.noteoff(0, mensaje[1])
        elif status == CONTROL_CHANGE and len(mensaje) >= 3:
            fs.cc(0, mensaje[1], mensaje[2])
        elif status == PROGRAM_CHANGE and len(mensaje) >= 2:
            num = mensaje[1]
            fs.program_change(0, num)
            estado["instrumento"] = num
            print(f">> (desde el teclado) Instrumento cambiado a: [{num}] {GM_INSTRUMENTS[num]}")
        elif status == PITCH_BEND and len(mensaje) >= 3:
            valor = mensaje[1] + (mensaje[2] << 7)
            fs.pitch_bend(0, valor - 8192)

    midiin.set_callback(callback)

    print(f"\nConectado a: {nombre_puerto}")
    print(f"Instrumento actual: [{DEFAULT_INSTRUMENT}] {GM_INSTRUMENTS[DEFAULT_INSTRUMENT]}")
    print("\nMientras tocás, podés escribir acá:")
    print("  - un número (0-127) + Enter -> cambiar de instrumento")
    print("  - 'lista' + Enter -> ver todos los instrumentos disponibles")
    print("  - Ctrl+C -> salir\n")

    hilo = threading.Thread(target=hilo_control_instrumentos, args=(fs, sfid, estado), daemon=True)
    hilo.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nCerrando...")
    finally:
        midiin.close_port()
        fs.delete()


if __name__ == "__main__":
    main()
