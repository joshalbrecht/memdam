
"""
A daemon that will collect and transmit events for as many types of data as possible.
"""

import os
import logging

import apscheduler.scheduler

import memdam.common.event
import memdam.common.timeutils
import memdam.common.parallel
import memdam.common.error
import memdam.common.client
import memdam.blobstore.localfolder
import memdam.blobstore.https
import memdam.eventstore.sqlite
import memdam.eventstore.https
import memdam.recorder.config
import memdam.recorder.collector.collector
import memdam.recorder.sync

#TODO: probably shouldn't do this, needed config
import memdam.server.web.urls

class SystemStats(memdam.recorder.collector.collector.Collector):
    """
    A simple collector for statistics like CPU usage, memory usage, I/O events, etc
    """

    def collect(self, blobstore, limit):
        return [memdam.common.event.new(u"com.memdam.cpu", cpu__number__percent=0.2)]

def main():
    """Run the daemon. Blocks."""

    #TODO: actually read some configuration
    configFile = "/home/cow/temp.json"
    local_folder = "/tmp"
    #TODO: in general, collectors should probably take a device
    device = "pretendThatThisIsAUUID"
    config = memdam.recorder.config.Config(configFile)

    handlers = [memdam.STDOUT_HANDLER]
    memdam.common.parallel.setup_log("mainlog", level=logging.DEBUG, handlers=handlers)

    #create both local and remote blob and event stores
    local_blob_folder = os.path.join(local_folder, "blobs")
    local_event_folder = os.path.join(local_folder, "events")
    #TODO: remember to clear these for testing probably...
    for folder in (local_event_folder, local_blob_folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
    username = memdam.server.web.urls.app.config["USERNAME"]
    password = memdam.server.web.urls.app.config["PASSWORD"]
    server_url = "http://127.0.0.1:5000/api/v1/"
    client = memdam.common.client.MemdamClient(server_url, username, password)
    local_blobs = memdam.blobstore.localfolder.Blobstore(local_blob_folder)
    remote_blobs = memdam.blobstore.https.Blobstore(client)
    local_events = memdam.eventstore.sqlite.Eventstore(local_event_folder)
    remote_events = memdam.eventstore.https.Eventstore(client)

    #schedule various collectors
    sched = apscheduler.scheduler.Scheduler(standalone=True)

    #TODO: schedule a bunch of collectors based on the config
    collector = SystemStats(config)
    collector.start()
    def collect():
        """Scheduler only calls functions without arguments"""
        collector.collect_and_persist(local_events, local_blobs)
    sched.add_cron_job(collect, second='0,10,20,30,40,50')

    synchronizer = memdam.recorder.sync.Synchronizer(local_events, remote_events, local_blobs, remote_blobs)
    synchronizer.start()

    try:
        #run until the exit signal has been recieved
        sched.start()
    except Exception, e:
        #stopd scheduling the collection of more events
        sched.shutdown()
        #stop each collector
        collector.stop()
        #stop synchronizing everything
        synchronizer.stop()
        #TODO: cleaner shutdown. Figure out what exception type this is
        raise e

if __name__ == '__main__':
    main()
