import sys
from PyQt6.QtWidgets import QApplication
from Ui import Window

app = QApplication(sys.argv)
with open("Design.qss","r") as style:
            app.setStyleSheet(style.read())
window = Window()
window.setWindowTitle("PediFile")
window.resize(1000,750)
window.show()
window.checkstate()

sys.exit(app.exec())