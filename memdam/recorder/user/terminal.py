
import time

import memdam.common.utils
import memdam.recorder.user.api
import memdam.recorder.application

class User(memdam.recorder.user.api.User):
    """
    Just interact with the user from the terminal instead of requiring qt4
    """

    def prompt_user(self, prompt_text):
        print prompt_text
        return raw_input()

    def main_loop(self, start, shutdown):
        start()
        while True:
            time.sleep(10.0)
        shutdown()
