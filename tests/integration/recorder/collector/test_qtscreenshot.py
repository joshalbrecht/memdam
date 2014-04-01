
import nose.tools

import memdam.recorder.collector.qtscreenshot
import tests.integration.recorder.collector

class TestScreenshots(tests.integration.recorder.collector.CollectorTestHarness):
    def __init__(self, *args, **kwargs):
        config = dict()
        tests.integration.recorder.collector.CollectorTestHarness.__init__(
            self,
            memdam.recorder.collector.qtscreenshot.ScreenshotCollector,
            config,
            *args,
            **kwargs
        )

    def runTest(self):
        from PyQt4.QtGui import QApplication
        app = QApplication([])
        events = self.collector._snapshot_func()
        nose.tools.eq_(len(events), 1)
