"""
Ventana principal de NEXO MIDI Synth.
Layout DAW-style con paneles de conexión, instrumentos, controles y actividad.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QComboBox, QListWidget, QListWidgetItem,
    QSlider, QLabel, QPushButton, QProgressBar,
    QStatusBar, QFrame, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

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
        self.setMinimumSize(480, 700)
        self.resize(520, 760)

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

        # Restaurar estado del instrumento
        self._restore_instrument_selection()

        # Status bar
        self.statusBar().showMessage("NEXO MIDI Synth v1.0.0 — Listo")

    # ── Construcción de UI ─────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # Título
        title_layout = QHBoxLayout()
        title = QLabel("♪ NEXO MIDI Synth")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Módulo de sonido virtual GM")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)

        # Separador
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Panel de conexión
        layout.addWidget(self._build_connection_panel())

        # Panel de instrumentos
        layout.addWidget(self._build_instrument_panel())

        # Panel de controles
        layout.addWidget(self._build_controls_panel())

        # Panel de actividad
        layout.addWidget(self._build_activity_panel())

    def _build_connection_panel(self) -> QGroupBox:
        group = QGroupBox("CONEXIÓN")

        layout = QVBoxLayout(group)

        # Fila: Dispositivo MIDI
        midi_row = QHBoxLayout()
        midi_row.addWidget(QLabel("🎹 Dispositivo MIDI"))
        self.midi_combo = QComboBox()
        self.midi_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        midi_row.addWidget(self.midi_combo)
        layout.addLayout(midi_row)

        # Fila: SoundFont
        sf_row = QHBoxLayout()
        sf_row.addWidget(QLabel("🔊 SoundFont"))
        self.sf_combo = QComboBox()
        self.sf_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sf_row.addWidget(self.sf_combo)
        layout.addLayout(sf_row)

        # Fila: Estado + Botones
        status_row = QHBoxLayout()
        self.status_label = QLabel("● Desconectado")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("color: #e74c3c;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedWidth(36)
        self.refresh_btn.setToolTip("Actualizar dispositivos")
        status_row.addWidget(self.refresh_btn)

        self.connect_btn = QPushButton("Conectar")
        status_row.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.setObjectName("disconnectBtn")
        self.disconnect_btn.setVisible(False)
        status_row.addWidget(self.disconnect_btn)

        layout.addLayout(status_row)

        return group

    def _build_instrument_panel(self) -> QGroupBox:
        group = QGroupBox("INSTRUMENTO")

        layout = QVBoxLayout(group)

        # Fila: Categoría
        cat_row = QHBoxLayout()
        cat_row.addWidget(QLabel("Categoría"))
        self.category_combo = QComboBox()
        self.category_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for cat_name, _, _ in GM_CATEGORIES:
            self.category_combo.addItem(cat_name)
        cat_row.addWidget(self.category_combo)
        layout.addLayout(cat_row)

        # Lista de instrumentos
        self.instrument_list = QListWidget()
        self.instrument_list.setMinimumHeight(140)
        layout.addWidget(self.instrument_list)

        # Label del instrumento seleccionado
        self.selected_label = QLabel("")
        self.selected_label.setObjectName("curveLabel")
        self.selected_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.selected_label)

        return group

    def _build_controls_panel(self) -> QGroupBox:
        group = QGroupBox("CONTROLES")
        layout = QVBoxLayout(group)

        # Volumen
        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Volumen"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 127)
        self.volume_slider.setValue(self.engine.volume)
        vol_row.addWidget(self.volume_slider)
        self.volume_value = QLabel(str(self.engine.volume))
        self.volume_value.setObjectName("sliderValue")
        vol_row.addWidget(self.volume_value)
        layout.addLayout(vol_row)

        # Velocity Curve
        curve_row = QHBoxLayout()
        curve_row.addWidget(QLabel("Vel. Curve"))
        self.curve_slider = QSlider(Qt.Orientation.Horizontal)
        self.curve_slider.setObjectName("velocityCurveSlider")
        self.curve_slider.setRange(10, 300)  # 0.1 a 3.0 (x100)
        self.curve_slider.setValue(int(self.engine.velocity_curve * 100))
        curve_row.addWidget(self.curve_slider)
        self.curve_value = QLabel(f"{self.engine.velocity_curve:.1f}")
        self.curve_value.setObjectName("sliderValue")
        curve_row.addWidget(self.curve_value)
        layout.addLayout(curve_row)

        # Label descriptivo de la curva
        self.curve_desc = QLabel(self._curve_description(self.engine.velocity_curve))
        self.curve_desc.setObjectName("curveLabel")
        self.curve_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.curve_desc)

        return group

    def _build_activity_panel(self) -> QGroupBox:
        group = QGroupBox("ACTIVIDAD")
        layout = QVBoxLayout(group)

        # Fila: Nota + Velocity
        activity_row = QHBoxLayout()

        # Nota
        note_col = QVBoxLayout()
        note_label = QLabel("Nota")
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
        vel_label = QLabel("Velocity")
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
        # Botones
        self.connect_btn.clicked.connect(self._on_connect)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        self.refresh_btn.clicked.connect(self._populate_devices)

        # Instrumentos
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        self.instrument_list.currentRowChanged.connect(self._on_instrument_selected)

        # Controles
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.curve_slider.valueChanged.connect(self._on_curve_changed)

        # Engine
        self.engine.note_played.connect(self._on_note_played)
        self.engine.note_released.connect(self._on_note_released)
        self.engine.instrument_changed.connect(self._on_instrument_changed_external)
        self.engine.connection_changed.connect(self._on_connection_changed)

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

            # Marcar el instrumento activo
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
        """Cuando el instrumento cambia desde el teclado MIDI (Program Change)."""
        # Actualizar categoría y selección
        for i, (_, start, end) in enumerate(GM_CATEGORIES):
            if start <= program <= end:
                self.category_combo.blockSignals(True)
                self.category_combo.setCurrentIndex(i)
                self.category_combo.blockSignals(False)
                self._on_category_changed(i)

                # Seleccionar el instrumento en la lista
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
        """Restaura la selección visual del instrumento guardado."""
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

        # Reiniciar timer de decay
        self._activity_timer.start(2000)

    def _on_note_released(self, note: int):
        pass  # No limpiamos inmediatamente — el timer se encarga

    def _clear_activity(self):
        self.note_display.setText("—")
        self.velocity_bar.setValue(0)
        self.velocity_value.setText("0")

    # ── Cleanup ────────────────────────────────────────────────────

    def closeEvent(self, event):
        self.engine.cleanup()
        super().closeEvent(event)
