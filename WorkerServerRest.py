import os, sys, traceback, configparser, _thread
import mysql, base64
from werkzeug import exceptions
import ssl
from flask import Flask, request
from flask_restful import Resource, Api
import json, time

import Constants, UtilsRest, ModesRest, Recognizer, Database
from WorkerClass import Worker
import Google_Auth_Gmail, DelayedTrain, AWS_S3, Face_Training


def propertiesInit():  # if properties file exist -> ask if want to change the last settings
    global server_host
    global server_port
    global database_host
    global database_port
    global database_user
    global database_passwd

    flag = False

    config = configparser.ConfigParser()
    pathToFile = 'properties.ini'

    if not os.path.isfile(pathToFile):  # properties file not exist
        flag = True

    else:  # properties file exist
        config.read('properties.ini')
        if ('Server_Properties' in config):
            server_host = config['Server_Properties']['server_host']
            server_port = int(config['Server_Properties']['server_port'])
            database_host = config['Server_Properties']['database_host']
            database_port = int(config['Server_Properties']['database_port'])
            database_user = config['Server_Properties']['database_user']
            database_passwd = config['Server_Properties']['database_passwd']

            answer = input("Do you want to change the last settings? (Y / y - yes, any other character - no)\t")
            if (answer == "Y" or answer == "y"):
                flag = True

        else:
            flag = True

    def serverSettings():
        global server_host
        global server_port

        print("\nServerSettings:")

        tmp = input("Enter the server host: (leave empty for " + Constants.SERVER_HOST + ")\t")
        if (tmp != ""):
            server_host = tmp
            config['Server_Properties']['server_host'] = server_host
        else:
            server_host = Constants.SERVER_HOST
            config['Server_Properties']['server_host'] = Constants.SERVER_HOST

        tmp = input("Enter the server port: (leave empty for default port: " + str(Constants.SERVER_PORT) + ")\t")

        if (tmp != ""):
            while (not tmp.isnumeric()):
                tmp = input("Server port must be numeric! try again:\t")
            server_port = int(tmp)
            config['Server_Properties']['server_port'] = str(server_port)
        else:
            server_port = Constants.SERVER_PORT
            config['Server_Properties']['server_port'] = str(Constants.SERVER_PORT)

    def databaseSettings():
        global database_host
        global database_port
        global database_user
        global database_passwd

        print("\nDatabase Settings:")

        tmp = input("Enter the mysql database host: (leave empty for " + Constants.DATABASE_HOST + ")\t")
        if (tmp != ""):
            database_host = tmp
            config['Server_Properties']['database_host'] = database_host
        else:
            database_host = Constants.DATABASE_HOST
            config['Server_Properties']['database_host'] = Constants.DATABASE_HOST

        tmp = input("Enter the mysql database port: (leave empty for default port: " + str(Constants.DATABASE_PORT) + ")\t")
        if (tmp != ""):
            while (not tmp.isnumeric()):
                tmp = input("database port must be numeric! try again:\t")
            database_port = int(tmp)
            config['Server_Properties']['database_port'] = str(database_port)
        else:
            database_port = Constants.DATABASE_PORT
            config['Server_Properties']['database_port'] = str(Constants.DATABASE_PORT)

        tmp = input("Enter the mysql database user name:\t")
        while (tmp == ""):
            tmp = input("Must enter database user name! try again:\t")
        database_user = tmp
        config['Server_Properties']['database_user'] = database_user

        tmp = input("Enter the mysql database password:\t")
        while (tmp == ""):
            tmp = input("Must enter database password! try again:\t")
        database_passwd = tmp
        config['Server_Properties']['database_passwd'] = str(database_passwd)

    if flag:
        config['Server_Properties'] = {}
        print("\nPlease enter the following setting:")
        serverSettings() # get the server_host and server_port from the user and keep in properties file
        databaseSettings() # get the database_host and database_port the user and keep in properties file

        with open('properties.ini', 'w') as configfile:
            config.write(configfile)


def trainRecognizerNow():
    answer = input("Do you want to train the recognizer now? (Y / y - yes, any other character - no)\t")
    if (answer == "Y" or answer == "y"):
        try:
            Face_Training.face_training()
        except Exception as e:
            UtilsRest.writeToLogger(str(e), Constants.ERROR_MODE)
            UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)  # saves the stacktrace to the logger
            print("Training failed.")


def convertWorkerJsonToWorkerObject(worker_str):
    worker = Worker(**worker_str)  # convert to Worker object
    UtilsRest.writeToLogger(worker, Constants.DEBUG_MODE)
    UtilsRest.writeToLogger("Converted from json to object(worker)", Constants.DEBUG_MODE)
    return worker


print("Starting the server. Please wait...")
UtilsRest.writeToLogger("Starting the server", Constants.DEBUG_MODE)

server_host = Constants.SERVER_HOST
server_port = Constants.SERVER_PORT

database_host = Constants.DATABASE_HOST
database_port = Constants.DATABASE_PORT
database_user = None
database_passwd = None

propertiesInit()

try:
    Database.initDB(database_host, database_port, database_user,
                    database_passwd)  # Creating the database & tables if not exist already

except mysql.connector.errors.DatabaseError as e:
    UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)  # saves the stacktrace to the logger
    sys.exit("Connection to the database failed. (is the database settings correct?)")  # closes the program

except Exception as e:
    UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)  # saves the stacktrace to the logger
    sys.exit("Connection to the database failed.")  # closes the program

lock = _thread.allocate_lock()

try:
    Google_Auth_Gmail.google_auth()

except Exception as e:
    UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)  # saves the stacktrace to the logger
    sys.exit("Gmail Connection problem.")  # closes the program

Recognizer.initRecognizer()
DelayedTrain.delayedTrain()
trainRecognizerNow()

print("waiting for a connection...")

app = Flask(__name__)
api = Api(app)


def getWorkerFromJson(json_obj):
    worker_str_json = json_obj.get('worker')

    if(worker_str_json is None):
        raise Exception(Constants.ERROR_MESSAGE + " Didn't got the worker's details")

    worker_obj_json = json.loads(worker_str_json)  # convert to general object
    worker = convertWorkerJsonToWorkerObject(worker_obj_json)
    return worker


def saveImageFromClient(json_obj, base_path, isRegister):
    amountOfPictures = json_obj.get('amountOfPictures')

    if (amountOfPictures is None):
        raise Exception(Constants.ERROR_MESSAGE + " Didn't got the amount Of pictures")

    if not os.path.exists(base_path):
        os.makedirs(base_path)

    for i in range(amountOfPictures):
        path = base_path + "/" + str(i + 1) + ".pgm"
        image_json = json_obj.get(str(i))

        if (image_json is None):
            raise Exception(Constants.ERROR_MESSAGE + " Didn't got some of the pictures")

        image_obj = json.loads(image_json)
        image_str = image_obj.get('image')

        if (image_str is None):
            raise Exception(Constants.ERROR_MESSAGE + " Didn't got some of the pictures")

        image = base64.urlsafe_b64decode(image_str)
        myfile = open(path, 'wb')
        myfile.write(image)
        myfile.close()

        if (isRegister):
            AWS_S3.uploadFileToS3(path)

    return amountOfPictures


class Root(Resource):
    def get(self):
        return {'status': 'success'}


class Register(Resource):

    def post(self):
        UtilsRest.writeToLogger("Register request: from " + str(request.remote_addr) +" at: "+ time.strftime('%Y-%m-%d %H:%M:%S'), Constants.DEBUG_MODE)
        json_obj = request.get_json(force=True)
        UtilsRest.writeToLogger("got the json", Constants.DEBUG_MODE)
        worker = None
        base_path = ""
        worker_id = None

        try:
            worker = getWorkerFromJson(json_obj)
            ModesRest.register(worker, lock)
            worker_id = worker.getWorkerId()
            base_path = Constants.DATASET_PATH + "/" + str(worker_id)
            saveImageFromClient(json_obj, base_path, True)

        except Exception as e:
            UtilsRest.writeToLogger("An error has occurred: " + str(e), Constants.ERROR_MODE)
            UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)  # saves the stacktrace to the logger

            if(worker_id is not None):
                AWS_S3.removeFolderFromS3(Constants.DATASET_PATH + '/' + str(worker_id))

            if(worker is not None):
                # delete the worker from the database
                sql = "DELETE FROM workers WHERE worker_id=%s"
                val = (worker.getWorkerId())
                Database.getDBCursor().execute(sql, val)
                Database.getDB().commit()  # update the database

                UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)  # saves the stacktrace to the logger
                id = worker.getWorkerId()
                if (base_path != ""):
                    AWS_S3.removeFolderFromS3(Constants.DATASET_PATH + '/' + str(id))
                    UtilsRest.deleteFoldersAndFileInPath(base_path)

            return str(e), 500

        try:
            # Train the predictor
            DelayedTrain.delayedTrain()
            UtilsRest.deleteFoldersAndFileInPath(Constants.DATASET_PATH)

        except Exception as e:
            UtilsRest.writeToLogger(Constants.TRAIN_FAILED, Constants.ERROR_MODE)
            UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)  # saves the stacktrace to the logger
            pass  # do nothing

        return worker.__dict__


class Recognition(Resource):

    def post(self):
        UtilsRest.writeToLogger("Recognition request: from " + str(request.remote_addr) +" at: "+ time.strftime('%Y-%m-%d %H:%M:%S'), Constants.DEBUG_MODE)
        json_obj = request.get_json(force=True)
        UtilsRest.writeToLogger("got the json", Constants.DEBUG_MODE)

        worker = None
        base_path = ""

        try:
            worker = getWorkerFromJson(json_obj)
            base_path = "tempRecognition/"   + str(request.remote_addr)
            amountOfPictures = saveImageFromClient(json_obj, base_path, False)
            reqType = json_obj.get('reqType')

            if(reqType is None):
                raise RuntimeError(Constants.ERROR_MESSAGE + "Didn't got the request type")

            response = ModesRest.recognition(reqType, worker, lock, amountOfPictures, base_path)

        except Exception as e:
            UtilsRest.writeToLogger("An error has occurred: " + str(e),Constants.ERROR_MODE)
            UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)  # saves the stacktrace to the logger
            return str(e), 500

        return response


class HoursReport(Resource):

    def get(self, json_str):
        UtilsRest.writeToLogger("Hours report request: from " + str(request.remote_addr) +" at: "+ time.strftime('%Y-%m-%d %H:%M:%S'), Constants.DEBUG_MODE)
        UtilsRest.writeToLogger(json_str, Constants.DEBUG_MODE)
        json_obj = json.loads(json_str)
        UtilsRest.writeToLogger("got the json", Constants.DEBUG_MODE)
        message = ModesRest.hoursReport(json_obj, lock)
        return {'response': message}


class HoursUpdate(Resource):

    def post(self):
        UtilsRest.writeToLogger("Hours update request: from " + str(request.remote_addr) +" at: "+ time.strftime('%Y-%m-%d %H:%M:%S'), Constants.DEBUG_MODE)
        json_obj = request.get_json(force=True)
        UtilsRest.writeToLogger("got the json", Constants.DEBUG_MODE)
        message = ModesRest.hoursUpdate(json_obj, lock)
        return {'response':message}


api.add_resource(Root, '/')
api.add_resource(Register, '/register')
api.add_resource(Recognition, '/recognition')
api.add_resource(HoursReport, '/hoursReport/<json_str>')
api.add_resource(HoursUpdate, '/hoursUpdate')


if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_cert_chain("certificates/certificate.crt", "certificates/certificate.key")
    app.run(host=server_host, port=server_port, ssl_context=context, threaded=True)

