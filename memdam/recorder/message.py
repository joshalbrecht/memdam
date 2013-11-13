
import os
import json
import smtplib
import email
import email.encoders
import email.message
import email.mime.base
import email.mime.multipart
import email.mime.text

from fn import _
from fn.uniform import *
from fn.monad import Option

class Message(object):
    """
    Internal interface for passing messages around.
    May contain references to local files and other nonsense.

    :param file_path: the path to the attached binary file, or None if there isn't one. Should
    be absolute. Will be deleted after the message is sent, so should be a copy of any original file
    and should be stored in a temporary space so that it is erased if the device is rebooted.
    """

    def __init__(self, device, events, file_path=None):
        self._device = device
        self._events = events
        self._file_path = file_path

    def send(self, recipients, smtp_address, username, password):
        """
        Actually perform the sending (blocking is fine)
        """
        server = smtplib.SMTP_SSL(':'.join((str(x) for x in smtp_address)))
        server.login(username, password)
        from_address = self._device
        server.sendmail(from_address, recipients, self._to_email())
        server.quit()

    def delete(self):
        """
        Do any cleanup here after the message has been transmitted.
        """
        if self._file_path != None:
            if os.path.exists(self._file_path):
                os.remove(self._file_path)

    def _to_email(self):
        """
        Convert to a string that can be emailed
        """
        message = email.mime.multipart.MIMEMultipart()
        message['Subject'] = 'subject goes here'
        message['To'] = 'toaddr'
        message['From'] = 'fromaddr'
        maintype = 'application'
        subtype = 'octet-stream'
        text_message = email.mime.text.MIMEText(self._get_text())
        message.attach(text_message)
        if self._file_path != None:
            infile = open(self._file_path, "rb")
            file_message = email.mime.base.MIMEBase(maintype, subtype)
            file_message.set_payload(infile.read())
            infile.close()
            email.encoders.encode_base64(file_message)
            message.add_header('Content-Disposition', 'attachment', filename=self._file_path)
            message.attach(file_message)
        composed = message.as_string()
        return composed

    def _get_text(self):
        """
        Return the body text of the email by serializing the event list
        """
        dict_list = [x.to_json_dict() for x in self._events]
        return json.dumps(dict_list, indent=4, separators=(',', ': '))
