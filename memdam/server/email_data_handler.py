
"""
Emails should be sent in the following format. All characters are literals except (name), which means that the named value (see below) should be substituted there and {}'s, which enclose regular expressions. Any {} or () characters in the regex will be escaped iff they are not being used to mean something special.

From: (device_name)
To: {.*}
Date: (datetime)
Subject: [memdam] [(device_name)] (unique_id){\( [(part_num)/(total_parts)]\)|}{.*}
Body: {.*}

Descriptions of variables:

data_type: a type of data. matches {[A-Za-z_0-9\.]+}  Heirachies can be formed using '.' characters (ex: com.random_company_name.product_name.heartbeats_per_century, using reverse tld standard like java)
device_name: the name of the device where the event was recorded. Same allowable characters and heirachy as data_type (ex: computer_name.camera_4)
datetime: time of last event, second accuracy, includes timestamp. Actual times should be taken 
unique_id: a unique identifier (UUID in standard format) for the event.
part_num: 1-indexed part numbers, for files that are too large to transfer as one big piece. Client should choose a size for splitting that is the minimum of the max supported size on the server, and at the client level. Server will respond with SIZE header to EHLO if it has a max size.
total_parts: total number of parts that will be transmitted for this unique_id. Note that the data will only be available once all parts are sent. Parts may be sent in any order.

Other restrictions:

Subject: is just generated. Try not to pull information out of it.
Body: should be formatted as json. Specifically, it must be a non-empty map of data_type (as described above) -> a list of json-encoded events.
Attachments: There should be only one. It should be named like this: (unique_id){\(-(part_num)-(total_parts)\)\{0,1\}}.(extension))
where extension does a half-decent job of identifying the type of content


"""

import email

import secure_smtpd

class EmailDataHandler(secure_smtpd.SMTPServer):
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
        self.users = {username: UserData("/tmp/")}
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        message = email.message_from_string(data)
        import pdb; pdb.set_trace()
        
    
    