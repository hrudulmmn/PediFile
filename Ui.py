from PyQt6 import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import ctypes
import markdown
import sys,os
import fitz
import render
import summarise

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PediFile.App")

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.doc = None
        main = QWidget()
        self.setCentralWidget(main)
        mainlayout = QVBoxLayout(main)
        self.page=0
        self.zoom=1.5
        
        icpath = self.resource_path("assets\PediFile_logo.png")
        self.setWindowIcon(QIcon(icpath))
        
        #pdf render area
        mainpdf = QWidget()
        lay = QHBoxLayout(mainpdf)
        self.pdf = QLabel()
        self.pdf.setScaledContents(True)
        self.pdf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setContentsMargins(20,20,20,20)
        lay.addWidget(self.pdf,alignment=Qt.AlignmentFlag.AlignCenter)

        #scroll area for pdf renderig
        self.scrll = QScrollArea()
        self.scrll.setWidgetResizable(True)
        self.scrll.setWidget(mainpdf)
        
        #summary panel
        split = QSplitter(Qt.Orientation.Horizontal)

        self.togbtn = QPushButton('>>')
        self.togbtn.setCheckable(True)
        self.togbtn.toggled.connect(self.summary)
        lay.addWidget(self.togbtn,alignment=Qt.AlignmentFlag.AlignRight)
        
        self.sumFrame = QFrame()
        self.sumFrame.setFrameShape(QFrame.Shape.StyledPanel)
        sumlay = QVBoxLayout(self.sumFrame)

        self.sumArea = QTextEdit()
        self.sumArea.setReadOnly(True)
        font = self.sumArea.font()
        font.setPointSize(10)
        self.sumArea.setFont(font)
        sumlay.addWidget(self.sumArea)

        split.addWidget(self.scrll)
        split.addWidget(self.sumFrame)
        split.setSizes([1,0])
        self.split = split

        #Navbar
        navbar = QHBoxLayout()

        opnfile = QPushButton("Open")
        opnfile.clicked.connect(self.opnpdf)
        navbar.addWidget(opnfile)

        pageprev = QPushButton("<")
        navbar.addWidget(pageprev)
        pageprev.clicked.connect(self.toprev)

        pagenxt = QPushButton(">")
        pagenxt.clicked.connect(self.tonxt)
        navbar.addWidget(pagenxt)

        inzoom = QPushButton("+")
        navbar.addWidget(inzoom)
        inzoom.clicked.connect(self.enlarge)

        outzoom = QPushButton("-")
        navbar.addWidget(outzoom)
        outzoom.clicked.connect(self.minimise)

        self.scrll.verticalScrollBar().valueChanged.connect(self.pageScroll)
        navbar.addStretch()
        mainlayout.addLayout(navbar)
        mainlayout.addWidget(self.split)
    
    def opnpdf(self):
        filepath,_ = QFileDialog.getOpenFileName(self,"Select File","","PDF Files (*.pdf);; All Files(*)")
        if filepath:
            try:
                self.page=0
                self.doc = fitz.open(filepath)
            except Exception as e:
                QMessageBox.warning(self,"Error","PDF Load Failed!")
            pixmp = render.render(self.doc,self.page,self.zoom)
            self.pdf.setPixmap(pixmp)
            self.pdf.setFixedSize(pixmp.size())
        
    def tonxt(self):
        if not self.doc:
            return
        total = self.doc.page_count
        if self.page >=total-1:
            return
        if self.page < total-1:
            self.page+=1
            pixmp = render.render(self.doc,self.page,self.zoom)
            if pixmp is None:
                QMessageBox.warning(self,"Error","Unable to Render Page!")
            self.pdf.setPixmap(pixmp)
            self.pdf.setFixedSize(pixmp.size())

            bar = self.scrll.verticalScrollBar()
            bar.blockSignals(True)
            bar.setValue(bar.minimum())
            bar.blockSignals(False)
            self.split.setSizes([1,0])
            self.togbtn.setText(">>")
            self.togbtn.setCheckable(False)
            self.togbtn.setCheckable(True)
    
    def toprev(self):
        if not self.doc:
            return
        total = self.doc.page_count
        if self.page >0:
            self.page-=1
            pixmp = render.render(self.doc,self.page,self.zoom)
        else:
            return
        if pixmp is None:
                QMessageBox.warning(self,"Error","Unable to Render Page!")
        self.pdf.setPixmap(pixmp)
        self.pdf.setFixedSize(pixmp.size())

        bar = self.scrll.verticalScrollBar()
        bar.blockSignals(True)
        bar.setValue(bar.maximum())
        bar.blockSignals(False)
        self.split.setSizes([1,0])
        self.togbtn.setText(">>")
        self.togbtn.setCheckable(False)
        self.togbtn.setCheckable(True)
        

    def enlarge(self):
        if not self.doc:
            return
        self.zoom*= 1.25
        pixmp = render.render(self.doc,self.page,self.zoom)
        self.pdf.setPixmap(pixmp)
        self.pdf.setFixedSize(pixmp.size())
    
    def minimise(self):
        if not self.doc:
            return
        self.zoom/=1.25
        pixmp = render.render(self.doc,self.page,self.zoom)
        self.pdf.setPixmap(pixmp)
        self.pdf.setFixedSize(pixmp.size())

    def pageScroll(self,value):
        if not self.doc:
            return
        bar = self.scrll.verticalScrollBar()
        min = bar.minimum()
        max = bar.maximum()

        if value==max:
            self.tonxt()
        if value==min:
            self.toprev()
           
    def summary(self,state):
        if not self.doc:
            return
        curPage = self.doc.load_page(self.page)
        content = curPage.get_text('text')
        self.pageSum = summarise.pagesummarise(self.doc,self.page,content)
        html = markdown.markdown(self.pageSum)


        if state==True:
            self.split.setSizes([600,200])
            self.togbtn.setText("<<")
            self.sumArea.setText(html)
        
        if state==False:
            self.split.setSizes([1,0])
            self.togbtn.setText(">>")

            
    def resource_path(self, relative_path):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)



app = QApplication(sys.argv)
window = Window()
window.setWindowTitle("PediFile")
window.resize(1000,750)
window.show()
sys.exit(app.exec())