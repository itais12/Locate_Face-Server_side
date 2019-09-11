import random, json

import Database, UtilsRest, Constants
import Face_Recognition
import DB_To_Excel
from Email_Manager_Google import sendFileByEmail


def register(worker, lock):
    pin_code = random.randint(1000, 99999)  # random int code
    worker.setPinCode(pin_code)

    # add the this worker to the database
    sql = "INSERT INTO workers (worker_id, name, id, role, department, pinCode, managerPermissions, email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    val = (None, worker.getName(), worker.getId(), worker.getRole(), worker.getDepartment(), worker.getPinCode(), worker.getManagerPermissions(), worker.getEmail())

    # start critical code ######################################################################
    lock.acquire(True)  # blocking until the lock is unlocked, then set it to locked and return True

    mycursor = Database.getDBCursor()
    mycursor.execute(sql, val)  # insert the worker to the database
    Database.getDB().commit()  # update the database
    worker.setWorkerId(mycursor.lastrowid)

    lock.release()
    # end critical code ######################################################################

    # return json of the worker with the pinCode
    str_json = json.dumps(worker.__dict__)
    return str_json


def recognition(reqType, worker, lock, num_of_images, path):
    try:
        greyImages = UtilsRest.loadImagesForRecognition(path, num_of_images)   # load the pictures of the worker to an array

        workerId = Face_Recognition.face_recognition(greyImages)   # recognize the worker
        if (workerId != Constants.UNKNOWN and workerId < 1):
            raise RuntimeError(Constants.ERROR_MESSAGE + " Internal Server Error (2)")

    finally:
        UtilsRest.deleteFoldersAndFileInPath(path) # delete the temp images

    if (workerId == Constants.UNKNOWN):
        return {'response':Constants.ERROR_MESSAGE + ' Did not recognized the worker'}

    else:
        # get the worker name from the database
        sql = "SELECT name, pinCode FROM workers WHERE worker_id = %s"
        val = (workerId,)

        mycursor = Database.getDBCursor()
        mycursor.execute(sql, val)
        res = mycursor.fetchone()

        # verify the worker pinCode
        if (res[1] != worker.getPinCode()):
            UtilsRest.writeToLogger('Recognition unsuccessful, Wrong pincode.', Constants.DEBUG_MODE)
            return {'response':Constants.ERROR_MESSAGE + ' The pincode is incorrect'}

        else:
            worker.setName(res[0])
            worker.setWorkerId(workerId)

            if (reqType == Constants.RECOGNIZE_IN):

                # get the num of check-in today for this worker
                sql = "SELECT COUNT(*) FROM working_hours WHERE worker_id = %s AND DATE(check_in_time) = DATE(NOW())"
                val = (worker.getWorkerId(),)

                mycursor.execute(sql, val)
                res = mycursor.fetchone()

                if (res[0] >= 3):  # num of check-in >= 3
                    return {'response':Constants.ERROR_MESSAGE + ' The worker already checked-in 3 time today'}

                else:  # num of check-in < 3

                    # add the check-in of this worker to the database
                    sql = "INSERT INTO working_hours (id, worker_id) VALUES (%s, %s)"
                    val = (None, worker.getWorkerId())

                    # start critical code ######################################################################
                    lock.acquire(True)  # blocking until the lock is unlocked, then set it to locked and return True

                    mycursor.execute(sql, val)  # insert the check-in of the worker to the database
                    Database.getDB().commit()  # update the database

                    lock.release()
                    # end critical code ######################################################################

            elif (reqType == Constants.RECOGNIZE_OUT):

                # get all the check-out of this worker that was today or yesterday
                sql = "SELECT id, check_out_time FROM working_hours WHERE worker_id = %s AND (DATE(check_in_time) = DATE(NOW()) OR DATE(check_in_time) = DATE(NOW() - DAY(1)))"
                val = (worker.getWorkerId(),)
                mycursor.execute(sql, val)
                res = mycursor.fetchall()

                if (res[-1][1] is not None):  # the last action of the worker was check-out
                   return {'response':Constants.ERROR_MESSAGE + ' No check-in was found'}

                else:  # the last action of the worker was check-in

                    # add the check-out of this worker to the last check-in row in the database
                    sql = "UPDATE working_hours SET check_out_time = NOW() WHERE id = %s"
                    val = (res[-1][0],)

                    # start critical code ######################################################################
                    lock.acquire(True)  # blocking until the lock is unlocked, then set it to locked and return True

                    mycursor.execute(sql, val)  # insert the worker check-out time to the database
                    Database.getDB().commit()  # update the database

                    lock.release()
                    # end critical code ######################################################################

            UtilsRest.writeToLogger('Recognition passed successfully. Worker id: %d'% worker.getWorkerId(), Constants.DEBUG_MODE)

            # return json of the worker with the name and workerId
            str_json = worker.__dict__
            UtilsRest.writeToLogger(str_json, Constants.DEBUG_MODE)

            return str_json


def hoursReport(json_obj, lock):
    worker_id = json_obj.get('workerId')
    pin_code = json_obj.get('pinCode')
    fromDate = json_obj.get('fromDate')
    toDate = json_obj.get('toDate')
    isDepartmentReport = json_obj.get('isDepartmentReport')
    workerDepartment = None

    if((worker_id is None) or (pin_code is None) or (fromDate is None) or (toDate is None) or (isDepartmentReport is None)):
        return "Some values are missing in the request"

    # get the worker manager permissions, pin code, email and department from the database
    sql = "SELECT pinCode, managerPermissions, email, department " \
          "FROM workers " \
          "WHERE worker_id = %s"
    val = (worker_id,)

    mycursor = Database.getDBCursor()
    mycursor.execute(sql, val)
    res = mycursor.fetchone()
    UtilsRest.writeToLogger(res, Constants.DEBUG_MODE)

    # check if res is empty
    if (len(res) == 0):
        return Constants.ERROR_MESSAGE + " The worker id %s is incorrect" % worker_id

    # verify the worker's pinCode
    if (res[0] != pin_code):
        return "Error: The pincode is incorrect"

    # verify the worker's manager permissions
    if (isDepartmentReport):
        if(not res[1]): #  manager permissions is False
            return "Error: The worker doesn't has manager permissions"
        workerDepartment = res[3]

    workerEmail = res[2]

    # start critical code ######################################################################
    lock.acquire(True)  # blocking until the lock is unlocked, then set it to locked and return True

    DB_To_Excel.toXLS(isDepartmentReport, worker_id, fromDate, toDate, workerDepartment)

    # send the file to the worker email
    sendFileByEmail(workerEmail, Constants.HOURS_REPORT_FILE_NAME)

    lock.release()
    # end critical code ######################################################################

    # return success message
    success_str = "The hours report was sent to your email, check your email in a few minutes"
    UtilsRest.writeToLogger(success_str, Constants.DEBUG_MODE)

    return success_str


def hoursUpdate(json_obj, lock):
    worker_id = json_obj.get('workerId')
    recordNumber = json_obj.get('recordNumber')
    date = json_obj.get('date')
    updatedInHour = json_obj.get('updatedInHour')
    updatedOutHour = json_obj.get('updatedOutHour')

    inOrOut = 0 # 1 - in, 2 - out, 3 - both
    error_str = Constants.ERROR_MESSAGE + " Check In time cannot be after check out time"

    if((worker_id is None) or (date is None)):
        return "Some values are missing in the request"

    if (updatedInHour is not None):
        inOrOut = inOrOut + Constants.HOURS_UPDATE_IN

    if (updatedOutHour is not None):
        inOrOut = inOrOut + Constants.HOURS_UPDATE_OUT

    if (inOrOut == 0):
        return "Both 'Updated in hour' and 'Updated out hour' are missing in the request. Fill one at least"

    mycursor = Database.getDBCursor()

    if (recordNumber is None): # insert new record

        sql = "SELECT worker_id " \
              "FROM workers " \
              "WHERE worker_id = %s"

        val = (worker_id,)
        mycursor.execute(sql, val)
        res = mycursor.fetchone()

        outDatetime = None

        if (len(res) == 0):
            return Constants.ERROR_MESSAGE + " The worker id is incorrect"

        if (updatedOutHour == Constants.HOURS_UPDATE_OUT):
            return Constants.ERROR_MESSAGE + " Cannot insert new record with 'Updated out hour' only"

        elif(updatedOutHour == Constants.HOURS_UPDATE_BOTH):
            if (not UtilsRest.checkInTimeBeforeOutTime(updatedInHour, updatedOutHour)):
                return error_str
            outDatetime = date + " " + updatedOutHour

        sql = "INSERT INTO working_hours (id, worker_id, check_in_time, check_out_time) " \
              "VALUES (%s, %s, %s, %s)"

        val = (None, worker_id, date + " " + updatedInHour, outDatetime)

        # start critical code ######################################################################
        lock.acquire(True)  # blocking until the lock is unlocked, then set it to locked and return True

        mycursor.execute(sql, val)  # update the record
        Database.getDB().commit()  # update the database

        lock.release()
        # end critical code ######################################################################

    else: # update existing record

        # get the worker_id and the date from the database to compare
        sql = "SELECT worker_id as Worker_ID, date(check_in_time) as Date, " \
                    "time(check_in_time) as Check_in_hour, time(check_out_time) as Check_out_hour " \
              "FROM working_hours " \
              "WHERE id = %s"

        val = (recordNumber,)
        mycursor.execute(sql, val)
        res = mycursor.fetchone()

        if(len(res) == 0): # check if empty
            return Constants.ERROR_MESSAGE + " The record number %s not exist" % (recordNumber)

        if (res[0] != worker_id):
            return Constants.ERROR_MESSAGE + " The worker doesn't belong to this record number"

        if (str(res[1]) != date):
            return Constants.ERROR_MESSAGE + " The date doesn't belong to this record number"

        sqlSetString = ""

        if(inOrOut == Constants.HOURS_UPDATE_IN):
            if(not UtilsRest.checkInTimeBeforeOutTime(updatedInHour, str(res[3]))):
                return error_str
            sqlSetString = sqlSetString + "check_in_time = '%s'" % (date + " " + updatedInHour)

        elif (inOrOut == Constants.HOURS_UPDATE_OUT):
            if (not UtilsRest.checkInTimeBeforeOutTime(str(res[2]), updatedOutHour)):
                return error_str
            sqlSetString = sqlSetString + "check_out_time = '%s'" % (date + " " + updatedOutHour)

        elif (inOrOut == Constants.HOURS_UPDATE_BOTH):
            if (not UtilsRest.checkInTimeBeforeOutTime(updatedInHour, updatedOutHour)):
                return error_str
            sqlSetString = sqlSetString + "check_in_time = \'%s\', check_out_time = '%s'" % (date + " " + updatedInHour, date + " " + updatedOutHour)


        sql = "UPDATE working_hours " \
              "SET " + sqlSetString + " " \
              "WHERE id = %s"
        val = (recordNumber,)

        # start critical code ######################################################################
        lock.acquire(True)  # blocking until the lock is unlocked, then set it to locked and return True

        mycursor.execute(sql, val)  # update the record
        Database.getDB().commit()  # update the database

        lock.release()
        # end critical code ######################################################################

    # return success message
    success_str = "The hours updated successfuly. worker_id: %s, date: %s" % \
                  (worker_id, date)
    UtilsRest.writeToLogger(success_str, Constants.DEBUG_MODE)

    return success_str



