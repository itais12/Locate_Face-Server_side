
class Worker:
    def __init__(self, pinCode, workerId, id, name, role, department, managerPermissions, email):
        self.pinCode = pinCode
        self.workerId = int(workerId)
        self.id = int(id)
        self.name = name
        self.role = role
        self.department = department
        self.managerPermissions = managerPermissions
        self.email = email


    def getPinCode(self):
        return self.pinCode

    def setPinCode(self, pinCode):
        self.pinCode = pinCode

    def getWorkerId(self):
        return self.workerId

    def setWorkerId(self, workerId):
        self.workerId = int(workerId)

    def getId(self):
        return self.id

    def setId(self, id):
        self.id = int(id)

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name

    def getRole(self):
        return self.role

    def setRole(self, role):
        self.role = role

    def getDepartment(self):
        return self.department

    def setDepartment(self, department):
        self.department = department

    def getManagerPermissions(self):
        return self.managerPermissions

    def setManagerPermissions(self, managerPermissions):
        self.managerPermissions = managerPermissions

    def getEmail(self):
        return self.email

    def setEmail(self, email):
        self.email = email

    def __str__(self):
        return "worker details -> pinCode: %s, workerId: %d, id: %d, name: %s, role: %s, department: %s, manager permissions: %s, email: %s" % \
               (self.pinCode, self.workerId, self.id, self.name, self.role, self.department, self.managerPermissions, self.email)


