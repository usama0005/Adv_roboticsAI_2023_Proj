import numpy as np
import argparse
import time
import cv2
import os
from gtts import gTTS
import pygame
import cv2
import webbrowser
import tempfile
from PIL import Image


def display_image(image):
    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Save the image to a temporary file
    temp_image_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    pil_image = Image.fromarray(image_rgb)
    pil_image.save(temp_image_path)

    # Open the image using the default web browser
    webbrowser.open('file://' + temp_image_path)




def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True,
                    help="path to input image")
    ap.add_argument("-y", "--yolo", required=True,
                    help="base path to YOLO directory")
    ap.add_argument("-c", "--confidence", type=float, default=0.5,
                    help="minimum probability to filter weak detections")
    ap.add_argument("-t", "--threshold", type=float, default=0.3,
                    help="threshold when applying non-maxima suppression")
    args = vars(ap.parse_args())

    labelsPath = os.path.sep.join([args["yolo"], "coco.names"])
    LABELS = open(labelsPath).read().strip().split("\n")

    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
                               dtype="uint8")

    weightsPath = os.path.sep.join([args["yolo"], "yolov3.weights"])
    configPath = os.path.sep.join([args["yolo"], "yolov3.cfg"])

    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)

    image = cv2.imread(args["image"])
    (H, W) = image.shape[:2]

    ln = net.getUnconnectedOutLayersNames()

    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    end = time.time()

    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    boxes = []
    confidences = []
    classIDs = []

    for output in layerOutputs:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence > args["confidence"]:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, args["confidence"],
                            args["threshold"])

    if len(idxs) > 0:
        list1 = []
        for i in idxs.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])
            centerx = round((2 * x + w) / 2)
            centery = round((2 * y + h) / 2)
            if centerX <= W / 3:
                W_pos = "left "
            elif centerX <= (W / 3 * 2):
                W_pos = "center "
            else:
                W_pos = "right "

            if centerY <= H / 3:
                H_pos = "top "
            elif centerY <= (H / 3 * 2):
                H_pos = "mid "
            else:
                H_pos = "bottom "
            list1.append(H_pos + W_pos + LABELS[classIDs[i]])

        description = ', '.join(list1)

        myobj = gTTS(text=description, lang="en", slow=False)
        myobj.save("object_detection.mp3")

        # Play the audio using pygame
        pygame.mixer.init()
        pygame.mixer.music.load("object_detection.mp3")
        pygame.mixer.music.play()

        # Display the image using Pillow
        display_image(image)

        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # Close the audio mixer
        pygame.mixer.quit()

if __name__ == "__main__":
    main()

#python script.py -i images/bottom.jpg -y yolo
