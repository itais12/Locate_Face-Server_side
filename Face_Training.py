import cv2
import numpy as np
import os
import Constants, UtilsRest, Recognizer
from AWS_S3 import downloadDirectoryFromS3


def face_training():

    path = Constants.DATASET_PATH # Path to the face images folder
    targetPath = Constants.PATH_TO_TRAINER

    print("Downloding faces from S3 Storage...")
    downloadDirectoryFromS3(path)

    print("Training faces...")
    if os.path.exists(path):
        def getImagesAndLabels(path):  # function to get the images and label data
            workerPaths = [os.path.join(path, d) for d in os.listdir(path)]
            faceSamples = []
            ids = []

            for workerPath in workerPaths:
                imagePaths = [os.path.join(workerPath, f) for f in os.listdir(workerPath)]
                for imagePath in imagePaths:
                    if (os.path.split(imagePath)[-1].split(".")[-1] != 'pgm'):
                        continue

                    img = (cv2.imread(imagePath))
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    x = 0
                    y = 0
                    h, w = img.shape[:2]


                    id = int(os.path.split(workerPath)[-1])
                    faceSamples.append(cv2.resize(img[y:y + h, x:x + w], (Constants.WIDTH, Constants.HEIGHT)))
                    ids.append(id)

            return faceSamples, ids

        UtilsRest.writeToLogger("[INFO] Training faces. It will take a few seconds. Wait ...", Constants.DEBUG_MODE)
        faces, ids = getImagesAndLabels(path)

        if(len(ids) == 0):
            UtilsRest.writeToLogger("No faces found in dataset", Constants.DEBUG_MODE)
            return

        recognizer = Recognizer.getRecognizer()
        recognizer.train(faces, np.array(ids))

        UtilsRest.writeToLogger("done train", Constants.DEBUG_MODE)


        path = 'trainer'
        if not os.path.exists(path):
            os.makedirs(path)

        else:
            if os.path.isfile(targetPath):  # delete old file if exist
                os.remove(targetPath)

        # Save the model into trainer/trainer.yml
        recognizer.save(targetPath)

        # write in the log file the number of faces trained
        str = "[INFO] {0} faces trained.".format(len(np.unique(ids)))
        UtilsRest.writeToLogger(str, Constants.DEBUG_MODE)
        print(str)

        UtilsRest.deleteFoldersAndFileInPath(Constants.DATASET_PATH) # delete the face images folder and the content
        Recognizer.readFromFile()