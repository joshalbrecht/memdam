
"""Send a test email to the local server"""

import smtplib

def main():
    fromaddr = 'user_me@gmail.com'
    toaddrs  = 'user_you@gmail.com'
    msg = 'Why,Oh why!'
    username = 'bcoe'
    password = 'foobar'
    server = smtplib.SMTP_SSL('127.0.0.1:8465')
    server.login(username,password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()
    
if __name__ == '__main__':
    main()