"""
Ventana principal de NEXO MIDI Synth.
Diseño por pestañas (QTabWidget) DAW-style con distribución limpia y sin solapamientos.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QComboBox, QListWidget, QListWidgetItem,
    QSlider, QLabel, QPushButton, QProgressBar,
    QStatusBar, QFrame, QSizePolicy, QMenu, QTabWidget,
    QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

from core.engine import MidiEngine
from core.instruments import (
    GM_INSTRUMENTS, GM_CATEGORIES,
    get_instruments_by_category, midi_note_to_name
)


class MainWindow(QMainWindow):
    """Ventana principal del módulo de sonido MIDI virtual."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("♪ NEXO MIDI Synth")
        self.setMinimumSize(520, 680)
        self.resize(560, 720)

        # Motor MIDI
        self.engine = MidiEngine(self)

        # Timer para decay de la actividad visual
        self._activity_timer = QTimer(self)
        self._activity_timer.setSingleShot(True)
        self._activity_timer.timeout.connect(self._clear_activity)

        # Construir UI
        self._build_ui()
        self._connect_signals()
        self._populate_devices()

        # Restaurar estado inicial de interfaz y presets
        self._restore_instrument_selection()
        self._update_favorites_buttons()

        # Status bar
        self.statusBar().showMessage("NEXO MIDI Synth v1.2.0 — Listo")

    # ── Construcción de UI ─────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(14, 12, 14, 12)

        # Título + Botón de Pánico
        title_layout = QHBoxLayout()
        title = QLabel("♪ NEXO MIDI Synth")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Módulo de sonido virtual GM")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_layout.addStretch()

        self.panic_btn = QPushButton("🚨 PÁNICO")
        self.panic_btn.setObjectName("disconnectBtn")
        self.panic_btn.setToolTip("Corta todas las notas resonando inmediatamente (All Notes Off)")
        title_layout.addWidget(self.panic_btn)

        main_layout.addLayout(title_layout)

        # Separador
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(sep)

        # Panel de conexión (Fijo arriba)
        main_layout.addWidget(self._build_connection_panel())

        # Contenedor Pestañas (TabWidget) para distribución holgada
        self.tabs = QTabWidget()
        
        # Pestaña 1: Instrumentos & Presets
        self.tabs.addTab(self._build_instrument_tab(), "🎹 Instrumentos & Presets")
        
        # Pestaña 2: Controles & Efectos
        self.tabs.addTab(self._build_controls_tab(), "🎛️ Controles & Efectos")
        
        # Pestaña 3: Transposición & Octavas
        self.tabs.addTab(self._build_transpose_tab(), "🎼 Pitch & Octavas")

        main_layout.addWidget(self.tabs, stretch=1)

        # Panel de actividad (Fijo abajo)
        main_layout.addWidget(self._build_activity_panel())

    def _build_connection_panel(self) -> QGroupBox:
        group = QGroupBox("CONEXIÓN")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        # Fila 1: Dispositivo MIDI & SoundFont en paralelo
        dev_row = QHBoxLayout()
        
        dev_row.addWidget(QLabel("🎹 MIDI:"))
        self.midi_combo = QComboBox()
        self.midi_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        dev_row.addWidget(self.midi_combo)

        dev_row.addWidget(QLabel("🔊 SoundFont:"))
        self.sf_combo = QComboBox()
        self.sf_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        dev_row.addWidget(self.sf_combo)

        layout.addLayout(dev_row)

        # Fila 2: Estado + Botones de acción
        status_row = QHBoxLayout()
        self.status_label = QLabel("● Desconectado")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("color: #e74c3c;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        self.refresh_btn = QPushButton("⟳ Buscar")
        self.refresh_btn.setToolTip("Buscar dispositivos MIDI y SoundFonts")
        status_row.addWidget(self.refresh_btn)

        self.connect_btn = QPushButton("Conectar")
        status_row.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.setObjectName("disconnectBtn")
        self.disconnect_btn.setVisible(False)
        status_row.addWidget(self.disconnect_btn)

        layout.addLayout(status_row)

        return group

    def _build_instrument_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Fila: Presets Favoritos (P1 a P6)
        fav_box = QGroupBox("FAVORITOS (Clic: Cargar | Clic Derecho: Guardar)")
        fav_layout = QHBoxLayout(fav_box)
        fav_layout.setSpacing(4)
        
        self.fav_buttons = []
        for i in range(6):
            btn = QPushButton(f"P{i+1}")
            btn.setProperty("slot_idx", i)
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(self._on_fav_context_menu)
            fav_layout.addWidget(btn)
            self.fav_buttons.append(btn)
        layout.addWidget(fav_box)

        # Selector de Categoría
        cat_row = QHBoxLayout()
        cat_row.addWidget(QLabel("Categoría GM:"))
        self.category_combo = QComboBox()
        self.category_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for cat_name, _, _ in GM_CATEGORIES:
            self.category_combo.addItem(cat_name)
        cat_row.addWidget(self.category_combo)
        layout.addLayout(cat_row)

        # Lista de instrumentos (espaciosa)
        self.instrument_list = QListWidget()
        self.instrument_list.setMinimumHeight(160)
        layout.addWidget(self.instrument_list, stretch=1)

        # Label del instrumento seleccionado
        self.selected_label = QLabel("")
        self.selected_label.setObjectName("curveLabel")
        self.selected_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.selected_label)

        return tab

    def _build_controls_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Grupo: Volumen & Velocity Curve
        dyn_group = QGroupBox("DINÁMICA & EXPRESIÓN")
        dyn_layout = QVBoxLayout(dyn_group)
        dyn_layout.setSpacing(10)

        # Volumen
        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Volumen Maestro"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 127)
        self.volume_slider.setValue(self.engine.volume)
        vol_row.addWidget(self.volume_slider)
        self.volume_value = QLabel(str(self.engine.volume))
        self.volume_value.setObjectName("sliderValue")
        vol_row.addWidget(self.volume_value)
        dyn_layout.addLayout(vol_row)

        # Velocity Curve
        curve_row = QHBoxLayout()
        curve_row.addWidget(QLabel("Curva Velocity"))
        self.curve_slider = QSlider(Qt.Orientation.Horizontal)
        self.curve_slider.setObjectName("velocityCurveSlider")
        self.curve_slider.setRange(10, 300)  # 0.1 a 3.0 (x100)
        self.curve_slider.setValue(int(self.engine.velocity_curve * 100))
        curve_row.addWidget(self.curve_slider)
        self.curve_value = QLabel(f"{self.engine.velocity_curve:.1f}")
        self.curve_value.setObjectName("sliderValue")
        curve_row.addWidget(self.curve_value)
        dyn_layout.addLayout(curve_row)

        # Label descriptivo de la curva
        self.curve_desc = QLabel(self._curve_description(self.engine.velocity_curve))
        self.curve_desc.setObjectName("curveLabel")
        self.curve_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dyn_layout.addWidget(self.curve_desc)

        layout.addWidget(dyn_group)

        # Grupo: Efectos (Reverb & Chorus)
        fx_group = QGroupBox("EFECTOS DE AUDIO")
        fx_layout = QVBoxLayout(fx_group)
        fx_layout.setSpacing(10)

        # Reverb
        rev_row = QHBoxLayout()
        rev_row.addWidget(QLabel("Reverb"))
        self.reverb_slider = QSlider(Qt.Orientation.Horizontal)
        self.reverb_slider.setRange(0, 100)
        self.reverb_slider.setValue(int(self.engine.reverb_level * 100))
        rev_row.addWidget(self.reverb_slider)
        self.reverb_value = QLabel(f"{int(self.engine.reverb_level * 100)}%")
        self.reverb_value.setObjectName("sliderValue")
        rev_row.addWidget(self.reverb_value)
        fx_layout.addLayout(rev_row)

        # Chorus
        cho_row = QHBoxLayout()
        cho_row.addWidget(QLabel("Chorus"))
        self.chorus_slider = QSlider(Qt.Orientation.Horizontal)
        self.chorus_slider.setRange(0, 100)
        self.chorus_slider.setValue(int(self.engine.chorus_level * 100))
        cho_row.addWidget(self.chorus_slider)
        self.chorus_value = QLabel(f"{int(self.engine.chorus_level * 100)}%")
        self.chorus_value.setObjectName("sliderValue")
        cho_row.addWidget(self.chorus_value)
        fx_layout.addLayout(cho_row)

        layout.addWidget(fx_group)
        layout.addStretch()

        return tab

    def _build_transpose_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(12, 12, 12, 12)

        # Octavas
        oct_group = QGroupBox("DESPLAZAMIENTO DE OCTAVA (-3 a +3)")
        oct_layout = QHBoxLayout(oct_group)
        self.oct_down_btn = QPushButton("◀ -1 Octava")
        self.oct_val_label = QLabel("0")
        self.oct_val_label.setObjectName("noteDisplay")
        self.oct_val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.oct_up_btn = QPushButton("+1 Octava ▶")

        oct_layout.addWidget(self.oct_down_btn)
        oct_layout.addWidget(self.oct_val_label, stretch=1)
        oct_layout.addWidget(self.oct_up_btn)
        layout.addWidget(oct_group)

        # Transposición (Semitonos)
        trans_group = QGroupBox("TRANSPOSICIÓN POR SEMITONOS (-12 a +12)")
        trans_layout = QHBoxLayout(trans_group)
        self.trans_down_btn = QPushButton("◀ -1 Semitono")
        self.trans_val_label = QLabel("0")
        self.trans_val_label.setObjectName("noteDisplay")
        self.trans_val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trans_up_btn = QPushButton("+1 Semitono ▶")

        trans_layout.addWidget(self.trans_down_btn)
        trans_layout.addWidget(self.trans_val_label, stretch=1)
        trans_layout.addWidget(self.trans_up_btn)
        layout.addWidget(trans_group)

        # Botón de Reset
        reset_row = QHBoxLayout()
        reset_row.addStretch()
        self.reset_pitch_btn = QPushButton("🔄 Restablecer Afinación (0)")
        self.reset_pitch_btn.setMinimumWidth(200)
        reset_row.addWidget(self.reset_pitch_btn)
        reset_row.addStretch()
        layout.addLayout(reset_row)

        layout.addStretch()

        return tab

    def _build_activity_panel(self) -> QGroupBox:
        group = QGroupBox("ACTIVIDAD")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)

        activity_row = QHBoxLayout()

        # Nota
        note_col = QVBoxLayout()
        note_label = QLabel("Nota Actual")
        note_label.setObjectName("subtitleLabel")
        note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note_col.addWidget(note_label)
        self.note_display = QLabel("—")
        self.note_display.setObjectName("noteDisplay")
        note_col.addWidget(self.note_display)
        activity_row.addLayout(note_col)

        # Separador vertical
        vsep = QFrame()
        vsep.setFrameShape(QFrame.Shape.VLine)
        vsep.setStyleSheet("background-color: #2a2a4a;")
        activity_row.addWidget(vsep)

        # Velocity
        vel_col = QVBoxLayout()
        vel_label = QLabel("Velocity Meter")
        vel_label.setObjectName("subtitleLabel")
        vel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vel_col.addWidget(vel_label)

        vel_display_row = QHBoxLayout()
        self.velocity_bar = QProgressBar()
        self.velocity_bar.setRange(0, 127)
        self.velocity_bar.setValue(0)
        vel_display_row.addWidget(self.velocity_bar)
        self.velocity_value = QLabel("0")
        self.velocity_value.setObjectName("velocityValue")
        vel_display_row.addWidget(self.velocity_value)

        vel_col.addLayout(vel_display_row)
        activity_row.addLayout(vel_col, stretch=2)

        layout.addLayout(activity_row)

        return group

    # ── Señales y Slots ────────────────────────────────────────────

    def _connect_signals(self):
        # Botones de Acción
        self.panic_btn.clicked.connect(self.engine.panic)
        self.connect_btn.clicked.connect(self._on_connect)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        self.refresh_btn.clicked.connect(self._populate_devices)

        # Presets Favoritos
        for btn in self.fav_buttons:
            btn.clicked.connect(self._on_fav_clicked)

        # Instrumentos
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        self.instrument_list.currentRowChanged.connect(self._on_instrument_selected)

        # Transposición
        self.oct_down_btn.clicked.connect(lambda: self._adjust_octave(-1))
        self.oct_up_btn.clicked.connect(lambda: self._adjust_octave(1))
        self.trans_down_btn.clicked.connect(lambda: self._adjust_transpose(-1))
        self.trans_up_btn.clicked.connect(lambda: self._adjust_transpose(1))
        self.reset_pitch_btn.clicked.connect(self._reset_pitch)

        # Controles
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.curve_slider.valueChanged.connect(self._on_curve_changed)
        self.reverb_slider.valueChanged.connect(self._on_reverb_changed)
        self.chorus_slider.valueChanged.connect(self._on_chorus_changed)

        # Engine
        self.engine.note_played.connect(self._on_note_played)
        self.engine.note_released.connect(self._on_note_released)
        self.engine.instrument_changed.connect(self._on_instrument_changed_external)
        self.engine.connection_changed.connect(self._on_connection_changed)
        self.engine.favorites_changed.connect(self._update_favorites_buttons)

    # ── Slots: Favoritos / Presets ─────────────────────────────────

    def _update_favorites_buttons(self, favs=None):
        favorites = favs if favs is not None else self.engine.favorites
        for i, btn in enumerate(self.fav_buttons):
            if i < len(favorites):
                prog = favorites[i]
                name = GM_INSTRUMENTS[prog]
                short_name = f"P{i+1}: {name[:8]}.." if len(name) > 8 else f"P{i+1}: {name}"
                btn.setText(short_name)
                btn.setToolTip(f"[{prog}] {name}\nClic: Seleccionar\nClic derecho: Reemplazar por instrumento actual")

    def _on_fav_clicked(self):
        btn = self.sender()
        if not btn:
            return
        idx = btn.property("slot_idx")
        favorites = self.engine.favorites
        if 0 <= idx < len(favorites):
            prog = favorites[idx]
            self.engine.set_instrument(prog)
            self._restore_instrument_selection()

    def _on_fav_context_menu(self, pos):
        btn = self.sender()
        if not btn:
            return
        idx = btn.property("slot_idx")
        current_prog = self.engine.current_instrument
        current_name = GM_INSTRUMENTS[current_prog]

        menu = QMenu(self)
        save_action = QAction(f"Guardar [{current_prog}] {current_name} en P{idx+1}", self)
        save_action.triggered.connect(lambda: self.engine.set_favorite(idx, current_prog))
        menu.addAction(save_action)
        menu.exec(btn.mapToGlobal(pos))

    # ── Slots: Transposición ───────────────────────────────────────

    def _adjust_octave(self, delta: int):
        new_oct = max(-3, min(3, self.engine.octave + delta))
        self.engine.set_octave(new_oct)
        self.oct_val_label.setText(f"{new_oct:+d}" if new_oct != 0 else "0")

    def _adjust_transpose(self, delta: int):
        new_trans = max(-12, min(12, self.engine.transpose + delta))
        self.engine.set_transpose(new_trans)
        self.trans_val_label.setText(f"{new_trans:+d}" if new_trans != 0 else "0")

    def _reset_pitch(self):
        self.engine.set_octave(0)
        self.engine.set_transpose(0)
        self.oct_val_label.setText("0")
        self.trans_val_label.setText("0")

    # ── Slots: Conexión ────────────────────────────────────────────

    def _populate_devices(self):
        self.midi_combo.clear()
        ports = self.engine.get_midi_ports()
        if ports:
            for p in ports:
                self.midi_combo.addItem(p)
        else:
            self.midi_combo.addItem("(No se detectaron dispositivos)")

        self.sf_combo.clear()
        soundfonts = self.engine.get_available_soundfonts()
        if soundfonts:
            for sf in soundfonts:
                self.sf_combo.addItem(sf)
        else:
            self.sf_combo.addItem("(No se encontraron archivos .sf2)")

    def _on_connect(self):
        port_idx = self.midi_combo.currentIndex()
        sf_name = self.sf_combo.currentText()

        if port_idx < 0 or sf_name.startswith("("):
            self.statusBar().showMessage("Error: seleccioná un dispositivo MIDI y un SoundFont")
            return

        self.connect_btn.setEnabled(False)
        self.statusBar().showMessage("Conectando...")

        success = self.engine.connect(port_idx, sf_name)
        if success:
            self.statusBar().showMessage(f"Conectado a {self.midi_combo.currentText()}")
        else:
            self.connect_btn.setEnabled(True)
            self.statusBar().showMessage("Error al conectar — verificá dispositivo y SoundFont")

    def _on_disconnect(self):
        self.engine.disconnect()
        self.statusBar().showMessage("Desconectado")

    def _on_connection_changed(self, connected: bool):
        self.connect_btn.setVisible(not connected)
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setVisible(connected)
        self.midi_combo.setEnabled(not connected)
        self.sf_combo.setEnabled(not connected)
        self.refresh_btn.setEnabled(not connected)

        if connected:
            self.status_label.setText("● Conectado")
            self.status_label.setStyleSheet("color: #00e676;")
        else:
            self.status_label.setText("● Desconectado")
            self.status_label.setStyleSheet("color: #e74c3c;")

    # ── Slots: Instrumentos ────────────────────────────────────────

    def _on_category_changed(self, index: int):
        if index < 0:
            return
        cat_name = GM_CATEGORIES[index][0]
        instruments = get_instruments_by_category(cat_name)

        self.instrument_list.blockSignals(True)
        self.instrument_list.clear()
        for prog, name in instruments:
            item = QListWidgetItem(f"{prog:3d}  {name}")
            item.setData(Qt.ItemDataRole.UserRole, prog)
            self.instrument_list.addItem(item)

            if prog == self.engine.current_instrument:
                self.instrument_list.setCurrentItem(item)
        self.instrument_list.blockSignals(False)

    def _on_instrument_selected(self, row: int):
        if row < 0:
            return
        item = self.instrument_list.item(row)
        if item is None:
            return
        prog = item.data(Qt.ItemDataRole.UserRole)
        self.engine.set_instrument(prog)
        self.selected_label.setText(f"► [{prog}] {GM_INSTRUMENTS[prog]}")
        self.statusBar().showMessage(f"Instrumento: [{prog}] {GM_INSTRUMENTS[prog]}")

    def _on_instrument_changed_external(self, program: int):
        for i, (_, start, end) in enumerate(GM_CATEGORIES):
            if start <= program <= end:
                self.category_combo.blockSignals(True)
                self.category_combo.setCurrentIndex(i)
                self.category_combo.blockSignals(False)
                self._on_category_changed(i)

                for row in range(self.instrument_list.count()):
                    item = self.instrument_list.item(row)
                    if item and item.data(Qt.ItemDataRole.UserRole) == program:
                        self.instrument_list.blockSignals(True)
                        self.instrument_list.setCurrentItem(item)
                        self.instrument_list.blockSignals(False)
                        break
                break

        self.selected_label.setText(f"► [{program}] {GM_INSTRUMENTS[program]}")

    def _restore_instrument_selection(self):
        prog = self.engine.current_instrument
        for i, (_, start, end) in enumerate(GM_CATEGORIES):
            if start <= prog <= end:
                self.category_combo.setCurrentIndex(i)
                break
        self.selected_label.setText(f"► [{prog}] {GM_INSTRUMENTS[prog]}")

    # ── Slots: Controles ───────────────────────────────────────────

    def _on_volume_changed(self, value: int):
        self.engine.set_volume(value)
        self.volume_value.setText(str(value))

    def _on_curve_changed(self, value: int):
        exponent = value / 100.0
        self.engine.set_velocity_curve(exponent)
        self.curve_value.setText(f"{exponent:.1f}")
        self.curve_desc.setText(self._curve_description(exponent))

    def _on_reverb_changed(self, value: int):
        level = value / 100.0
        self.engine.set_reverb_level(level)
        self.reverb_value.setText(f"{value}%")

    def _on_chorus_changed(self, value: int):
        level = value / 100.0
        self.engine.set_chorus_level(level)
        self.chorus_value.setText(f"{value}%")

    @staticmethod
    def _curve_description(exponent: float) -> str:
        if exponent < 0.7:
            return "🟢 Muy Soft — ideal para toques suaves"
        elif exponent < 1.0:
            return "🟢 Soft — amplifica toques suaves"
        elif exponent == 1.0:
            return "⚪ Linear — sin transformación"
        elif exponent < 1.5:
            return "🟡 Firm — comprime toques suaves"
        else:
            return "🔴 Hard — toques suaves requieren más fuerza"

    # ── Slots: Actividad ───────────────────────────────────────────

    def _on_note_played(self, note: int, velocity: int):
        name = midi_note_to_name(note)
        self.note_display.setText(name)
        self.velocity_bar.setValue(velocity)
        self.velocity_value.setText(str(velocity))
        self._activity_timer.start(2000)

    def _on_note_released(self, note: int):
        pass

    def _clear_activity(self):
        self.note_display.setText("—")
        self.velocity_bar.setValue(0)
        self.velocity_value.setText("0")

    # ── Cleanup ────────────────────────────────────────────────────

    def closeEvent(self, event):
        self.engine.cleanup()
        super().closeEvent(event)
