import mysql.connector
import Constants

mydb = None
mycursor = None


def initDB(host, port, user, passwd):
    global mydb
    global mycursor
    mydb = mysql.connector.connect(host=host, user=user, passwd=passwd, port=port)

    mycursor = mydb.cursor()
    mycursor.execute("CREATE DATABASE IF NOT EXISTS "+ Constants.DATABASE_NAME)
    mydb.database= Constants.DATABASE_NAME

    mycursor.execute("CREATE TABLE IF NOT EXISTS workers (worker_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), id INT, "
                      + "role VARCHAR(255), department VARCHAR(255), pinCode VARCHAR(255), managerPermissions BOOL, email VARCHAR(255))")

    mycursor.execute("CREATE TABLE IF NOT EXISTS working_hours (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,"
                      + "worker_id INT NOT NULL, "
                      + "check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ,"
                      + "check_out_time TIMESTAMP NULL )")

    mycursor = mydb.cursor()


def getDBCursor():
    global mycursor
    return mycursor


def getDB():
    global mydb
    return mydb
