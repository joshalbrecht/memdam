import logging

import rumps

import memdam.common.parallel
import memdam.recorder.main

class Capture(rumps.App):
    def __init__(self):
        super(Capture, self).__init__("Capture")
        self.menu = ["Preferences", "Pause"]

    @rumps.clicked("Preferences")
    def prefs(self, sender):
        rumps.alert("todo")

    @rumps.clicked("Pause")
    def pause(self, _):
        rumps.alert("todo")

if __name__ == "__main__":
    handlers = [memdam.STDOUT_HANDLER]
    memdam.common.parallel.setup_log("mainlog", level=logging.DEBUG, handlers=handlers)
    strand = memdam.common.parallel.create_strand("chronographer_main", memdam.recorder.main.main)
    strand.start()
    Capture().run()
