
"""
A daemon that will collect and transmit events for as many types of data as possible.
"""

import logging

import apscheduler.scheduler

import memdam.common.event
import memdam.common.timeutils
import memdam.common.parallel
import memdam.recorder.config
import memdam.recorder.collector.collector
import memdam.recorder.mailqueue
import memdam.recorder.eventqueue

class SystemStats(memdam.recorder.collector.collector.Collector):
    """
    A simple collector for statistics like CPU usage, memory usage, I/O events, etc
    """

    def collect(self):
        return [memdam.common.event.Event(memdam.common.timeutils.now(), "com.memdam.cpu", cpu__number__percent=0.2)]

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

    #create the queues
    mail_queue = memdam.recorder.mailqueue.MailQueue(num_workers, to_addresses, smtp_address)
    eventQueue = memdam.recorder.eventqueue.EventQueue(device, mail_queue)

    #schedule various collectors
    sched = apscheduler.scheduler.Scheduler(standalone=True)

    #TODO: schedule a bunch of collectors based on the config
    collector = SystemStats(config)
    collector.start()
    def collect():
        """Scheduler only calls functions without arguments"""
        eventQueue.collect_events(collector)
    sched.add_cron_job(collect, second='0,10,20,30,40,50')

    #processes the events periodically
    sched.add_cron_job(eventQueue.process_events, second='0,30')

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
