"""
Punto de entrada principal para la aplicación GUI de NEXO MIDI Synth (PySide6).
"""

import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Asegurar que el directorio raíz esté en el PYTHONPATH
CARPETA_RAIZ = os.path.dirname(os.path.abspath(__file__))
if CARPETA_RAIZ not in sys.path:
    sys.path.insert(0, CARPETA_RAIZ)

from gui.main_window import MainWindow
from gui.theme import DARK_THEME


def main():
    # Habilitar High DPI Scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("NEXO MIDI Synth")
    app.setOrganizationName("NEXO")

    # Aplicar Dark Theme QSS
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
