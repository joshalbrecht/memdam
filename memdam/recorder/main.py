
'''
A daemon that will collect and transmit events for as many types of data as possible.
'''

import sys
import os
import logging
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
import memdam.recorder.state
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

@memdam.tracer
def all_collectors():
    '''
    :returns: a list of all of all collectors that are possibly supported by this operating system
    '''
    collectors = [memdam.recorder.collector.systemstats.SystemStats,
                  memdam.recorder.collector.qtscreenshot.ScreenshotCollector]
    if memdam.common.utils.is_windows():
        collectors += []
    elif memdam.common.utils.is_osx():
        collectors += [memdam.recorder.collector.osx.webcam.WebcamCollector]
    else:
        collectors += [memdam.recorder.collector.linux.webcam.WebcamCollector]
    return tuple(collectors)

@memdam.tracer
def schedule(sched, collector, interval):
    '''
    Schedules a collector to be called at a particular interval.

    :param sched: the scheduler which should call the collector at the particular interval.
    :type  sched: apscheduler.scheduler.Scheduler
    :param collector: the particular collector that should be called at the given interval
    :type  collector: memdam.recorder.collector.collector.Collector
    :param interval: arguments to be passed as keyward arguments to the add_cron_job method of the
    scheduler
    :type  interval: dict(string -> string)
    '''
    def collect():
        '''Scheduler only calls functions without arguments'''
        memdam.log.debug("Collecting events from %s" % (collector))
        collector.collect_and_persist(1)
    sched.add_cron_job(collect, **interval)

@memdam.tracer
def create_collectors(sched, config, state_folder, eventstore, blobstore):
    '''Schedule a bunch of collectors based on the config'''
    collectors = []
    for collector_class in all_collectors():
        collector_name = collector_class.__name__
        collector_config = config.get('collectors').get(collector_name, None)
        if collector_config is not None:
            state_file = os.path.join(state_folder, collector_name + '.json')
            state_store = memdam.recorder.state.StateStore(state_file)
            collector = collector_class(config=collector_config,
                                        state_store=state_store,
                                        eventstore=eventstore,
                                        blobstore=blobstore)
            interval = collector_config.get('interval')
            schedule(sched, collector, interval)
            collectors.append(collector)
    assert len(collectors) > 0, "Should really probably configure at least SOME collectors..."
    return collectors

@memdam.tracer
def run(user, config):
    '''Run the daemon. Blocks.'''

    if not memdam.is_threaded_logging_setup():
        handlers = [memdam.STDOUT_HANDLER]
        log_level_name = config.get(u'log_level')
        if log_level_name == 'TRACE':
            log_level = memdam.TRACE
        else:
            log_level = getattr(logging, log_level_name)
            assert 'TRACE_FILE' not in os.environ, 'Don\'t set TRACE_FILE without changing the log level!'
        memdam.common.parallel.setup_log('mainlog', level=log_level, handlers=handlers)
        #TODO: why do I need this? :( wtf is adding this handler? my guess is that it's apscheduler...
        #see this for slightly more reasonable options:
        #http://docs.python.org/2/howto/logging.html#configuring-logging
        logging.getLogger().removeHandler(logging.getLogger().handlers[0])

    memdam.log.info(config.format_for_log())

    local_folder = config.get(u'data_folder')
    username = config.get(u'username')
    password = config.get(u'password')
    server_url = config.get(u'server_url')

    #create both local and remote blob and event stores
    local_blob_folder = os.path.join(local_folder, "blobs")
    local_event_folder = os.path.join(local_folder, "events")
    state_folder = os.path.join(local_folder, "state")
    #TODO: remember to clear these for testing probably...
    for folder in (local_event_folder, local_blob_folder, state_folder):
        if not os.path.exists(folder):
            os.makedirs(folder)

    client = memdam.common.client.MemdamClient(server_url, username, password)
    local_blobs = memdam.blobstore.localfolder.Blobstore(local_blob_folder)
    remote_blobs = memdam.blobstore.https.Blobstore(client)
    local_events = memdam.eventstore.sqlite.Eventstore(local_event_folder)
    remote_events = memdam.eventstore.https.Eventstore(client)

    #schedule various collectors
    sched = apscheduler.scheduler.Scheduler(standalone=True)
    collectors = create_collectors(sched, config, state_folder, local_events, local_blobs)

    #start the synchronizer in the background
    synchronizer = memdam.recorder.sync.Synchronizer(local_events, remote_events, local_blobs, remote_blobs)

    #start the scheduler in the background
    strand = memdam.common.parallel.create_strand("scheduler", sched.start, use_process=False)

    @memdam.tracer
    def start_collectors():
        '''Starts all of the actual processing threads'''
        for collector in collectors:
            collector.start()
        synchronizer.start()
        strand.start()

    @memdam.tracer
    def clean_shutdown():
        '''Call this to cancel all of the workers and exit cleanly'''
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

@memdam.tracer
def run_as_script():
    '''Parses commandline arguments, converting them into the appropriate config variables'''
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
            collector_config = {}
            for collector_class in all_collectors():
                collector_name = collector_class.__name__
                #TODO: abstract the default collector configuration a bit...
                #really how this should work is that collector should have a default configuration,
                #then each subclass should have a default configuration, and THEN the user overrides
                #should occur. This way we don't have to serialize so much of the configuration.
                #when new collectors are added, just ask people if they want to add them (post-upgrade)
                #when new keys are added to configurations, it should work out fine (will be added to one of the two defaults)
                #if keys are renamed or deleted, need to have a migration step that loads the config, looks for things that are gone, and warns/renames
                collector_config[collector_name] = dict(interval=dict(second='0,10,20,30,40,50'))
            user.create_initial_config(config_file, collector_config)
    config = memdam.recorder.config.Config(config_file)
    run(user, config)

if __name__ == '__main__':
    run_as_script()
