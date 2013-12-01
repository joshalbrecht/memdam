
import imaplib

import memdam.recorder.collector.uniqueidcollector

_MAIL_CODE = 'M'
_CHAT_CODE = 'C'

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
        mail_ids = self._generate_all_ids_from_folder('[Gmail]/All Mail', _MAIL_CODE)
        chat_ids = self._generate_all_ids_from_folder('[Gmail]/Chats', _CHAT_CODE)
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

    def create_event(self, mail_id):
        """
        :returns: an event representing this email
        :rtype: memdam.common.event.Event
        """

        #chats (via imap) really have two formats--a text/html one and a  multipart/alternative -> text/html one
        #the first one seems to be single messages, and happen later
        #the second one has  abunch of back and forth messages smushed together and should probably be separated

        #select the folder (read-only)
        #download the email
        #if this is a chat, check that if we care about chats
        #if this is an email, check that we care about emails
        #get all associated labels
        #turn any attachments into files in our temp workspace
        #parse the rest of the fields out of the message or chat
        #return the event

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
    :returns: an event representing this email
    :rtype: memdam.common.event.Event
    :throws: an Exception if anything went wrong related to this specific email (email deleted, etc)
    """
    connection = GmailConnection(config)
    return connection.create_event(mail_id)
