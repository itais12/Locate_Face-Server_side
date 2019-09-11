import Constants, UtilsRest, Database


def toXLS(isDepartmentReport, worker_id, fromDate, toDate, department):
    import pandas as pd
    cursor = Database.getDBCursor()

    if isDepartmentReport:
        script = "SELECT working_hours.worker_id as 'Worker_ID', workers.name as 'Worker Name', " \
                        "CONVERT(date(working_hours.check_in_time), CHAR) as Date, CONVERT(time(check_in_time), CHAR) as 'Starting time', " \
                        "CONVERT(time(check_out_time), CHAR) as 'Ending time', working_hours.id as 'Record_number' " \
                "FROM facelogin.working_hours, facelogin.workers " \
                "WHERE working_hours.worker_id = workers.worker_id AND workers.department = '%s' AND date(working_hours.check_in_time) BETWEEN date('%s') AND date('%s')" \
                "ORDER BY Date, Worker_ID" \
                 % (department, fromDate, toDate)
    else:
        script = "SELECT CONVERT(date(working_hours.check_in_time), CHAR) as Date, CONVERT(time(check_in_time), CHAR) as 'Starting time', " \
                        "CONVERT(time(check_out_time), CHAR) as 'Ending time', working_hours.id as 'Record_number' " \
                 "FROM working_hours " \
                 "WHERE worker_id = %s AND date(check_in_time) BETWEEN date('%s') AND date('%s')" \
                 % (worker_id, fromDate, toDate)
    cursor.execute(script)

    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    df = pd.DataFrame(list(data), columns=columns)

    writer = pd.ExcelWriter(Constants.HOURS_REPORT_FILE_NAME)
    df.to_excel(writer, sheet_name='Report')

    writer.save()
    UtilsRest.writeToLogger("\'"+ Constants.HOURS_REPORT_FILE_NAME +"\' file has been created",Constants.DEBUG_MODE)


