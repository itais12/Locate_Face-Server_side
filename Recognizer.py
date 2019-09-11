import cv2, os
import Constants

recognizer = None


def initRecognizer():
    global recognizer
    recognizer = cv2.face.FisherFaceRecognizer_create()

    if os.path.isfile(Constants.PATH_TO_TRAINER):
        readFromFile()

    return recognizer

def readFromFile():
    global recognizer
    recognizer.read('trainer/trainer.yml')

def getRecognizer():
    global recognizer
    return recognizer