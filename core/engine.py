"""
Motor MIDI + FluidSynth para el módulo de sonido virtual.

Encapsula la captura MIDI (rtmidi) y la síntesis (FluidSynth) en una clase
que emite señales Qt para actualizar la GUI sin bloqueos.

Incluye:
- Detección soberana de SoundFonts (soporta PyInstaller frozen mode)
- Transformación de curva de velocity (Soft/Linear/Hard)
- Controles de Reverb y Chorus nativos de FluidSynth
- Transposición por semitonos y octavas
- Función de Pánico (All Notes Off / Reset)
- Favoritos / Presets persistentes
"""

import os
import sys
import glob
import json

from PySide6.QtCore import QObject, Signal

# Determinación robusta de la carpeta raíz de ejecución (compatible con PyInstaller .exe)
if getattr(sys, 'frozen', False):
    # Modo empaquetado (.exe de PyInstaller)
    CARPETA_RAIZ = os.path.dirname(os.path.abspath(sys.executable))
else:
    # Modo desarrollo (Python script)
    CARPETA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Agregar directorio de DLLs si estamos en Windows
if hasattr(os, "add_dll_directory"):
    for dll_dir in [CARPETA_RAIZ, getattr(sys, '_MEIPASS', '')]:
        if dll_dir and os.path.exists(dll_dir):
            try:
                os.add_dll_directory(dll_dir)
            except (FileNotFoundError, OSError):
                pass

try:
    import rtmidi
    import fluidsynth
except ImportError as e:
    print(f"Faltan dependencias: {e}")
    print("Ejecutá: pip install python-rtmidi pyfluidsynth")
    sys.exit(1)

# Constantes MIDI
NOTE_OFF = 0x80
NOTE_ON = 0x90
CONTROL_CHANGE = 0xB0
PROGRAM_CHANGE = 0xC0
PITCH_BEND = 0xE0

# Archivo de configuración persistente
CONFIG_FILE = os.path.join(CARPETA_RAIZ, "config.json")

DEFAULT_FAVORITES = [0, 4, 19, 48, 88, 56]  # Piano, EP, Organ, Ensemble, Pad, Trumpet


def _load_config() -> dict:
    """Carga la configuración persistente desde config.json."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_config(config: dict):
    """Guarda la configuración persistente en config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except OSError:
        pass


class MidiEngine(QObject):
    """
    Motor de captura MIDI y síntesis de audio.

    Señales emitidas (thread-safe vía Qt):
        note_played(int, int)       - (nota MIDI original, velocity ajustada)
        note_released(int)          - nota MIDI liberada
        instrument_changed(int)     - nuevo program number
        connection_changed(bool)    - estado de conexión MIDI
        favorites_changed(list)     - lista actualizada de instrumentos favoritos
    """

    note_played = Signal(int, int)
    note_released = Signal(int)
    instrument_changed = Signal(int)
    connection_changed = Signal(bool)
    favorites_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._midiin = rtmidi.MidiIn()
        self._synth = None
        self._sfid = None
        self._connected = False

        # Estado por defecto / persistente
        config = _load_config()
        self._current_instrument = config.get("instrument", 0)
        self._volume = config.get("volume", 100)
        self._velocity_curve = config.get("velocity_curve", 1.0)
        self._reverb_level = config.get("reverb_level", 0.3)  # 0.0 a 1.0
        self._chorus_level = config.get("chorus_level", 0.0)  # 0.0 a 1.0
        self._transpose = config.get("transpose", 0)           # -12 a +12 semitonos
        self._octave = config.get("octave", 0)                 # -3 a +3 octavas
        self._favorites = config.get("favorites", list(DEFAULT_FAVORITES))

    # ── Dispositivos MIDI ──────────────────────────────────────────

    def get_midi_ports(self) -> list[str]:
        """Devuelve la lista de puertos MIDI disponibles."""
        return self._midiin.get_ports()

    # ── SoundFonts ─────────────────────────────────────────────────

    def _get_search_directories(self) -> list[str]:
        """Devuelve todas las rutas donde buscar archivos .sf2."""
        dirs = [CARPETA_RAIZ, os.getcwd()]
        if hasattr(sys, '_MEIPASS'):
            dirs.append(getattr(sys, '_MEIPASS'))
        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_dirs = []
        for d in dirs:
            if d and d not in seen and os.path.exists(d):
                seen.add(d)
                unique_dirs.append(d)
        return unique_dirs

    def get_available_soundfonts(self) -> list[str]:
        """Busca archivos .sf2 en la carpeta del ejecutable y working directory."""
        sf_files = set()
        for d in self._get_search_directories():
            pattern = os.path.join(d, "*.sf2")
            for f in glob.glob(pattern):
                sf_files.add(os.path.basename(f))
        return sorted(list(sf_files))

    def _resolve_soundfont_path(self, soundfont_name: str) -> str:
        """Encuentra la ruta completa para un nombre de archivo .sf2."""
        for d in self._get_search_directories():
            candidate = os.path.join(d, soundfont_name)
            if os.path.exists(candidate):
                return candidate
        return os.path.join(CARPETA_RAIZ, soundfont_name)

    # ── Conexión ───────────────────────────────────────────────────

    def connect(self, port_index: int, soundfont_name: str) -> bool:
        """
        Conecta al puerto MIDI indicado y carga el SoundFont.
        Retorna True si la conexión fue exitosa.
        """
        self.disconnect()

        try:
            self._midiin.open_port(port_index)
        except Exception:
            self.connection_changed.emit(False)
            return False

        # Inicializar FluidSynth
        self._synth = fluidsynth.Synth()
        self._synth.start(driver="dsound")

        # Resolver ruta completa del SoundFont
        sf_path = self._resolve_soundfont_path(soundfont_name)
        try:
            self._sfid = self._synth.sfload(sf_path)
        except Exception:
            self._midiin.close_port()
            self._synth.delete()
            self._synth = None
            self.connection_changed.emit(False)
            return False

        # Configurar estado inicial en el motor
        self._synth.program_select(0, self._sfid, 0, self._current_instrument)
        self._synth.cc(0, 7, self._volume)
        self._apply_reverb()
        self._apply_chorus()

        # Registrar callback MIDI
        self._midiin.set_callback(self._midi_callback)

        self._connected = True
        self.connection_changed.emit(True)

        # Guardar configuración
        self._persist_config()

        return True

    def disconnect(self):
        """Desconecta el puerto MIDI y detiene el sintetizador."""
        if self._midiin.is_port_open():
            self._midiin.cancel_callback()
            self._midiin.close_port()
        if self._synth:
            self._synth.delete()
            self._synth = None
            self._sfid = None
        self._connected = False
        self.connection_changed.emit(False)

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ── Controles de Instrumento ───────────────────────────────────

    @property
    def current_instrument(self) -> int:
        return self._current_instrument

    def set_instrument(self, program: int):
        """Cambia el instrumento activo (0-127)."""
        if not 0 <= program <= 127:
            return
        self._current_instrument = program
        if self._synth and self._sfid is not None:
            self._synth.program_select(0, self._sfid, 0, program)
        self.instrument_changed.emit(program)
        self._persist_config()

    # ── Controles de Volumen y Curva de Velocity ───────────────────

    @property
    def volume(self) -> int:
        return self._volume

    def set_volume(self, value: int):
        """Ajusta el volumen maestro (0-127)."""
        self._volume = max(0, min(127, value))
        if self._synth:
            self._synth.cc(0, 7, self._volume)
        self._persist_config()

    @property
    def velocity_curve(self) -> float:
        return self._velocity_curve

    def set_velocity_curve(self, exponent: float):
        """Ajusta el exponente de la curva de velocity (0.1 a 3.0)."""
        self._velocity_curve = max(0.1, min(3.0, exponent))
        self._persist_config()

    def _apply_velocity_curve(self, velocity: int) -> int:
        """Transforma la velocity cruda según la curva configurada."""
        if self._velocity_curve == 1.0:
            return velocity
        normalized = velocity / 127.0
        adjusted = normalized ** self._velocity_curve
        return max(1, min(127, int(adjusted * 127)))

    # ── Efectos: Reverb y Chorus ────────────────────────────────────

    @property
    def reverb_level(self) -> float:
        return self._reverb_level

    def set_reverb_level(self, level: float):
        """Ajusta el nivel de Reverb (0.0 a 1.0)."""
        self._reverb_level = max(0.0, min(1.0, level))
        self._apply_reverb()
        self._persist_config()

    def _apply_reverb(self):
        if not self._synth:
            return
        try:
            roomsize = 0.6
            damping = 0.4
            width = 1.0
            self._synth.set_reverb(roomsize, damping, width, self._reverb_level)
            self._synth.reverb_on(1 if self._reverb_level > 0 else 0)
        except Exception:
            pass

    @property
    def chorus_level(self) -> float:
        return self._chorus_level

    def set_chorus_level(self, level: float):
        """Ajusta el nivel de Chorus (0.0 a 1.0)."""
        self._chorus_level = max(0.0, min(1.0, level))
        self._apply_chorus()
        self._persist_config()

    def _apply_chorus(self):
        if not self._synth:
            return
        try:
            nr = 3
            scaled_level = self._chorus_level * 5.0
            speed = 0.3
            depth = 8.0
            chorus_type = 0
            self._synth.set_chorus(nr, scaled_level, speed, depth, chorus_type)
            self._synth.chorus_on(1 if self._chorus_level > 0 else 0)
        except Exception:
            pass

    # ── Transposición y Octavas ─────────────────────────────────────

    @property
    def transpose(self) -> int:
        return self._transpose

    def set_transpose(self, semitones: int):
        """Ajusta la transposición (-12 a +12 semitonos)."""
        self.panic()
        self._transpose = max(-12, min(12, semitones))
        self._persist_config()

    @property
    def octave(self) -> int:
        return self._octave

    def set_octave(self, octs: int):
        """Ajusta el desplazamiento de octava (-3 a +3)."""
        self.panic()
        self._octave = max(-3, min(3, octs))
        self._persist_config()

    # ── Botón de Pánico (All Notes Off) ─────────────────────────────

    def panic(self):
        """Corta todas las notas resonando inmediatamente."""
        if self._synth:
            for chan in range(16):
                self._synth.cc(chan, 123, 0)  # All Notes Off
                self._synth.cc(chan, 121, 0)  # Reset All Controllers
            try:
                self._synth.system_reset()
            except Exception:
                pass

    # ── Favoritos / Presets ─────────────────────────────────────────

    @property
    def favorites(self) -> list[int]:
        return self._favorites

    def set_favorite(self, slot_index: int, program: int):
        """Guarda un instrumento en un slot de favoritos (0-5)."""
        if 0 <= slot_index < len(self._favorites) and 0 <= program <= 127:
            self._favorites[slot_index] = program
            self.favorites_changed.emit(list(self._favorites))
            self._persist_config()

    # ── Callback MIDI (corre en thread de rtmidi) ─────────────────

    def _midi_callback(self, event, data=None):
        """Procesa mensajes MIDI entrantes. Corre en thread separado."""
        message, _delta = event
        if not message:
            return

        status = message[0] & 0xF0

        # Calcular notas transpuestas
        shift = self._transpose + (self._octave * 12)

        if status == NOTE_ON and len(message) >= 3:
            raw_note, vel = message[1], message[2]
            target_note = max(0, min(127, raw_note + shift))
            if vel > 0:
                adjusted_vel = self._apply_velocity_curve(vel)
                self._synth.noteon(0, target_note, adjusted_vel)
                self.note_played.emit(target_note, adjusted_vel)
            else:
                self._synth.noteoff(0, target_note)
                self.note_released.emit(target_note)

        elif status == NOTE_OFF and len(message) >= 3:
            raw_note = message[1]
            target_note = max(0, min(127, raw_note + shift))
            self._synth.noteoff(0, target_note)
            self.note_released.emit(target_note)

        elif status == CONTROL_CHANGE and len(message) >= 3:
            self._synth.cc(0, message[1], message[2])

        elif status == PROGRAM_CHANGE and len(message) >= 2:
            program = message[1]
            self._current_instrument = program
            self._synth.program_change(0, program)
            self.instrument_changed.emit(program)
            self._persist_config()

        elif status == PITCH_BEND and len(message) >= 3:
            value = message[1] + (message[2] << 7)
            self._synth.pitch_bend(0, value - 8192)

    # ── Persistencia ───────────────────────────────────────────────

    def _persist_config(self):
        """Guarda la configuración actual en disco."""
        config = _load_config()
        config["instrument"] = self._current_instrument
        config["volume"] = self._volume
        config["velocity_curve"] = self._velocity_curve
        config["reverb_level"] = self._reverb_level
        config["chorus_level"] = self._chorus_level
        config["transpose"] = self._transpose
        config["octave"] = self._octave
        config["favorites"] = self._favorites
        _save_config(config)

    # ── Cleanup ────────────────────────────────────────────────────

    def cleanup(self):
        """Libera todos los recursos."""
        self.disconnect()
