
"""Send a test email to the local server"""

import smtplib
import email
import email.encoders
import email.message
import email.mime.base
import email.mime.multipart
import email.mime.text

def create_message(text_content, file_name=None):
    message = email.mime.multipart.MIMEMultipart()
    message['Subject'] = 'subject goes here'
    message['To'] = 'toaddr'
    message['From'] = 'fromaddr'
    maintype = 'application'
    subtype = 'octet-stream'
    text_message = email.mime.text.MIMEText(text_content)
    message.attach(text_message)
    if file_name != None:
        fp = open(file_name, "rb")
        file_message = email.mime.base.MIMEBase(maintype, subtype)
        file_message.set_payload(fp.read())
        fp.close()
        email.encoders.encode_base64(file_message)
        message.add_header('Content-Disposition', 'attachment', filename=file_name)
        message.attach(file_message)
    composed = message.as_string()
    return composed

def main():
    fromaddr = 'user_me@gmail.com'
    toaddrs  = 'user_you@gmail.com'
    msg = create_message('Why,Oh why!', __file__)
    username = 'bcoe'
    password = 'foobar'
    server = smtplib.SMTP_SSL('127.0.0.1:8465')
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()
    
if __name__ == '__main__':
    main()
    