import Constants
import logging
import sys
import os
import cv2
import datetime

try:
    FORMAT = '%(asctime)-15s %(clientip)-20s  %(message)s'
    level = logging.DEBUG # logging.DEBUG or logging.ERROR
    logName = Constants.SERVER_LOG

    logger = logging.getLogger(logName)
    logger.setLevel(level)

    # create file handler
    ch = logging.FileHandler(logName, mode='w')  # clear the log file
    ch.setLevel(level)

    # create formatter
    formatter = logging.Formatter(FORMAT)

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


except Exception:
    sys.exit("No space on the disk. please make some space") # closes the program


def writeToLogger(message, type, clientip=None):
    if(clientip is None):
        clientip = "\tSERVER"
    if type == Constants.ERROR_MODE:
        logger.error(msg=message, extra={'clientip': clientip})
    elif type == Constants.DEBUG_MODE:
        logger.debug(msg=message, extra={'clientip': clientip})


def checkInTimeBeforeOutTime(str_in_time, str_out_time):
    time_format = '%H:%M:%S'
    time_in = datetime.datetime.strptime(str_in_time, time_format)
    time_out = datetime.datetime.strptime(str_out_time, time_format)
    return time_in < time_out


def loadImagesForRecognition(path, num_of_images):
    greyImages = []

    for i in range(num_of_images):
        imagePath = path + "\\" + str(i + 1) + ".pgm"
        img = cv2.imread(imagePath)
        greyImages.append(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    return greyImages


def deleteFoldersAndFileInPath(path):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            deleteFoldersAndFileInPath(file_path)
            os.removedirs(file_path)

