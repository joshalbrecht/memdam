
import nose.tools

import memdam.recorder.collector.linux.webcam
import tests.integration.recorder.collector

class TestWebcam(tests.integration.recorder.collector.CollectorTestHarness):
    def __init__(self, *args, **kwargs):
        config = dict()
        tests.integration.recorder.collector.CollectorTestHarness.__init__(
            self,
            memdam.recorder.collector.linux.webcam.WebcamCollector,
            config,
            *args,
            **kwargs
        )

    def validate(self, result, error=None):
        nose.tools.eq_(error, None)
        nose.tools.eq_(len(result), 1)

if __name__ == '__main__':
    test = TestWebcam()
    test.setUp()
    test.runTest()
    test.tearDown()
