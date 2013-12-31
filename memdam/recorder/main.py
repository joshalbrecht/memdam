
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
import memdam.blobstore.localfolder
import memdam.blobstore.https
import memdam.eventstore.sqlite
import memdam.eventstore.https
import memdam.recorder.config
import memdam.recorder.collector.collector

class SystemStats(memdam.recorder.collector.collector.Collector):
    """
    A simple collector for statistics like CPU usage, memory usage, I/O events, etc
    """

    def collect(self):
        return [memdam.common.event.new("com.memdam.cpu", cpu__number__percent=0.2)]

def main():
    """Run the daemon. Blocks."""

    #TODO: actually read some configuration
    configFile = "/home/cow/temp.json"
    device = "pretendThatThisIsAUUID"
    config = memdam.recorder.config.Config(configFile)
    num_workers = 4
    to_addresses = "user@domain.com"
    smtp_address = ('127.0.0.1', 8465)

    handlers = [memdam.STDOUT_HANDLER]
    memdam.common.parallel.setup_log("mainlog", level=logging.DEBUG, handlers=handlers)

    #create both local and remote blob and event stores
    local_blob_folder = os,path.join(local_folder, "blobs")
    local_event_folder = os,path.join(local_folder, "events")
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

    #TODO: actually, probably don't use the schedule for this--just runs continuously at some polling interval
    #main thread pulls things (uuids) into a queue that is consumed by workers
    #use some of the existing code for that

    #processes the events periodically
    def _sync_blobs():
        """Scheduler only calls functions without arguments"""
        sync_blobs(local_blobs, remote_blobs)
    sched.add_cron_job(_sync_blobs, second='0,30')

    try:
        #run until the exit signal has been recieved
        sched.start()
    except Exception, e:
        #stopd scheduling the collection of more events
        sched.shutdown()
        #stop each collector
        collector.stop()
        #finish turning all events into messages and mail them
        eventQueue.process_events()
        #finish mailing everything
        mail_queue.shutdown()
        #TODO: cleaner shutdown. Figure out what exception type this is
        raise e

if __name__ == '__main__':
    main()
