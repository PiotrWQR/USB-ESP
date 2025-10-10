import sys
import time
import threading
import json
import serial
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel,
                             QPushButton, QVBoxLayout, QLineEdit,  QHBoxLayout,
                             QDialog)
# dostęp do com musi być zarzadzany asynchronicznie

request_types = {
    "set_cca": 4,
    "get_cca": 2,
    "set_msg_settings": 5,
    "get_msg_settings": 3,
    "none": 0,
    "get_topology": 1
}

device_types = {
    0: "coordinator",
    1: "router",
    2: "end device"
}
relationship_type = {
    0: "partner",
    1: "child",
    2: "sibling",
    3: "none ",
    4: "previous child",
    5: "unauthenticated child"
}


class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)


class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ser = serial.Serial("COM24", 115200, rtscts=False)
        print("0")
        self.setWindowTitle("Ustawienia koordynatora")
        self.layout = QHBoxLayout()

        self.bemin_edit = QLineEdit()
        self.bemax_edit = QLineEdit()
        self.retries_edit = QLineEdit()
        self.repeats_edit = QLineEdit()
        self.dest_addr_edit = QLineEdit()
        self.delay_edit = QLineEdit()
        self.payload_size_edit = QLineEdit()
        self.tables_label = QLabel()
        self.topology_label = QLabel()
        self.nwk_panid = QLabel()
        self.nwk_channel = QLabel()
        self.adres = QLabel()
        self.transmion_start = QLabel()
        self.transmion_end = QLabel()
        self.transmion_duration_time = QLabel()
        print("0.5")
        self.attach_cca_layout()
        print("1")
        self.attach_sending_settings_window()
        print("2")
        self.show_tables()
        print("3")
        self.attach_topology()
        print("4")
        self.attach_nwk_layout()
        print("5")
        self.attach_transmission_layout()
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        self.setLayout(self.layout)
        self.show()
        self.update_topology_tables()

        handle = threading.Thread(target=self.read_and_handle)
        handle.start()

    def attach_transmission_layout(self):
        layout = QVBoxLayout()
        header_label = QLabel("Dane transmisji")
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(header_label)
        layout.addWidget(self.adres)
        layout.addWidget(self.transmion_start)
        layout.addWidget(self.transmion_end)
        layout.addWidget(self.transmion_duration_time)
        self.get_nwk_data()
        self.layout.addLayout(layout)

    def read_and_handle(self):
        while True:
            line = self.ser.readline()
            self.handle_response(line)

    def attach_nwk_layout(self):
        layout = QVBoxLayout()
        header_label = QLabel("Dane sieci")
        layout.addWidget(header_label)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.nwk_panid)
        layout.addWidget(self.nwk_channel)
        self.get_nwk_data()
        self.layout.addLayout(layout)

    def show_error_window(self, text):
        self.setWindowTitle("Bład")
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)
        self.show()

    def attach_cca_layout(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        header_label = QLabel("Ustawienia CA/CSMA")
        bemin_label = QLabel("Minimalna ekspotencja odwrotu")
        bemax_label = QLabel("Maksymalna ekspotencja odwrotu(max ")
        retries_label = QLabel("Maksymalna liczba prób(maks 8)")

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
        self.get_topology()
        cca_button.setText("Zatwierź nowe parametry")
        cca_button.pressed.connect(self.set_cca_data)
        layout.addWidget(cca_button)
        self.layout.addLayout(layout)

    def show_tables(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.get_tables()
        header_lable = QLabel("Tablice")
        layout.addWidget(header_lable)
        layout.addWidget(self.tables_label)
        button = QPushButton()
        button.setText("Ściągnij aktualne dane")
        button.pressed.connect(self.update_topology_tables)
        layout.addWidget(button)
        self.layout.addLayout(layout)

    def update_topology_tables(self):
        self.get_msg_settings()
        time.sleep(0.1)
        self.get_tables()
        time.sleep(0.1)
        self.get_topology()
        time.sleep(0.1)
        self.get_nwk_data()
        time.sleep(0.1)
        self.get_transmision_data()


    def attach_sending_settings_window(self):
        layout = QVBoxLayout()
        header_label = QLabel("Ustawienia żądań")
        repeats_label = QLabel("Powtórzenia")
        dest_addr_label = QLabel("Adres docelowy (szesnastkowy)")
        delay_label = QLabel("Przerwa między żądaniami(ms)")
        payload_size_label = QLabel("Rozmiar ładunku")
        header_label.setAlignment(Qt.AlignTop)
        layout.setAlignment(Qt.AlignTop)
        button = QPushButton()
        button.setText("Zatwierź nowe parametry")
        layout.addWidget(header_label)
        layout.addWidget(repeats_label)
        layout.addWidget(self.repeats_edit)
        layout.addWidget(dest_addr_label)
        layout.addWidget(self.dest_addr_edit)
        layout.addWidget(delay_label)
        layout.addWidget(self.delay_edit)
        layout.addWidget(payload_size_label)
        layout.addWidget(self.payload_size_edit)
        layout.addWidget(button)
        self.layout.addLayout(layout)

    def get_nwk_data(self):
        request = {
            "request_type":7
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        time.sleep(0.1)

    def get_cca_data(self):
        request = {
            "request_type": 2
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        time.sleep(0.2)

    def get_msg_settings(self):
        time.sleep(0.05)
        request = {
            "request_type": 3
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        time.sleep(0.05)

    def get_tables(self):
        request = {
            "request_type": 6,
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        time.sleep(0.1)

    def get_transmision_data(self):
        request = {
            "request_type": 8,
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        time.sleep(0.2)

    def get_topology(self):
        request = {
            "request_type": 1,
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        time.sleep(0.2)

    def set_cca_data(self):
        request = dict()
        request['request_type'] = request_types['set_cca']
        request['csma_min_be'] = self.bemin_edit.text()
        request['csma_max_be'] = self.bemax_edit.text()
        request['csma_max_backoffs'] = self.retries_edit.text()
        json_str = json.dumps(request).encode("utf-8")
        self.ser.write(json_str)
        self.get_cca_data()

    def attach_topology(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        header_label = QLabel("Topologia")
        header_label.setAlignment(Qt.AlignTop)
        layout.addWidget(header_label)
        layout.addWidget(self.topology_label)
        self.layout.addLayout(layout)

    def set_sending_settings(self):
        request = dict()
        request["request_type"] = 5
        request['dest_addr'] = int(self.dest_addr_edit.text(), 16)
        request['delay_ms'] = int(self.delay_edit.text())
        request['repeats'] = int(self.repeats_edit.text())
        request['payload_size'] = int(self.payload_size_edit.text())
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
        elif json_obj["information_type"] == 1:
            text = json.dumps(json_obj, skipkeys=True, indent=2)
            container = QVBoxLayout()
            for router in json_obj:
                if router == "information_type":
                    continue
                container.addWidget(QLabel(router))
                sub_container = QVBoxLayout()
                sub_container.addWidget(QLabel(json_obj[router]))
                sub_container.addWidget(QLabel(json_obj[router]))
            self.layout.addLayout(container)
        elif json_obj['information_type'] == 2:
            self.bemin_edit.setText(str(json_obj['csma_min_be']))
            self.bemax_edit.setText(str(json_obj['csma_max_be']))
            self.retries_edit.setText(str(json_obj['csma_max_backoffs']))
        elif json_obj["information_type"] == 3:
            self.repeats_edit.setText(str(json_obj['repeats']))
            self.dest_addr_edit.setText(str(json_obj['dest_addr_str']))
            self.delay_edit.setText(str(json_obj['delay_ms']))
            self.payload_size_edit.setText(str(json_obj['payload_size']))
        elif json_obj["information_type"] == 4:
            text = "Dane sąsiadów koordynatora:\n"
            for neighbour in json_obj["neighbors"]:
                text += " Adres ieee: " + neighbour["ieee_addr"] + "\n"
                text += "   Adres krótki: " + neighbour["short_addr"] + "\n"
                text += "   Typ urzadzenia: " + device_types[neighbour["device_type"]] + "\n"
                text += "   Typ relacji: " + str(neighbour["relationship"]) + "\n"
                text += "   RSSI: " + str(neighbour["rssi"]) + "\n"
                text += "   LQI: " + str(neighbour["lqi"]) + "\n"
                text += "   Koszt: " + str(neighbour["outgoing_cost"]) + "\n"
            text += "Dane tras koordynatora\n"
            for route in json_obj['routes']:
                text += "  Adres: " + route["dest_addr"] + "\n"
                text += "  Następny węzeł: " + route['next_hop'] + "\n"
            self.tables_label.setText(text)
        elif json_obj["information_type"] == 5:
            self.nwk_panid.setText("Adres rozszerzony: " + str(json_obj["extended_pan_id"]))
            self.nwk_channel.setText("Kanał: " + str(json_obj["channel"]))
        elif json_obj["information_type"] == 6:
            self.adres.setText("Adres: " + str(json_obj["short_addr"]))
            self.transmion_start.setText("Czas rozpoczęcia: " + str(json_obj["start_time"]))
            self.transmion_end.setText("Czas zakończenia: " + str(json_obj["end_time"]))
            self.transmion_start.setText("Czas trwania: " + str(json_obj["duration_ms"]))
        else:
            print("informacja z poza zakresu")


app = QApplication(sys.argv)

window = MyMainWindow()
window.show()

app.exec()
