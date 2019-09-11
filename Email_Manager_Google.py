import smtplib, Constants, UtilsRest, Google_Auth_Gmail
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes, base64, os, traceback
from apiclient import errors


def create_message_with_attachment(sender, to, subject, message_text, file):
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    content_type, encoding = mimetypes.guess_type(file)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)

    if main_type == 'text':
        fp = open(file, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()

    elif main_type == 'image':
        fp = open(file, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()

    elif main_type == 'audio':
        fp = open(file, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()

    else:
        fp = open(file, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        encoders.encode_base64(msg)
        fp.close()

    filename = os.path.basename(file)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}


def sendFileByEmail(email, filepath):
    subject = "Hours Report from \'Locate Face\'"
    body = "The hours report is attached"
    sender_email = Constants.EMAIL_USER
    receiver_email = email

    message = create_message_with_attachment(sender_email, receiver_email, subject, body, filepath)

    try:
        Google_Auth_Gmail.google_auth()
        response = (Google_Auth_Gmail.getGmailService().users().messages().send(userId=Constants.EMAIL_USER, body=message).execute())
        UtilsRest.writeToLogger('Message Id: %s' % response['id'],Constants.DEBUG_MODE)
        return message

    except errors.HttpError as e:
        UtilsRest.writeToLogger('An error occurred: %s' % str(e),Constants.ERROR_MODE)
        UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)

    except Exception as e:
        UtilsRest.writeToLogger("error: " + str(e), Constants.ERROR_MODE)
        UtilsRest.writeToLogger(traceback.format_exc(), Constants.ERROR_MODE)



