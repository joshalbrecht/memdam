
import tempfile
import subprocess

import memdam.common.event
import memdam.recorder.collector.collector

class WebcamCollector(memdam.recorder.collector.collector.Collector):
    '''
    Collects snapshots from webcam by using external universal (osx) binary wacaw
    '''

    def _collect(self, limit):
        _, screenshot_file = tempfile.mkstemp('')
        #TODO: when packaging, make this path correct...
        command = './bin/wacaw %s && mv %s.jpeg %s.jpg' % (screenshot_file, screenshot_file, screenshot_file)
        subprocess.check_call(command, shell=True)
        screenshot_file += '.jpg'
        screenshot = self._save_file(screenshot_file, consume_file=True)
        return [memdam.common.event.new(u'com.memdam.webcam', data__file=screenshot)]
