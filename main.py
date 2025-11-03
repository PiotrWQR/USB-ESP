import sys
import time
import threading
import json

from datetime import datetime

import serial
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QTimer, QStringListModel, QModelIndex, QPersistentModelIndex
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel,
                             QPushButton, QVBoxLayout, QLineEdit, QHBoxLayout,
                             QDialog, QScrollArea, QListWidget, QListWidgetItem)

request_types = {
    "set_cca": 4,
    "get_cca": 2,
    "set_msg_settings": 5,
    "get_msg_settings": 3,
    "none": 0,
    "get_topology": 1
}
device_types = {
    0: "koordynator",
    1: "router",
    2: "urządzenie brzegowe"
}
relationship_type = {
    0: "rodzic",
    1: "dziecko",
    2: "rodzeństwo",
    3: "żadne",
    4: "poprzednie dziecko",
    5: "nieautoryzowane dziecko"
}
basewidth = 210

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ser = serial.Serial("COM4", 115200, rtscts=False)
        print("0")
        self.setWindowTitle("Ustawienia koordynatora")
        self.layout = QHBoxLayout()

        self.bemin_edit = QLineEdit()
        self.bemax_edit = QLineEdit()
        self.retries_edit = QLineEdit()
        self.device_addr_edit = QLineEdit()
        self.dest_addr_edit = QLineEdit()
        self.delay_edit = QLineEdit()
        self.tx_power_edit = QLineEdit()
        self.payload_size_edit = QLineEdit()

        self.topology_label = QLabel()
        self.nwk_ex_pan_id = QLabel()
        self.nwk_pan_id = QLabel()
        self.nwk_channel = QLabel()
        self.address = QLabel()
        self.nwk_energy_scan = QLabel()
        self.transmission_label = QLabel()
        self.topology_list = QListWidget()
        self.transmission_list = QListWidget()
        self.transmission_list2 = QListWidget()
        self.neighbours_table_list = QListWidget()
        self.routes_table_list = QListWidget()
        self.route_records_table_list = QListWidget()
        
        request = dict()
        request["request_type"] = 5
        request['dest_addr'] = 0
        request['delay_ms'] = 1000
        request['repeats'] = 1
        request['payload_size'] = 20
        request_json = json.dumps(request).encode("utf-8")
        self.ser.write(request_json)
    
        time_now = datetime.now().strftime("%Y%m%d%H%M%S")
        self.f = open("files/route_record" + time_now + ".txt", "x")

        print("0.5")
        # self.attach_cca_layout()
        print("1")
        self.attach_sending_settings_window()
        print("2")
        self.attach_nwk_layout()
        print("3")
        #self.attach_topology()
        print("4")
        self.attach_tables()
        print("5")
        # self.attach_transmission_layout()
        self.attach_transmission_layout2()
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        self.setLayout(self.layout)
        self.show()
        self.update_window()

        self.ieee_list = list()

        self.handle = threading.Thread(target=self.read_and_handle)
        self.handle.start()

    def handle_response(self, json_str):
        json_obj = json.loads(json_str.strip(b'\n'))
        text = json.dumps(json_obj, skipkeys=True, indent=2)
        # print(text)
        # błąd
        if json_obj["information_type"] == 255:
            dlg = QDialog()
            dlg.setWindowTitle("Błąd")
            if json_obj['error_description'] is not None:
                layout = QVBoxLayout()
                layout.addWidget(QLabel(json_obj['error_description']))
                dlg.setLayout(layout)
                print(json_obj['error_description'])
        # toplogy
        elif json_obj["information_type"] == 1:
            #print("topology")
            self.topology_list.clear()
            self.ieee_list = []
            for rd in json_obj:
                if rd == "information_type":
                    continue
                text = ""
                text += "Router: " + rd + '\n'
                self.ieee_list.append("rd")
                obj = json_obj[rd]
                neighbors = obj["neighbors"]
                routes = obj["routes"]
                text += " Sąsiedzi: " + '\n'
                for n in neighbors:
                    text += "  Adres ieee: " + n["ieee_addr"] + '\n'
                    text += "   Adres krótki: " + n["short_addr"] + '\n'
                    text += "   LQI: " + str(n["lqi"]) + '\n'
                    text += "   RSSI: " + str(n["rssi"]) + '\n'
                    text += "   Typ urządzenia : " + device_types[n["device_type"]] + '\n'
                    text += "   Koszt: " + str(n["outgoing_cost"]) + '\n'
                    text += "   Relacja: " + relationship_type[n["relationship"]] + '\n'
                text += " Trasy: \n"
                for r in routes:
                    text += "  Adres docelowy: " + r["dest_addr"] + '\n'
                    text += "   Następny węzeł: " + r["next_hop"] + '\n'
                item = QListWidgetItem(self.topology_list)
                item.setText(text)
        # cca
        elif json_obj['information_type'] == 2:
            #print("ca settings")
            self.bemin_edit.setText(str(json_obj['csma_min_be']))
            self.bemax_edit.setText(str(json_obj['csma_max_be']))
            self.retries_edit.setText(str(json_obj['csma_max_backoffs']))
        # ustawienia wiadomości
        elif json_obj["information_type"] == 3:
            #print("settings")
            self.device_addr_edit.setText("")
            self.dest_addr_edit.setText(str(json_obj['dest_addr_str']))
            self.delay_edit.setText(str(json_obj['delay_ms']))
            self.payload_size_edit.setText(str(json_obj['payload_size']))
            self.tx_power_edit.setText(str(json_obj['tx_power']))
        # tablice
        elif json_obj["information_type"] == 4:
            #print("tables")
            self.neighbours_table_list.clear()
            index = 1
            for neighbour in json_obj["neighbors"]:
                text = "Indeks: " + str(index) + "\n"
                index += 1
                text += " Adres ieee: " + neighbour["ieee_addr"] + "\n"
                text += "   Adres krótki: " + neighbour["short_addr"] + "\n"
                #text += "   Typ urzadzenia: " + device_types[neighbour["device_type"]] + "\n"
                #text += "   Typ relacji: " + relationship_type[neighbour["relationship"]] + "\n"
                text += "   Odległość: " + str(neighbour["depth"]) + "\n"
                text += "   RSSI: " + str(neighbour["rssi"]) + "\n"
                text += "   LQI: " + str(neighbour["lqi"]) + "\n"
                text += "   Koszt: " + str(neighbour["outgoing_cost"]) + "\n"
                item = QListWidgetItem()
                # item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setFlags(item.flags() | Qt.ItemIsSelectable)
                # item.setCheckState(QtCore.Qt.CheckState.Unchecked)
                item.setText(text)
                self.neighbours_table_list.addItem(item)
            self.routes_table_list.clear()
            for route in json_obj['routes']:
                text = "  Adres: " + route["dest_addr"] + "\n"
                text += "  Następny węzeł: " + route['next_hop'] + "\n"
                text += "  Flagi: " + str(route["flags"]) + "\n"
                item = QListWidgetItem(self.routes_table_list)
                item.setText(text)
            self.route_records_table_list.clear()
            for route_record in json_obj["route_records"]:
                text = "  Adres docelowy: " + route_record["dest_addr"] + "\n"
                text += "   Wygaśnięcie: " + str(route_record["expiry"]) + "\n"
                text += "   Ścieżka: " + str(route_record["path"]) + "\n"
                item = QListWidgetItem(self.route_records_table_list)
                item.setText(text)
                self.f.write(text)
        # parametry nwk
        elif json_obj["information_type"] == 5:
            #print("nwk")
            self.nwk_channel.setText("Kanał: " + str(json_obj["channel"]))
            self.nwk_pan_id.setText("Adres PAN: " + str(json_obj["pan_id"]))
            self.nwk_ex_pan_id.setText("Adres rozszerzony: " + str(json_obj["extended_pan_id"]))
        # transmision data
        elif json_obj["information_type"] == 6:
            #print("transmission")
            self.transmission_list.clear()
            for obj in json_obj['arr']:
                text = ""
                text += ("Adres ieee: " + obj["ieee_addr"] + '\n')
                text += (" Krótki adres: " + obj["short_addr"] + '\n')
                text += (" Udane pingi: " + str(obj["successful_pings"]) + '\n')
                text += (" Nieudane pingi: " + str(obj["failed_pings"]) + '\n')
                text += (" Czas rozpoczęcia: " + str(obj["start_time"]) + '\n')
                text += (" Czas zakończenia: " + str(obj["end_time"]) + '\n')
                text += (" Czas trwania: " + str(obj["duration_ms"]) + '\n')
                text += (" Wyznaczone powtórzenia: " + str(obj["repeats"]) + '\n')
                text += (" Wyznaczone opóżnienie: " + str(obj["delay"]) + '\n')
                text += (" Wyznaczony rozmiar: " + str(obj["size"]) + '\n')
                if obj["recon_time"] != 0:
                    text += (" Czas rekonwergencji: " + str(obj["recon_time"]) + '\n\n')
                item = QListWidgetItem(self.transmission_list)
                item.setText(text)
        # skan kanałow
        elif json_obj["information_type"] == 7:
            if "status" in json_obj:
                self.nwk_energy_scan.setText("Wyniki skanu energetycznego: błąd")
                return
            tx = ""
            for value in json_obj["energy_values"]:
                tx += "Kanał " + str(value['channel']) + ": " + str(value['energy_value']) + "\n"
            tx+= "\nWszystkich transmisji: " + str(json_obj["total_transmission"]) + "\n"
            tx+= "Nieudanych transmisji: " + str(json_obj["transmission_failures"]) + "\n"
            self.nwk_energy_scan.setText("Wyniki skanu energetycznego: \n" + tx)
        #dane pojedyńczego pingu
        elif json_obj["information_type"] == 8:
            text = "Numer pingu: " + str(json_obj["ping_num"]) + "\n"
            text += "Indykator od " + hex(json_obj["addr"]) + " numer: " \
                + str(json_obj["seq_num"]) + "\n"
            text += "LQI: " + str(json_obj["lqi"]) + "\n"
            text += "Ścieżka: [" 
            path  = json_obj["path"]
            for addr in path:
                text += hex(addr) + ", "
            text += "]\n"
            # if "route" in json_obj:
            #     text += "Trasa:"+ hex(json_obj["route"])
            text += "\n"
            self.f.write(text)
            item = QListWidgetItem()
            item.setText(text)
            self.transmission_list2.addItem(item)
        else:
            print("informacja z poza zakresu")

    def read_and_handle(self):
        print("6")
        while True:
            try:
                line = self.ser.readline()
                self.handle_response(line)
            except serial.SerialException:
                print("Error in loop")
                self.ser.close()
                self.close()
                return

    def attach_transmission_layout(self):
        layout = QVBoxLayout()
        area = QScrollArea()
        area.setMinimumWidth(220)
        area.setAlignment(Qt.AlignTop)
        header_label = QLabel("Dane transmisji              ")
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(header_label)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidgetResizable(True)
        area.setWidget(self.transmission_list)
        layout.addWidget(area)
        button = QPushButton("Wyczyść tablice transmsji")
        button.clicked.connect(self.clear_transmission)
        layout.addWidget(button)
        self.layout.addLayout(layout)

    def attach_transmission_layout2(self):
        layout = QVBoxLayout()
        area = QScrollArea()
        area.setMinimumWidth(220)
        area.setAlignment(Qt.AlignTop)
        header_label = QLabel("Dane transmisji              ")
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(header_label)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidgetResizable(True)
        area.setWidget(self.transmission_list2)
        layout.addWidget(area)
        button = QPushButton("Wyczyść tablice transmsji i zapisz plik")
        button.clicked.connect(self.reset_transmision_write)
        layout.addWidget(button)
        self.layout.addLayout(layout)

    def attach_nwk_layout(self):
        layout = QVBoxLayout()
        header_label = QLabel("Dane sieci")
        header_label.setFixedWidth(basewidth)
        layout.addWidget(header_label)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.nwk_pan_id)
        layout.addWidget(self.nwk_ex_pan_id)
        layout.addWidget(self.nwk_channel)
        layout.addWidget(self.nwk_energy_scan)
        button1 = QPushButton("Otwórz sieć")
        button1.clicked.connect(self.open_network)
        button2 = QPushButton("Resetuj sieć")
        button2.clicked.connect(self.reset_network)
        layout.addWidget(button1)
        layout.addWidget(button2)
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
        header_label.setFixedWidth(basewidth)
        bemin_label = QLabel("Minimalna ekspotencja odwrotu (min 4)")
        bemax_label = QLabel("Maksymalna ekspotencja odwrotu(max 8)")
        retries_label = QLabel("Maksymalna liczba prób(max 8)")
        layout.addWidget(header_label)
        layout.addWidget(bemin_label)
        layout.addWidget(self.bemin_edit)
        layout.addWidget(bemax_label)
        layout.addWidget(self.bemax_edit)
        layout.addWidget(retries_label)
        layout.addWidget(self.retries_edit)
        cca_button = QPushButton()
        cca_button.setText("Zatwierź nowe parametry")
        self.get_cca_data()
        cca_button.pressed.connect(self.set_cca_data)
        layout.addWidget(cca_button)
        self.layout.addLayout(layout)

    def attach_topology(self):
        area = QScrollArea()
        area.setMinimumWidth(250)
        area.setAlignment(Qt.AlignTop)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        header_label = QLabel("Topologia        ")
        header_label.setAlignment(Qt.AlignTop)
        layout.addWidget(header_label)
        area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidgetResizable(True)
        area.setWidget(self.topology_list)
        layout.addWidget(area)

        self.layout.addLayout(layout)

    def attach_tables(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        self.get_tables()
        header_lable = QLabel("Tablice")
        header_lable.setMinimumWidth(280)
        layout.addWidget(header_lable)
        neighbours_table_label = QLabel("Sąsiedzi koordynatora:")
        routes_table_label = QLabel("Trasy koordynatora:")
        route_record_table_label = QLabel("Trasy MTO koordynatora:")
        layout.addWidget(neighbours_table_label)
        layout.addWidget(self.neighbours_table_list)
        layout.addWidget(routes_table_label)
        layout.addWidget(self.routes_table_list)
        layout.addWidget(route_record_table_label)
        layout.addWidget(self.route_records_table_list)
        button = QPushButton()
        button.setText("Ściągnij aktualne dane")
        button.pressed.connect(self.update_window)
        layout.addWidget(button)
        self.layout.addLayout(layout)

    def attach_sending_settings_window(self):
        layout = QVBoxLayout()
        
        header_label = QLabel("Ustawienia żądań")
        header_label.setFixedWidth(basewidth)
        device_addr_label = QLabel("Adres urządzenia do konfiguracji (szesnastkowy): ")
        dest_addr_label = QLabel("Adres docelowy transmisji (szesnastkowy): ")
        delay_label = QLabel("Przerwa między żądaniami(ms): ")
        payload_size_label = QLabel("Rozmiar ładunk(bajty): ")
        tx_power_label = QLabel("Moc sygnału(dBm): ")
        header_label.setAlignment(Qt.AlignTop)

        layout.setAlignment(Qt.AlignTop)
        button = QPushButton()
        button.setText("Zatwierź nowe parametry")
        button.pressed.connect(self.set_sending_settings)
        layout.addWidget(header_label)
        layout.addWidget(device_addr_label)
        layout.addWidget(self.device_addr_edit)
        layout.addWidget(dest_addr_label)
        layout.addWidget(self.dest_addr_edit)
        layout.addWidget(delay_label)
        layout.addWidget(self.delay_edit)
        layout.addWidget(payload_size_label)
        layout.addWidget(self.payload_size_edit)
        layout.addWidget(tx_power_label)
        layout.addWidget(self.tx_power_edit)
        layout.addWidget(button)

        self.layout.addLayout(layout)

    def update_window(self):
        request = {
            "request_type": 13
        }
        self.ser.write(json.dumps(request).encode("utf-8"))

    def get_cca_data(self):
        request = {
            "request_type": 2
        }
        self.ser.write(json.dumps(request).encode("utf-8"))

    def get_tables(self):
        request = {
            "request_type": 6,
        }
        self.ser.write(json.dumps(request).encode("utf-8"))
        time.sleep(0.1)

    def set_cca_data(self):
        request = dict()
        request['request_type'] = request_types['set_cca']
        request['csma_min_be'] = self.bemin_edit.text()
        request['csma_max_be'] = self.bemax_edit.text()
        request['csma_max_backoffs'] = self.retries_edit.text()
        json_str = json.dumps(request).encode("utf-8")
        if self.ser.writable():
            self.ser.write(json_str)
        self.get_cca_data()

    def set_sending_settings(self):
        request = dict()
        request["request_type"] = 5
        request['device_addr'] = int(self.device_addr_edit.text(), 16)
        request['dest_addr'] = int(self.dest_addr_edit.text(), 16)
        request['delay_ms'] = int(self.delay_edit.text())
        request['payload_size'] = int(self.payload_size_edit.text())
        request['tx_power'] = int(self.tx_power_edit.text())
        request_json = json.dumps(request).encode("utf-8")
        if self.ser.writable():
            self.ser.write(request_json)

    def clear_transmission(self):
        request = {
            "request_type": 9,
        }
        msg = json.dumps(request).encode("utf-8")
        if self.ser.writable():
            self.ser.write(msg)

    def open_network(self):
        request = {
            "request_type": 10,
        }
        msg = json.dumps(request).encode("utf-8")
        if self.ser.writable():
            self.ser.write(msg)

    def reset_network(self):
        request = {
            "request_type": 11,
        }
        msg = json.dumps(request).encode("utf-8")
        if self.ser.writable():
            self.ser.write(msg)

    def get_nwk_data(self):
        request = {
            "request_type": 7
        }
        self.ser.write(json.dumps(request).encode("utf-8"))

    def reset_transmision_write(self):
        self.transmission_list2.clear()
        self.f.close()
        time_now = datetime.now().strftime("%Y%m%d%H%M%S")
        self.f = open("files/route_record" + time_now + ".txt", "x")


app = QApplication(sys.argv)

window = MyMainWindow()
window.show()

app.exec()

window.f.close()
window.ser.close()
