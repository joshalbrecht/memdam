
"""Runs the SMTP server"""

import asyncore
import ssl

import secure_smtpd

class DebuggingServer(secure_smtpd.SMTPServer):
    def __init__(self, listenAddress):
        secure_smtpd.SMTPServer.__init__(self,
            listenAddress,
            None,
            require_authentication=True,
            ssl=True,
            certfile='/home/cow/memdam/lib/secure-smtpd/examples/server.crt',
            keyfile='/home/cow/memdam/lib/secure-smtpd/examples/server.key',
            credential_validator=secure_smtpd.FakeCredentialValidator(),
            process_count=None)
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        inheaders = 1
        lines = data.split('\n')
        print '---------- MESSAGE FOLLOWS ----------'
        for line in lines:
            # headers first
            if inheaders and not line:
                print 'X-Peer:', peer[0]
                inheaders = 0
            print line
        print '------------ END MESSAGE ------------'

def main(listenAddress):
    DebuggingServer(listenAddress)
    asyncore.loop()
    
if __name__ == '__main__':
    #main(('0.0.0.0', 465))
    main(('0.0.0.0', 8465))
