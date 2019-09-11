import boto3
import Constants, UtilsRest
import os


def uploadFileToS3(fullFileName):
    global bucket
    try:
        bucket.upload_file(fullFileName, fullFileName)

    except Exception as e:
        UtilsRest.writeToLogger(e, Constants.ERROR_MODE)
        pass


def downloadDirectoryFromS3(remoteDirectoryName):
    global bucket
    for key in bucket.objects.filter(Prefix = remoteDirectoryName):
        if not os.path.exists(os.path.dirname(key.key)):
            os.makedirs(os.path.dirname(key.key))

        bucket.download_file(key.key,key.key)


def removeFolderFromS3(path): # delete folder and content
    global bucket
    bucket.objects.filter(Prefix=path).delete()


# Create an S3 resource
s3 = boto3.resource('s3',
                aws_access_key_id=Constants.AWS_SERVER_PUBLIC_KEY,
                aws_secret_access_key=Constants.AWS_SERVER_SECRET_KEY,
                region_name=Constants.REGION_NAME)


bucket = s3.Bucket(Constants.BUCKET_NAME)