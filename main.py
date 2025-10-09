import sys
import json
import io
import serial
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel,
                             QPushButton, QVBoxLayout, QLineEdit, QAction,
                             QMenu, QHBoxLayout, QLayout, QDialog)
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

        self.bemin_edit = QLineEdit()
        self.bemax_edit = QLineEdit()
        self.retries_edit = QLineEdit()
        self.repeats_edit = QLineEdit()
        self.dest_addr_edit = QLineEdit()
        self.delay_edit = QLineEdit()
        self.tables_label = QLabel()
        self.topology_label = QLabel()

        self.attach_cca_layout()
        self.attach_sending_settings_window()
        self.show_tables()
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        self.setLayout(self.layout)
        self.show()
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.on_context_menu)
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

        layout.addWidget(header_label)
        layout.addWidget(bemin_label)
        layout.addWidget(self.bemin_edit)
        layout.addWidget(bemax_label)
        layout.addWidget(self.bemax_edit)
        layout.addWidget(retries_label)
        layout.addWidget(self.retries_edit)
        cca_button = QPushButton()
        self.get_cca_data()
        self.get_msg_settings()
        cca_button.setText("Zatwierź nowe parametry")
        cca_button.pressed.connect(self.set_cca_data)
        layout.addWidget(cca_button)
        self.layout.addLayout(layout)

    def show_tables(self):
        layout = QVBoxLayout()
        self.get_tables()
        header_lable = QLabel("Tablice")
        layout.addWidget(header_lable)
        layout.addWidget(self.tables_label)
        self.layout.addLayout(layout)

    def attach_sending_settings_window(self):
        layout = QVBoxLayout()
        header_label = QLabel("Ustawienia żądań")
        repeats_label = QLabel("Powtórzenia")
        dest_addr_label = QLabel("Adres docelowy (szesnastkowy)")
        delay_label = QLabel("Przerwa między żądaniami")

        button = QPushButton()
        button.setText("Zatwierź nowe parametry")
        layout.addWidget(header_label)
        layout.addWidget(repeats_label)
        layout.addWidget(self.repeats_edit)
        layout.addWidget(dest_addr_label)
        layout.addWidget(self.dest_addr_edit)
        layout.addWidget(delay_label)
        layout.addWidget(self.delay_edit)
        layout.addWidget(button)
        self.layout.addLayout(layout)

    def get_cca_data(self):
        request = {
            "request_type": 2
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        json_str = self.ser.readline()
        self.handle_response(json_str)

    def get_msg_settings(self):
        request = {
            "request_type": 3
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        json_str = self.ser.readline()
        self.handle_response(json_str)

    def get_tables(self):
        request = {
            "request_type": 6,
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        json_str = self.ser.readline()
        self.handle_response(json_str)

    def set_cca_data(self):
        request = dict()
        request['request_type'] = request_types['set_cca']
        request['csma_min_be'] = self.bemin_edit.text()
        request['csma_max_be'] = self.bemax_edit.text()
        request['csma_max_backoffs'] = self.retries_edit.text()
        json_str = json.dumps(request).encode("utf-8")
        self.ser.write(json_str+b"\n")
        self.get_cca_data()

    def attach_topology_window(self):
        layout = QVBoxLayout()
        header_label = QLabel("Topologia")


        self.layout.addLayout(layout)

    def set_sending_settings(self):
        request = dict()
        request["request_type"] = 5
        request['dest_addr'] = self.dest_addr_edit.text()
        request['delay_ms'] = self.delay_edit.text()
        request['repeats'] = self.repeats_edit.text()
        request_json = json.dumps(request).encode("utf-8")
        self.ser.write(request_json)
        response = self.ser.readline()
        self.handle_response(response)

    def handle_response(self, json_str):
        json_obj = json.loads(json_str.strip(b'\n'))
        if json_obj["information_type"] == 255:
            dlg = QDialog(self)
            dlg.setWindowTitle("Błąd")
            if json_obj['error_description'] is not None:
                layout = QVBoxLayout()
                layout.addWidget(QLabel(json_obj['error_description']))
                dlg.setLayout(layout)
            dlg.exec()
        elif json_obj['information_type'] == 2:
            self.bemin_edit.setText(str(json_obj['csma_min_be']))
            self.bemax_edit.setText(str(json_obj['csma_max_be']))
            self.retries_edit.setText(str(json_obj['csma_max_backoffs']))
        elif json_obj["information_type"] == 3:
            self.repeats_edit.setText(str(json_obj['repeats']))
            self.dest_addr_edit.setText(str(json_obj['dest_addr']))
            self.delay_edit.setText(str(json_obj['delay_ms']))
        elif json_obj["information_type"] == 1:
            print("tu bedzie topologia")
        elif json_obj["information_type"] == 4:
            text = "Dane sąsiadów koordynatora:\n"
            for neighbour in json_obj["neighbors"]:
                text += " Adres ieee: " + neighbour["ieee_addr"] + "\n"
                text += "   Adres krótki: " + neighbour["short_addr"] + "\n"
                text += "   Typ urzadzenia: " + str(neighbour["device_type"]) + "\n"
                text += "   Typ relacji: " + str(neighbour["relationship"]) + "\n"
                text += "   RSSI: " + str(neighbour["rssi"]) + "\n"
                text += "   LQI: " + str(neighbour["lqi"]) + "\n"
                text += "   Koszt: " + str(neighbour["outgoing_cost"]) + "\n"
            text += "Dane tras koordynatora\n"
            for route in json_obj['routes']:
                text += "  Adres: " + route["dest_addr"] + "\n"
                text += "  Następny węzeł: " + route['next_hop'] + "\n"
            self.tables_label.setText(text)
        else:
            print("informacja z poza zakresu")


app = QApplication(sys.argv)

window = MyMainWindow()
window.show()

app.exec()
