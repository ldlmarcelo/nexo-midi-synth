"""
Dark theme QSS para NEXO MIDI Synth.
Estética DAW profesional con acentos en azul eléctrico.
"""

DARK_THEME = """
/* ── Base ─────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

/* ── Grupos ───────────────────────────────────── */
QGroupBox {
    background-color: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    font-size: 12px;
    color: #8892b0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #8892b0;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── Labels ───────────────────────────────────── */
QLabel {
    color: #ccd6f6;
    background: transparent;
}

QLabel#statusLabel {
    font-weight: bold;
    font-size: 13px;
}

QLabel#noteDisplay {
    font-size: 36px;
    font-weight: bold;
    color: #0ff0fc;
    font-family: "Consolas", "Courier New", monospace;
    qproperty-alignment: AlignCenter;
}

QLabel#velocityValue {
    font-size: 20px;
    font-weight: bold;
    color: #0f9deb;
    font-family: "Consolas", "Courier New", monospace;
}

QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #ccd6f6;
    padding: 4px 0px;
}

QLabel#subtitleLabel {
    font-size: 11px;
    color: #5a6785;
}

QLabel#sliderValue {
    font-size: 12px;
    font-weight: bold;
    color: #0f9deb;
    font-family: "Consolas", "Courier New", monospace;
    min-width: 36px;
}

QLabel#curveLabel {
    font-size: 11px;
    color: #6c5ce7;
    font-style: italic;
}

/* ── Combos ───────────────────────────────────── */
QComboBox {
    background-color: #0a0a1a;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    padding: 6px 12px;
    color: #ccd6f6;
    min-height: 28px;
}

QComboBox:hover {
    border-color: #0f9deb;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8892b0;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #0a0a1a;
    border: 1px solid #2a2a4a;
    color: #ccd6f6;
    selection-background-color: #0f9deb;
    selection-color: #ffffff;
    outline: none;
}

/* ── Lista de instrumentos ────────────────────── */
QListWidget {
    background-color: #0a0a1a;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    color: #ccd6f6;
    outline: none;
    padding: 4px;
}

QListWidget::item {
    padding: 6px 10px;
    border-radius: 4px;
    margin: 1px 2px;
}

QListWidget::item:selected {
    background-color: #0f9deb;
    color: #ffffff;
    font-weight: bold;
}

QListWidget::item:hover:!selected {
    background-color: #1e2d4a;
}

/* ── Sliders ──────────────────────────────────── */
QSlider::groove:horizontal {
    background: #0a0a1a;
    height: 8px;
    border-radius: 4px;
    border: 1px solid #2a2a4a;
}

QSlider::handle:horizontal {
    background: #0f9deb;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
    border: 2px solid #16213e;
}

QSlider::handle:horizontal:hover {
    background: #3db8f5;
    border: 2px solid #0f9deb;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6c5ce7, stop:1 #0f9deb);
    border-radius: 4px;
}

/* ── Velocity Curve Slider (acento púrpura) ───── */
QSlider#velocityCurveSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0f9deb, stop:1 #6c5ce7);
}

QSlider#velocityCurveSlider::handle:horizontal {
    background: #6c5ce7;
}

QSlider#velocityCurveSlider::handle:horizontal:hover {
    background: #8b7cf7;
    border: 2px solid #6c5ce7;
}

/* ── Botones ──────────────────────────────────── */
QPushButton {
    background-color: #0f9deb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
    font-size: 13px;
    min-height: 32px;
}

QPushButton:hover {
    background-color: #3db8f5;
}

QPushButton:pressed {
    background-color: #0a7bc4;
}

QPushButton:disabled {
    background-color: #2a2a4a;
    color: #5a6785;
}

QPushButton#disconnectBtn {
    background-color: #e74c3c;
}

QPushButton#disconnectBtn:hover {
    background-color: #ff6b5b;
}

/* ── Progress Bar (velocity meter) ────────────── */
QProgressBar {
    background-color: #0a0a1a;
    border: 1px solid #2a2a4a;
    border-radius: 4px;
    text-align: center;
    color: transparent;
    min-height: 16px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0f9deb, stop:0.7 #6c5ce7, stop:1 #e74c3c);
    border-radius: 3px;
}

/* ── Scrollbars ───────────────────────────────── */
QScrollBar:vertical {
    background: #0a0a1a;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #2a2a4a;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #3a3a5a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── Separator ────────────────────────────────── */
QFrame#separator {
    background-color: #2a2a4a;
    max-height: 1px;
}

/* ── Status Bar ───────────────────────────────── */
QStatusBar {
    background-color: #0a0a1a;
    color: #5a6785;
    font-size: 11px;
    border-top: 1px solid #2a2a4a;
}
"""
