# nexo-midi-synth

Módulo de sonido MIDI virtual — convierte tu PC Windows en un sintetizador General MIDI para el **Samson Carbon 49** (o cualquier controlador MIDI USB).

> **Sin módulo de sonido físico.** Solo teclado → USB → Python → FluidSynth → parlantes.

## Stack

| Componente | Tecnología |
|---|---|
| Captura MIDI | `python-rtmidi` (RtMidi) |
| Síntesis | `pyfluidsynth` (FluidSynth) |
| SoundFont | `FluidR3_GM_GS.sf2` (General MIDI) |
| Driver de audio | DirectSound (`dsound`) |
| Interfaz | Consola interactiva |

## Requisitos

- **Windows 10/11** (por DirectSound)
- **Python 3.10+**
- **Samson Carbon 49** (o cualquier controlador MIDI USB)

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/ldlmarcelo/nexo-midi-synth.git
cd nexo-midi-synth
```

### 2. Instalar dependencias Python
```bash
pip install python-rtmidi pyfluidsynth
```

### 3. DLLs de FluidSynth
FluidSynth necesita sus DLLs nativas en la misma carpeta del script:
- Descargar desde [FluidSynth releases](https://github.com/FluidSynth/fluidsynth/releases)
- Copiar `libfluidsynth-3.dll` (y dependencias) a la carpeta del proyecto

### 4. SoundFont
Descargar `FluidR3_GM_GS.sf2` y colocarlo en la carpeta del proyecto:
- [FluidR3 en MuseScore](https://ftp.osuosl.org/pub/musescore/soundfont/FluidR3_GM_GS.sf2)

## Uso

```bash
python midi_sound_module.py
```

1. Seleccionar el dispositivo MIDI (Carbon 49)
2. Tocar el teclado — el sonido sale por los parlantes
3. Cambiar instrumento: escribir un número `0-127` + Enter
4. Ver lista de instrumentos: escribir `lista` + Enter
5. Salir: `Ctrl+C`

## Instrumentos

Los 128 instrumentos del estándar General MIDI están disponibles. Algunos destacados:

| # | Instrumento |
|---|---|
| 0 | Acoustic Grand Piano |
| 4 | Electric Piano 1 |
| 19 | Church Organ |
| 24 | Acoustic Guitar (nylon) |
| 40 | Violin |
| 56 | Trumpet |
| 73 | Flute |

## Roadmap & Futuras Nociones

- [x] Persistencia de instrumento y controles entre sesiones (`config.json`)
- [x] Curva de velocity ajustable por software (Soft / Linear / Hard)
- [x] Ruteo de efectos nativos de FluidSynth (`Reverb` y `Chorus` vía `CC 91` y `CC 93`)
- [x] Transposición por semitonos (-12 a +12) y octavas (-3 a +3)
- [x] Interfaz gráfica GUI (PySide6 / Dark DAW Style)
- [x] Script de empaquetado autónomo para Windows (`build_exe.py` + PyInstaller)

> 📌 Para consultar el roadmap completo de arquitectura avanzada (presets de sala, delay, arpegiador, layering y grabación), ver `ROADMAP.md`.

## Origen

Proyecto nacido de una sesión con Claude (Anthropic) y absorbido al ecosistema NEXO para su desarrollo continuo.

## Licencia

MIT
