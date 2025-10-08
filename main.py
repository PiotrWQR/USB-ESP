import sys
import json
import io
import serial
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel,
                             QPushButton, QVBoxLayout, QLineEdit, QAction,
                             QMenu, QHBoxLayout, QLayout)
import json
from _queue import SimpleQueue
# dostęp do com musi być zarzadzany asynchronicznie
#
import esptool
request_types = {
    "set_cca": 4,
    "get_cca": 2,
    "set_msg_settings": 5,
    "get_msg_settings": 3,
    "none": 0,
    "get_topology": 1
}


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

        self.ser = serial.Serial("COM24", 115200, rtscts=False)

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
        self.bemin_edit = QLineEdit()
        self.bemax_edit = QLineEdit()
        self.retries_edit = QLineEdit()
        cca_button = QPushButton()
        cca_button.setText("Zatwierź nowe parametry")
        cca_button.pressed.connect(self.get_cca_data)
        self.get_cca_data()
        layout.addWidget(bemin_label)
        layout.addWidget(self.bemin_edit)
        layout.addWidget(bemax_label)
        layout.addWidget(self.bemax_edit)
        layout.addWidget(retries_label)
        layout.addWidget(self.retries_edit)
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

    def get_cca_data(self):
        request = {
            "request_type": 2
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        json_str = self.ser.readline().strip(b'\n')
        json_obj = json.loads(json_str)
        if json_obj['information_type'] == 2:
            self.bemin_edit.setText(str(json_obj['csma_min_be']))
            self.bemax_edit.setText(str(json_obj['csma_max_be']))
            self.retries_edit.setText(str(json_obj['csma_max_backoffs']))

    def set_cca_data(self):
        # błąd metody
        print("set_cca_data start")
        request = dict()
        request['request_type'] = request_types['set_cca']
        request['csma_min_be'] = self.bemin_edit.text()
        request['csma_max_be'] = self.bemax_edit.text()
        request['csma_max_backoffs'] = self.retries_edit.rext()
        json_str = json.dumps(request).encode("utf-8")
        self.ser.write(json_str)
        self.get_cca_data()
    def attach_topology_window(self):
        layout = QVBoxLayout()
        header_label = QLabel("Topologia")
        neightbours_label = QLabel("Sąsiedzi")

        self.layout.addLayout(layout)


app = QApplication(sys.argv)

window = MyMainWindow()
window.show()

app.exec()
