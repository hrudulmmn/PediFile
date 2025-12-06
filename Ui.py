from PyQt6 import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt,QTimer
from PyQt6.QtGui import QIcon
import ctypes
import markdown
import sys,os
import fitz
import render
import summarise
from gesture import GestureMan

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PediFile.App")

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.doc = None
        main = QWidget()
        self.setCentralWidget(main)
        mainlayout = QVBoxLayout(main)
        self.page=0
        self.zoom=1.2
        self.control = GestureMan()

        icpath = self.resource_path("assets\PediFile_logo.png")
        self.setWindowIcon(QIcon(icpath))
        
        #pdf render area
        mainpdf = QWidget()
        mainpdf.setObjectName("pdf")
        lay = QHBoxLayout(mainpdf)
        self.pdf = QLabel()
        self.pdf.setVisible(False)
        self.pdf.setScaledContents(True)
        self.pdf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setContentsMargins(50,20,50,20)
        lay.addWidget(self.pdf,alignment=Qt.AlignmentFlag.AlignCenter)

        #scroll area for pdf renderig
        self.scrll = QScrollArea()
        self.scrll.setWidgetResizable(True)
        self.scrll.setWidget(mainpdf)
        
        #summary panel
        split = QSplitter(Qt.Orientation.Horizontal)

        self.togbtn = QPushButton('')
        self.togbtn.setIcon(QIcon("assets/sum.svg"))
        self.togbtn.setObjectName("Sumbtn")
        self.togbtn.setVisible(False)
        self.togbtn.clicked.connect(self.summary)
        self.togbtn.setParent(mainpdf)
        self.togbtn.setFixedSize(32,48)
        
        self.sumFrame = QFrame()
        self.sumFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.sumFrame.setObjectName("frame")
        close = QPushButton("")
        close.setIcon(QIcon("assets/close.svg"))
        close.setObjectName("close")
        close.setFixedSize(20,20)
        close.clicked.connect(self.close)
        sumlay = QVBoxLayout(self.sumFrame)
        sumlay.addWidget(close,alignment=Qt.AlignmentFlag.AlignRight)

        self.sumArea = QTextEdit()
        self.sumArea.setReadOnly(True)
        font = self.sumArea.font()
        font.setPointSize(10)
        self.sumArea.setFont(font)
        self.sumArea.setObjectName("Area")
        sumlay.addWidget(self.sumArea)

        split.addWidget(self.scrll)
        split.addWidget(self.sumFrame)
        split.setSizes([1,0])
        self.split = split

        #Navbar
        nav = QWidget()
        navbar = QHBoxLayout(nav)
        navbar.setContentsMargins(0,0,0,0)
        navbar.setSpacing(30)
        nav.setObjectName("navbar")
        opnfile = QPushButton("")
        opnfile.setIcon(QIcon("assets/open.svg"))
        opnfile.setProperty("class","tools")
        opnfile.clicked.connect(self.opnpdf)
        navbar.addWidget(opnfile)

        pageprev = QPushButton("")
        pageprev.setIcon(QIcon("assets/prev.svg"))
        pageprev.setProperty("class","tools")
        navbar.addWidget(pageprev)
        pageprev.clicked.connect(self.toprev)

        pagenxt = QPushButton("")
        pagenxt.setIcon(QIcon("assets/next.svg"))
        pagenxt.setProperty("class","tools")
        pagenxt.clicked.connect(self.tonxt)
        navbar.addWidget(pagenxt)

        inzoom = QPushButton("")
        inzoom.setIcon(QIcon("assets/inzoom.svg"))
        inzoom.setProperty("class","tools")
        navbar.addWidget(inzoom)
        inzoom.clicked.connect(self.enlarge)

        outzoom = QPushButton("")
        outzoom.setIcon(QIcon("assets/outzoom.svg"))
        outzoom.setProperty("class","tools")
        navbar.addWidget(outzoom)
        outzoom.clicked.connect(self.minimise)

        self.mode = QPushButton("")
        self.mode.setCheckable(True)
        self.mode.setIcon(QIcon("assets/mouse.svg"))
        self.mode.setProperty("class","tools")
        self.mode.toggled.connect(self.startGest)
        navbar.addWidget(self.mode,Qt.AlignmentFlag.AlignRight)

        self.scrll.verticalScrollBar().valueChanged.connect(self.pageScroll)
        navbar.addStretch()
        mainlayout.addWidget(nav)
        mainlayout.addWidget(self.split)

        self.control.man.nextPage.connect(self.tonxt)
        self.control.man.prevPage.connect(self.toprev)
    
    def opnpdf(self):
        filepath,_ = QFileDialog.getOpenFileName(self,"Select File","","PDF Files (*.pdf);; All Files(*)")
        if filepath:
            try:
                self.page=0
                self.doc = fitz.open(filepath)
            except Exception as e:
                QMessageBox.warning(self,"Error","PDF Load Failed!")
            pixmp = render.render(self.doc,self.page,self.zoom)
            self.pdf.setVisible(True)
            self.togbtn.setVisible(True)
            self.pdf.setPixmap(pixmp)
            self.pdf.setFixedSize(pixmp.size())
            self.toggle()
        
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
            self.togbtn.setIcon(QIcon("assets/sum.svg"))
            self.togbtn.setCheckable(False)
            self.togbtn.setCheckable(True)
            self.toggle()
    
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
        self.togbtn.setIcon(QIcon("assets/sum.svg"))
        self.toggle()
        

    def enlarge(self):
        if not self.doc:
            return
        self.zoom*= 1.25
        pixmp = render.render(self.doc,self.page,self.zoom)
        self.pdf.setPixmap(pixmp)
        self.pdf.setFixedSize(pixmp.size())
        self.toggle()
        
    
    def minimise(self):
        if not self.doc:
            return
        self.zoom/=1.25
        pixmp = render.render(self.doc,self.page,self.zoom)
        self.pdf.setPixmap(pixmp)
        self.pdf.setFixedSize(pixmp.size())
        self.toggle()
        

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
           
    def summary(self):
        if not self.doc:
            return
        curPage = self.doc.load_page(self.page)
        content = curPage.get_text('text')
        self.pageSum = summarise.pagesummarise(self.doc,self.page,content)
        html = markdown.markdown(self.pageSum)
        self.split.setSizes([600,200])
        self.sumArea.setText(html)
    
    def close(self):
        if not self.doc:
            return
        self.split.setSizes([1,0])

            
    
    def resource_path(self, relative_path):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    
    def toggle(self):
        if self.pdf.height()==0 or self.pdf.width()==0:
            return
        rect=self.pdf.geometry()
        x = rect.right()
        y = rect.top() + rect.height()//2-self.togbtn.height()//2
        self.togbtn.move(x,y)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.toggle()

    def startGest(self,state):
        if state == True:
            self.mode.setIcon(QIcon("assets/hand.svg"))
            self.control.start()
        if state == False:
            self.control.stop()
            self.mode.setIcon(QIcon("assets/mouse.svg"))

