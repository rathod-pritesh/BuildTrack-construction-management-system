import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime

# from PIL import ImageGrab

path = 'C:\\Users\\Pritesh Rathod\\OneDrive\\Desktop\\BuildTrack\\static\\faces'

images = []
classNames = []
myList = os.listdir(path)
print(myList)

for cl in myList:
    img_path = os.path.join(path, cl)

    # read img
    curImg = cv2.imread(img_path)
    
    if curImg is None:
        print(f"Skipping invalid image: {cl}")
        continue

    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])

print("Loaded class names: ", classNames)

# encode faces
def findEncodings(images):
    encodeList = []

    for img in images:

        try:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            encodings = face_recognition.face_encodings(img)

            if len(encodings) > 0:
                encodeList.append(encodings[0])
            else:
                print("No face detected in images, skipping")

        except Exception as e:
            print("Encoding error: ", e)

    return encodeList

# Attendance function
def markAttendance(name):
    file_path = 'Attendance.csv'

    # Create file if not exists
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write("Name,Time\n")  

    with open(file_path, 'r+') as f:

        myDataList = f.readlines()
        nameList = [line.split(',')[0] for line in myDataList]  

        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{name},{dtString}')

# Encode known faces
encodeListKnown = findEncodings(images)
print('Encoding Complete')

# Start webcam
cap = cv2.VideoCapture(0)

while True:

    success, img = cap.read()

    if not success:
        print("Failed to capture frame")
        break

    # Resize for faster processing
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Detect face
    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            name = classNames[matchIndex].upper()

            y1, x2, y2, x1 = faceLoc

            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)

            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

            markAttendance(name)

    cv2.imshow('Webcam', img)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()