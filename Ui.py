from PyQt6 import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt,QTimer,QEvent
import webbrowser
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
        self.mainpdf = QWidget()
        self.mainpdf.setObjectName("pdf")
        lay = QHBoxLayout(self.mainpdf)
        self.pdf = QLabel()
        self.pdf.setVisible(False)
        self.pdf.setScaledContents(True)
        self.pdf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf.installEventFilter(self)
        lay.setContentsMargins(50,20,50,20)
        lay.addWidget(self.pdf,alignment=Qt.AlignmentFlag.AlignCenter)

        #scroll area for pdf renderig
        self.scrll = QScrollArea()
        self.scrll.setWidgetResizable(True)
        self.scrll.setWidget(self.mainpdf)
        
        #summary panel
        split = QSplitter(Qt.Orientation.Horizontal)

        self.togbtn = QPushButton('')
        self.togbtn.setIcon(QIcon("assets/sum.svg"))
        self.togbtn.setObjectName("Sumbtn")
        self.togbtn.setVisible(False)
        self.togbtn.clicked.connect(self.summary)
        self.togbtn.setParent(self.mainpdf)
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

        self.coffee = QPushButton()
        self.coffee.setIcon(QIcon("assets/cof.svg"))
        self.coffee.setObjectName("cofee")
        self.coffee.setFixedSize(45,45)
        self.coffee.clicked.connect(self.opnlink)
        self.coffee.setParent(self)
        self.coffee.move(self.width()-60,self.height()-60)
        self.coffee.raise_()
        self.coffee.show()

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
        self.control.man.takt.connect(self.gestSum)
        self.control.man.zoom.connect(self.gestZoom)
        
    
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
        self.toggle2()
        
    
    def minimise(self):
        if not self.doc:
            return
        self.zoom/=1.25
        pixmp = render.render(self.doc,self.page,self.zoom)
        self.pdf.setPixmap(pixmp)
        self.pdf.setFixedSize(pixmp.size())
        self.toggle2()
        

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
    
    def toggle2(self):
        QTimer.singleShot(0,self.toggle)

    def toggle(self):
        if not self.doc and self.pdf.isVisible():
            return
        rect=self.pdf.geometry()
        x = rect.right()
        y = rect.center().y()-self.togbtn.height()//2
        self.togbtn.move(x,y)
        self.togbtn.raise_()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.toggle()
        self.coffee.move(self.width()-60,self.height()-60)

    def checkstate(self):
        if self.control.man.active==True:
            self.mode.setIcon(QIcon("assets/hand.svg"))
        else:
            self.mode.setIcon(QIcon("assets/mouse.svg"))


    def startGest(self,state):
        if state == True or self.control.man.active==True:
            self.mode.setIcon(QIcon("assets/hand.svg"))
            self.control.start()
        if state == False or not self.control.man.active:
            self.control.stop()
            self.mode.setIcon(QIcon("assets/mouse.svg"))

    def gestSum(self,enbled:bool):
        if enbled==True:
            self.summary()
        else:
            self.close()

    def gestZoom(self,state:int):
        maxzoom = 3.0
        minzoom = 0.03
        if state==1 and self.zoom<=maxzoom:
            self.enlarge()
        if state==-1 and self.zoom>=minzoom:
            self.minimise()

    def eventFilter(self,obj,event):
        if obj is self.mainpdf and event.type()==QEvent.Type.Wheel:
            if not self.doc:
                return True
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier():
                delta = event.angleDelta().y()
                if delta>0:
                    self.enlarge()
                else:
                    self.minimise()
                return True
            
            return False
                
        return super().eventFilter(obj,event)
    
    def opnlink(self):
        webbrowser.open("https://buymeacoffee.com/_hrudu_lmmn_")
    