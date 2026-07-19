# NEXO MIDI Synth — ROADMAP DE EXPANSIÓN Y FUTURAS NOCIONES

Documento de visión técnica y arquitectura futura para **NEXO MIDI Synth**.

---

## 🗺️ Visión General

Transformar `nexo-midi-synth` de un módulo de sonido virtual básico a una estación de trabajo de síntesis por software soberana, portátil y extensible para controladores MIDI de 49 teclas (Samson Carbon 49).

---

## 📌 Hitos y Módulos de Expansión

### 1. 🎛️ Procesamiento de Audio & Efectos Avanzados
- [ ] **Presets de Reverb Acústicos**: Selección de espacios modelados (`Concert Hall`, `Small Room`, `Plate`, `Cathedral`, `Church`) mediante ajuste fino de `roomsize`, `damping` y `width` en FluidSynth.
- [ ] **Módulo de Delay / Echo Digital**:
  - Parámetros: *Delay Time* (ms), *Feedback* (%), *Dry/Wet* (%).
  - Modo Sincronizado por Tempo (BPM) y Tap Tempo.
- [ ] **Master Equalizer & Filter**:
  - EQ de 3/5 bandas (Bass, Mid, Treble).
  - Filtro Pasa-Bajos (*Low-Pass Cutoff*) con resonancia (*Resonance*) dinámicos.

### 2. 🎹 Capas e Instrumentos Múltiples (Layering & Splits)
- [ ] **Dual Layering**: Tocar 2 instrumentos en simultáneo en el mismo canal (ej. *Acoustic Piano + Warm Synth Pad*).
- [ ] **Keyboard Split**: Dividir las 49 teclas del teclado en 2 zonas con diferentes instrumentos (ej. *Bass* en octavas agudas/graves y *Piano* en el resto).

### 3. ⏱️ Rítmica & Arpegiador por Software
- [ ] **Arpegiador Programable**:
  - Modos: Up, Down, Up/Down, Random, Latch.
  - Tempo asignable en BPM con multiplicadores de división rítmica (1/4, 1/8, 1/16, Tripletas).

### 4. 🎚️ Soporte Multi-SoundFont & Mezclador
- [ ] **Mezclador de SoundFonts**: Cargar múltiples bancos `.sf2` de alta calidad simultáneamente para asignar libremente a cada capa o canal.

### 5. 🔴 Grabador MIDI & Captura Audio
- [ ] **Grabación MIDI en Vivo**: Grabar interpretaciones y exportar archivos `.mid`.
- [ ] **Render de Audio WAV**: Exportar la interpretación a audio `.wav` nativo de 24-bit / 44.1kHz.

---

## 🛠️ Deuda Técnica & Optimización de Empaquetado
- [ ] Incorporar ícono soberano `.ico` al ejecutable compilado por PyInstaller.
- [ ] Soporte para drivers de baja latencia WASAPI / ASIO4ALL en Windows.

---

*Registrado el 2026-07-19 en el Terroir de Marcelo y NEXO.*
