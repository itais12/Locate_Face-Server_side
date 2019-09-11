from threading import Timer
import traceback
import Constants
import Face_Training
import UtilsRest

needTrain = False


def delayedTrain():
    global needTrain

    def startDelayedTrain():
        global needTrain
        try:
            Face_Training.face_training()

        except Exception as e:
            UtilsRest.writeToLogger(str(e), Constants.ERROR_MODE)
            UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)  # saves the stacktrace to the logger

        finally:
            needTrain = False

    if(not needTrain):
        needTrain = True
        Timer(Constants.THREAD_TRAIN_TIMER, startDelayedTrain).start()

