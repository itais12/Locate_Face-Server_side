''''
Face Recogition
	==> Each face stored on dataset/ dir, should have a unique numeric integer ID as 1, 2, 3, etc
	==> FisherFace computed model (trained faces) should be on trainer/ dir
'''

import Constants, UtilsRest, Recognizer, os

#iniciate id counter
id = 0

def face_recognition(greyImages):
    UtilsRest.writeToLogger("RECONIZING", "debug")

    if not os.path.isfile(Constants.PATH_TO_TRAINER):
        UtilsRest.writeToLogger("No trainer file exist, " + Constants.RECOGNIZE_FAILED, "error")
        raise FileNotFoundError(Constants.ERROR_MESSAGE + Constants.RECOGNIZE_FAILED)

    recognizer = Recognizer.getRecognizer()

    ids = {}
    index = 1
    for img in greyImages:
        if(img is None):
            UtilsRest.writeToLogger("No image exist by name: %d.pgm" %  index, Constants.DEBUG_MODE)
            break

        x, y = 0,0
        height, width = img.shape[:2]
        id, confidence = recognizer.predict(img[y:y + height, x:x + width])
        UtilsRest.writeToLogger("id: %d, conf: %d" % (id, confidence), "debug")

        # values that lower than FISHERFACE_CONFIDENCE are good enough for prediction
        if (confidence <= Constants.FISHERFACE_CONFIDENCE):
            if(id not in ids):
                ids[id] = 0
            ids[id] = ids[id]+1

        index = index+1

    maxID = 0
    maxVal = 0

    for i in ids:
        if (ids[i] > maxVal):
            maxID = i
            maxVal = ids[i]

    UtilsRest.writeToLogger("Recognized id: %d" % maxID, "debug")
    UtilsRest.writeToLogger("Number of times recognized: %d" % maxVal, "debug")

    if (maxVal >= (len(greyImages)/2)):
        return maxID
    else:
       return Constants.UNKNOWN
