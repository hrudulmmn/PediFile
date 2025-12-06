import cv2
import mediapipe as mp
import math 
from PyQt6.QtCore import pyqtSignal,QObject,QThread
import time

class Gesture(QObject):
    nextPage = pyqtSignal()
    prevPage = pyqtSignal()
    takt = pyqtSignal()
    zoom = pyqtSignal(int)
    def __init__(self, parent =None):
        super().__init__(parent)
        self.hands = mp.solutions.hands
        self.draw = mp.solutions.drawing_utils
        self.running =True
        self.enabled = True

        self.befNextActive = False
        self.befPrevActive = False
        self.befTaktActive = False

        self.nextTime = 0.0
        self.prevTime = 0.0
        self.taktTime = 0.0
        self.cooldown = 700
        self.lastpinch=0


    def run(self):
        capture = cv2.VideoCapture(0)
        hand = self.hands.Hands(
                    static_image_mode = False,
                    max_num_hands = 1,
                    min_detection_confidence = 0.5,
                    min_tracking_confidence = 0.5
                )
        
        try:
            while self.running:
                ret,frame = capture.read()
                if not ret:
                    break

                self.time = time.time()*1000
                rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

                result = hand.process(rgb)
                if result.multi_hand_landmarks:
                    for landmarks in result.multi_hand_landmarks:
                        self.draw.draw_landmarks(
                            frame,
                            landmarks,
                            self.hands.HAND_CONNECTIONS
                        )
                        
                        norm = []
                        wristx = landmarks.landmark[0].x
                        wristy = landmarks.landmark[0].y
                        for point in landmarks.landmark:
                            
                            x = point.x - wristx
                            y = point.y - wristy
                            norm.append((x,y))
                        
                        def fingUp(norm,tip,pip):
                            return norm[tip][1]<norm[pip][1]
                        
                        thumb = fingUp(norm,4,2)
                        index = fingUp(norm,8,6)
                        middle = fingUp(norm,12,10)
                        ring = fingUp(norm,16,14)
                        smol = fingUp(norm,20,18)

                        if(middle and index and thumb and not ring and not smol and not self.befTaktActive):
                            if(self.time-self.taktTime>=self.cooldown):
                                self.takt.emit()
                                self.taktTime = self.time
                                self.befTaktActive = True
                        else:
                            self.befTaktActive = False

                        direction = middle and index and thumb and ring and smol

                        if(direction and norm[12][0]<-0.15 and not self.befPrevActive):
                            if(self.time-self.prevTime>=self.cooldown):
                                self.prevPage.emit()
                                self.befPrevActive = True
                                self.prevTime = self.time
                        else:
                            self.befPrevActive = False
                            
                        if(direction and norm[12][0]>0.15 and not self.befNextActive):
                            if(self.time-self.nextTime>=self.cooldown):
                                self.nextPage.emit()
                                self.befNextActive = False
                                self.nextTime = self.time
                        else:
                            self.befNextActive = False

                        #zoom
                        if(index and thumb and not middle and not ring and not smol):
                            a = norm[4]
                            b = norm[8]
                            dist = math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)
                            threshold = 0.01

                            pinch = dist
                            if(pinch>self.lastpinch+threshold):
                                self.zoom.emit(+1)
                            if(pinch>self.lastpinch-threshold):
                                self.zoom.emit(-1)
                            self.lastpinch = pinch

                cv2.imshow("Camera",frame)
                if cv2.waitKey(1) & 0xFF==ord('q'):
                    break
                

        finally:
            capture.release()
            cv2.destroyAllWindows()
            hand.close()

class GestureMan(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.thred = QThread()
        self.man = Gesture()
        self.man.moveToThread(self.thred)
        self.thred.started.connect(self.man.run)
        
    def start(self):
        self.thred.start()
        self.man.running = True
    

    def stop(self):
        self.man.running=False
        self.thred.quit()
        self.thred.wait()



