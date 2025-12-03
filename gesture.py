import cv2
import mediapipe as mp
import math 

capture = cv2.VideoCapture(0)
hands = mp.solutions.hands
draw = mp.solutions.drawing_utils

hand = hands.Hands(
    static_image_mode = False,
    max_num_hands = 1,
    min_detection_confidence = 0.5,
    min_tracking_confidence = 0.5
)
while True:
    ret,frame = capture.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

    result = hand.process(rgb)
    if result.multi_hand_landmarks:
        for landmarks in result.multi_hand_landmarks:
            draw.draw_landmarks(
                frame,
                landmarks,
                hands.HAND_CONNECTIONS
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

            if(middle and index and thumb and not ring and not smol):
                print("TAKT")

            direction = middle and index and thumb and ring and smol
            if(direction and norm[12][0]<-0.15):
                print("prev")
            elif(direction and norm[12][0]>0.15):
                print("next")

            #zoom
            if(index and thumb and not middle and not ring and not smol):
                a = norm[4]
                b = norm[8]
                dist = math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)
                print(dist)
    cv2.imshow("Camera",frame)
    if cv2.waitKey(1) & 0xFF==ord('q'):
        break
    


capture.release()
cv2.destroyAllWindows()
hand.close()

