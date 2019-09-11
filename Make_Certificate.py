import werkzeug, os
from werkzeug import serving
import OpenSSL # pip install pyopenssl


def createCertificate(path):
    context = werkzeug.serving.make_ssl_devcert(path)
    print(context)


FolderPath = "certificates"
FilePath = "certificates/certificate"

if not os.path.exists(FolderPath):
    os.makedirs(FolderPath)

print("Creating certificate...")
createCertificate(FilePath)
print("Done. The certificate is in \'certificates/\' folder")
