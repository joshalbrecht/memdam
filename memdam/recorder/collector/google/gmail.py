
import email
import imaplib

import memdam.recorder.collector.uniqueidcollector

_MAIL_CODE = 'M'
_CHAT_CODE = 'C'
_MAIL_FOLDER = '[Gmail]/All Mail'
_CHAT_FOLDER = '[Gmail]/Chats'
_CONTACT_INFO_NAMESPACE = "com.memdam.social.people.contact.unique"
_EMAIL_NAMESPACE = "com.memdam.social.communication.email"
_IM_NAMESPACE = "com.memdam.social.communication.im"

class GmailCollector(memdam.recorder.collector.uniqueidcollector.UniqueIdCollector):
    """
    Collects the following information types from gmail:

    com.memdam.social.communication.email
    com.memdam.social.communication.im
    com.memdam.social.people.contact
    """

    def __init__(self, config, state_store):
        memdam.recorder.collector.uniqueidcollector.UniqueIdCollector.__init__(
            self,
            config,
            state_store
        )

    def start(self):
        kwargs = {'config': self._config,}
        memdam.recorder.collector.uniqueidcollector.UniqueIdCollector.launch(
            self,
            _collector,
            kwargs,
            _processor,
            kwargs
        )

class GmailConnection(object):
    """
    An IMAP connection to Gmail.
    """

    def __init__(self, config):
        self._config = config
        self._imap = imaplib.IMAP4_SSL('imap.gmail.com')
        username = self._config['username']
        password = self._config['password']
        self._imap.login(username, password)

    def generate_all_ids(self):
        """
        :returns: a set of all ids for all emails and chats from google
        :rtype: set(string)
        """
        mail_ids = self._generate_all_ids_from_folder(_MAIL_FOLDER, _MAIL_CODE)
        chat_ids = self._generate_all_ids_from_folder(_CHAT_FOLDER, _CHAT_CODE)
        return mail_ids + chat_ids

    def _generate_all_ids_from_folder(self, folder, code):
        """
        Generate a list of ids for a gmail IMAP folder
        """
        #select the folder with all mail (read-only)
        self._imap.select(folder, True)
        #search for everything
        result = self._imap.search(None, 'ALL')
        assert result[0] == 'OK'
        id_list = result[1][0]
        all_ids = [code + x for x in id_list.split(" ")]
        #return the list of all ids
        return all_ids

    def create_events(self, mail_id):
        """
        :returns: all events from this email
        :rtype: list(memdam.common.event.Event)
        """

        memdam.log().debug("Reading message %s", mail_id)
        current_code = mail_id[0]
        message_id = int(mail_id[1:])
        assert current_code in (_MAIL_CODE, _CHAT_CODE)
        if current_code == _MAIL_CODE:
            folder = _MAIL_FOLDER
        else:
            folder = _CHAT_FOLDER

        memdam.log().debug("Reading from %s", folder)
        self._imap.select(folder, True)
        message_response = self._imap.fetch(message_id, '(RFC822)')

        memdam.log().debug("Parsing server response: %s", message_response)
        message_string = message_response[1][0][1]
        message = email.message_from_string(message_string)

        events = []
        if _CONTACT_INFO_NAMESPACE in self._config['namespaces']:
            events += self._create_contact_info_events(message)
        if _EMAIL_NAMESPACE in self._config['namespaces']:
            if current_code == _MAIL_CODE:
                events += self._create_email_events(message)
        if _IM_NAMESPACE in self._config['namespaces']:
            if current_code == _CHAT_CODE:
                events += self._create_im_events(message)
        return events

    def _create_email_events(self, message):
        """
        """
        basic_event = self._create_basic_message_event(message)
        #pull out attachments as files in temp workspace
        #pull out other useful fields (bcc, cc, subject, thread id, any other headers)
        #parse out main searchable text body
        return [basic_event]

    def _create_im_events(self, message):
        """
        """
        basic_event = self._create_basic_message_event(message)
        #chats (via imap) really have (at least) two formats--a text/html one and a  multipart/alternative -> text/html one
        #the first one seems to be single messages, and happen later
        #the second one has  abunch of back and forth messages smushed together and should probably be separated
        #except that separating these is kinda hard... have to parse for "me" and the other name, and map using the email header I guess...
        #also have to parse out the time stamps from the html and email and use that to get actual time stamps
        #maybe look at the xml ones to see if the information is any easier to separate?
        return [basic_event]

    def _create_basic_message_event(self, message):
        #labels
        #from
        #to
        #date / time
        #full message field
        return event

    def _create_contact_info_events(self, message):
        """
        """
        #pull out from and to fields by requesting ONLY the headers
        #create a mapping event for each
        return []

def _collector(finished, config=None):
    """
    Called periodically to collect all new unique ids.
    """
    connection = GmailConnection(config)
    all_ids = connection.generate_all_ids()
    filtered_ids = [new_id for new_id in all_ids if new_id not in finished]
    return filtered_ids

def _processor(mail_id, config=None):
    """
    :returns: all events from this email
    :rtype: list(memdam.common.event.Event)
    :throws: an Exception if anything went wrong related to this specific email (email deleted, etc)
    """
    connection = GmailConnection(config)
    return connection.create_events(mail_id)
