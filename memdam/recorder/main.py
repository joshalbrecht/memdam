
"""
A daemon that will collect and transmit events for as many types of data as possible.
"""

import sys
import os
import logging
import time
import argparse

import apscheduler.scheduler

import memdam.common.utils
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
import memdam.recorder.collector.systemstats
import memdam.recorder.collector.qtscreenshot
import memdam.recorder.sync
import memdam.recorder.application

if memdam.common.utils.is_windows():
    pass
elif memdam.common.utils.is_osx():
    import memdam.recorder.collector.osx.webcam
else:
    import memdam.recorder.collector.linux.webcam

import memdam.recorder.user.terminal
try:
    import memdam.recorder.user.qtgui
except ImportError, e:
    pass

def all_collectors():
    collectors = [memdam.recorder.collector.systemstats.SystemStats,
                  memdam.recorder.collector.qtscreenshot.ScreenshotCollector]
    if memdam.common.utils.is_windows():
        collectors += []
    elif memdam.common.utils.is_osx():
        collectors += [memdam.recorder.collector.osx.webcam.WebcamCollector]
    else:
        collectors += [memdam.recorder.collector.linux.webcam.WebcamCollector]
    return tuple(collectors)

def schedule(sched, collector):
    def collect():
        """Scheduler only calls functions without arguments"""
        memdam.log.debug("Collecting events from %s" % (collector))
        collector.collect_and_persist(1)
    sched.add_cron_job(collect, second='0,10,20,30,40,50')

def create_collectors(sched, collector_kwargs):
    collectors = []
    for collector_class in all_collectors():
        collector = collector_class(**collector_kwargs)
        schedule(sched, collector)
        collectors.append(collector)
    return collectors

def run(user, config):
    """Run the daemon. Blocks."""
    local_folder = config.get(u'data_folder')
    username = config.get(u'username')
    password = config.get(u'password')
    server_url = config.get(u'server_url')

    if not memdam.is_threaded_logging_setup():
        handlers = [memdam.STDOUT_HANDLER]
        memdam.common.parallel.setup_log("mainlog", level=logging.DEBUG, handlers=handlers)

    #create both local and remote blob and event stores
    local_blob_folder = os.path.join(local_folder, "blobs")
    local_event_folder = os.path.join(local_folder, "events")
    #TODO: remember to clear these for testing probably...
    for folder in (local_event_folder, local_blob_folder):
        if not os.path.exists(folder):
            os.makedirs(folder)

    client = memdam.common.client.MemdamClient(server_url, username, password)
    local_blobs = memdam.blobstore.localfolder.Blobstore(local_blob_folder)
    remote_blobs = memdam.blobstore.https.Blobstore(client)
    local_events = memdam.eventstore.sqlite.Eventstore(local_event_folder)
    remote_events = memdam.eventstore.https.Eventstore(client)

    #schedule various collectors
    sched = apscheduler.scheduler.Scheduler(standalone=True)

    #TODO: schedule a bunch of collectors based on the config
    collector_kwargs = dict(config=config, state_store=None, eventstore=local_events, blobstore=local_blobs)
    collectors = create_collectors(sched, collector_kwargs)

    #start the synchronizer in the background
    synchronizer = memdam.recorder.sync.Synchronizer(local_events, remote_events, local_blobs, remote_blobs)

    #start the scheduler in the background
    strand = memdam.common.parallel.create_strand("scheduler", sched.start, use_process=False)

    def start_collectors():
        """Starts all of the actual processing threads"""
        for collector in collectors:
            collector.start()
        synchronizer.start()
        strand.start()

    def clean_shutdown():
        """Call this to cancel all of the workers and exit cleanly"""
        #stop scheduling the collection of more events
        sched.shutdown()
        #stop each collector
        for collector in collectors:
            collector.stop()
        #stop synchronizing everything
        synchronizer.stop()
        #TODO: cleaner shutdown. Figure out what exception type this is
        memdam.shutdown_log()

    try:
        sys.exit(user.main_loop(start_collectors, clean_shutdown))
    except Exception, e:
        import traceback
        traceback.print_exc(e)
        clean_shutdown()
        raise

def run_as_script():
    """Parses commandline arguments, converting them into the appropriate config variables"""
    parser = argparse.ArgumentParser(description='Run the chronographer server.')
    parser.add_argument('--config', dest='config', type=str,
                        help='the path to a file with additional configuration')
    parser.add_argument('--terminal', dest='terminal', type=bool,
                        help='indicates that this should run without the gui')
    args, unknown = parser.parse_known_args()
    if len(unknown) > 1:
        raise Exception("Invalid argument!" + str(unknown))
    elif len(unknown) == 1:
        if not unknown[0].startswith('-psn_'):
            raise Exception("Invalid arguments: " + str(unknown))
    if args.terminal:
        user = memdam.recorder.user.terminal.User()
    else:
        user = memdam.recorder.user.qtgui.User()
    config_file = args.config
    if config_file == None:
        config_folder = os.path.join(os.path.expanduser('~'), u'.chronographer')
        if not os.path.exists(config_folder):
            os.makedirs(config_folder)
        config_file = os.path.join(config_folder, u'config.json')
        if not os.path.exists(config_file):
            user.create_initial_config(config_file)
    config = memdam.recorder.config.Config(config_file)
    run(user, config)

if __name__ == '__main__':
    run_as_script()
