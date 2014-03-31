
import nose.tools

import memdam.recorder.collector.qtscreenshot
import tests.integration.recorder.collector

class TestScreenshots(tests.integration.recorder.collector.CollectorTestHarness):
    def __init__(self):
        config = dict()
        tests.integration.recorder.collector.CollectorTestHarness.__init__(
            memdam.recorder.collector.qtscreenshot.ScreenshotCollector,
            config,
        )

    def validate(self, events, error=None):
        nose.tools.eq_(error, None)
        nose.tools.eq_(len(events), 1)
