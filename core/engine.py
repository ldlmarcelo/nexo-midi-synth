"""
Motor MIDI + FluidSynth para el módulo de sonido virtual.

Encapsula la captura MIDI (rtmidi) y la síntesis (FluidSynth) en una clase
que emite señales Qt para actualizar la GUI sin bloqueos.

Incluye transformación de curva de velocity para compensar
las limitaciones mecánicas de teclados económicos.
"""

import os
import sys
import glob
import json

from PySide6.QtCore import QObject, Signal

CARPETA_SCRIPT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(os, "add_dll_directory"):
    try:
        os.add_dll_directory(CARPETA_SCRIPT)
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
CONFIG_FILE = os.path.join(CARPETA_SCRIPT, "config.json")


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
        note_played(int, int)       - (nota MIDI, velocity ajustada)
        note_released(int)          - nota MIDI liberada
        instrument_changed(int)     - nuevo program number
        connection_changed(bool)    - estado de conexión MIDI
    """

    note_played = Signal(int, int)
    note_released = Signal(int)
    instrument_changed = Signal(int)
    connection_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._midiin = rtmidi.MidiIn()
        self._synth = None
        self._sfid = None
        self._connected = False
        self._current_instrument = 0
        self._volume = 100          # 0-127
        self._velocity_curve = 1.0  # exponente: <1 = soft, 1 = lineal, >1 = hard

        # Cargar configuración persistente
        config = _load_config()
        self._current_instrument = config.get("instrument", 0)
        self._volume = config.get("volume", 100)
        self._velocity_curve = config.get("velocity_curve", 1.0)

    # ── Dispositivos MIDI ──────────────────────────────────────────

    def get_midi_ports(self) -> list[str]:
        """Devuelve la lista de puertos MIDI disponibles."""
        return self._midiin.get_ports()

    # ── SoundFonts ─────────────────────────────────────────────────

    def get_available_soundfonts(self) -> list[str]:
        """Busca archivos .sf2 en la carpeta del proyecto."""
        pattern = os.path.join(CARPETA_SCRIPT, "*.sf2")
        return [os.path.basename(f) for f in glob.glob(pattern)]

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

        # Cargar SoundFont
        sf_path = os.path.join(CARPETA_SCRIPT, soundfont_name)
        try:
            self._sfid = self._synth.sfload(sf_path)
        except Exception:
            self._midiin.close_port()
            self._synth.delete()
            self._synth = None
            self.connection_changed.emit(False)
            return False

        # Configurar instrumento y volumen inicial
        self._synth.program_select(0, self._sfid, 0, self._current_instrument)
        self._synth.cc(0, 7, self._volume)

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

    # ── Controles ──────────────────────────────────────────────────

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
        """
        Ajusta la curva de velocity.
        exponent < 1.0 → Soft (amplifica toques suaves)
        exponent = 1.0 → Linear (sin cambio)
        exponent > 1.0 → Hard (comprime toques suaves)
        """
        self._velocity_curve = max(0.1, min(3.0, exponent))
        self._persist_config()

    def _apply_velocity_curve(self, velocity: int) -> int:
        """Transforma la velocity cruda según la curva configurada."""
        if self._velocity_curve == 1.0:
            return velocity
        normalized = velocity / 127.0
        adjusted = normalized ** self._velocity_curve
        return max(1, min(127, int(adjusted * 127)))

    # ── Callback MIDI (corre en thread de rtmidi) ─────────────────

    def _midi_callback(self, event, data=None):
        """Procesa mensajes MIDI entrantes. Corre en thread separado."""
        message, _delta = event
        if not message:
            return

        status = message[0] & 0xF0

        if status == NOTE_ON and len(message) >= 3:
            note, vel = message[1], message[2]
            if vel > 0:
                adjusted_vel = self._apply_velocity_curve(vel)
                self._synth.noteon(0, note, adjusted_vel)
                self.note_played.emit(note, adjusted_vel)
            else:
                self._synth.noteoff(0, note)
                self.note_released.emit(note)

        elif status == NOTE_OFF and len(message) >= 3:
            self._synth.noteoff(0, message[1])
            self.note_released.emit(message[1])

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
        _save_config(config)

    # ── Cleanup ────────────────────────────────────────────────────

    def cleanup(self):
        """Libera todos los recursos."""
        self.disconnect()
