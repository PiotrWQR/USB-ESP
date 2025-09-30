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


class CCASettings:
    def __init__(self):
        self.MinBackoffExp = 0
        self.MaxBackoffExp = 0
        self.MaxBackoffRetries = 0

    def get_settings(self):
        self.MinBackoffExp = 3

    def set_settings(self):
        self.MinBackoffExp = 0


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
        self.port = "COM19"

        # esptool.main()
        # esp = esptool.ESPLoader('COM19')
        # print(esp)
        # esptool.run(esp)
        # esptool.read_mac(esp)
        # return

        try:
            ser = serial.Serial(self.port, 115200, timeout=0,
                                parity=serial.PARITY_EVEN, rtscts=False,
                                stopbits=1)
        except serial.SerialException:
            self.show_error_window("Nie udało się znaleźć portu")
            return
        except:
            self.show_error_window("Wystąpił błąd: \n" + str(NameError))
            return
        sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))


        try:
            while True:
                if ser.in_waiting:
                    #data = sio.readline().
                    data = sio.readline().encode(encoding='utf-8', errors='ignore').strip()
                    print(f"Odebrano: {data}")
        except KeyboardInterrupt:
            print("Zakończono odbiór.")
        finally:
            ser.close()

        self.setWindowTitle("Ustawienia koordynatora")
        self.layout = QHBoxLayout()
        self.attach_cca_layout()

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


app = QApplication(sys.argv)

window = MyMainWindow()
window.show()

app.exec()
