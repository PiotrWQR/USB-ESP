import sys
import io
import serial
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel,
                             QPushButton, QVBoxLayout, QLineEdit, QAction,
                             QMenu, QHBoxLayout, QLayout)
from _queue import SimpleQueue
# dostęp do com musi być zarzadzany asynchronicznie
#
import esptool


class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)


def clicked():
    print("clicked")


class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ustawienia koordynatora")
        self.layout = QHBoxLayout()
        self.attach_cca_layout()
        self.attach_sending_settings_window()
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        self.setLayout(self.layout)
        self.show()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, pos):
        context = QMenu(self)
        context.addAction(QAction("test 1", self))
        context.addAction(QAction("test 2", self))
        context.exec(self.mapToGlobal(pos))

    def show_error_window(self, text):
        self.setWindowTitle("Bład")
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)
        self.show()

    def attach_cca_layout(self):
        layout = QVBoxLayout()
        header_label = QLabel("Ustawienia CA/CSMA")
        bemin_label = QLabel("Minimalna ekspotencja odwrotu")
        bemax_label = QLabel("Maksymalna ekspotencja odwrotu")
        retries_label = QLabel("Maksymalna liczba prób")
        bemin_edit = QLineEdit()
        bemax_edit = QLineEdit()
        retries_edit = QLineEdit()
        cca_button = QPushButton()
        cca_button.setText("Zatwierź nowe parametry")
        layout.addWidget(bemin_label)
        layout.addWidget(bemin_edit)
        layout.addWidget(bemax_label)
        layout.addWidget(bemax_edit)
        layout.addWidget(retries_label)
        layout.addWidget(retries_edit)
        layout.addWidget(cca_button)

        self.layout.addLayout(layout)

    def attach_sending_settings_window(self):
        layout = QVBoxLayout()
        header_label = QLabel("Ustawienia żądań")
        repeats_label = QLabel("Powtórzenia")
        dest_addr_label = QLabel("Adres docelowy (szesnastkowy)")
        delay_label = QLabel("Przerwa między żądaniami")
        repeats_edit = QLineEdit()
        dest_addr_edit = QLineEdit()
        delay_edit = QLineEdit()
        button = QPushButton()
        button.setText("Zatwierź nowe parametry")
        layout.addWidget(header_label)
        layout.addWidget(repeats_label)
        layout.addWidget(repeats_edit)
        layout.addWidget(dest_addr_label)
        layout.addWidget(dest_addr_edit)
        layout.addWidget(delay_label)
        layout.addWidget(delay_edit)
        layout.addWidget(button)
        self.layout.addLayout(layout)

    def attach_topology_window(self):
        layout = QVBoxLayout()
        header_label = QLabel("Topologia")
        neightbours_label = QLabel("Sąsiedzi")


        self.layout.addLayout(layout)


app = QApplication(sys.argv)

window = MyMainWindow()
window.show()

app.exec()
