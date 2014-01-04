
import multiprocessing

import memdam.common.parallel
import memdam.common.poisonpill

class PollingWorkManager(object):
    """
    Has a main thread, a queue, and a bunch of workers
    """

    def __init__(self, name, work_generator_func, work_consumer_func, **kwargs):
        self._manager = multiprocessing.Manager()
        self._pool_queue = self._manager.Queue()
        if 'args' not in kwargs:
            kwargs['args'] = []
        num_workers = kwargs.get('num_workers', 4)
        if 'num_workers' in kwargs:
            del kwargs['num_workers']
        original_args = kwargs['args']
        kwargs['args'] = [self._pool_queue] + original_args
        self._pool = [
                memdam.common.parallel.create_strand(
                    name=name + "-worker-" + str(x), target=work_consumer_func,
                    **kwargs) \
            for x in range(0, num_workers)]
        self._master_queue = self._manager.Queue()
        kwargs['args'] = [self._master_queue] + kwargs['args']
        self._main_strand = memdam.common.parallel.create_strand(
                    name=name + "-master", target=work_generator_func,
                    **kwargs)

    def start(self):
        for process in self._pool:
            process.start()
        self._main_strand.start()

    def stop(self):
        memdam.log.debug("Adding PoisonPills")
        for i in range(0, len(self._pool)):
            self._pool_queue.put(memdam.common.poisonpill.PoisonPill())
        self._master_queue.put(memdam.common.poisonpill.PoisonPill())
        for process in self._pool + [self._main_strand]:
            memdam.log.info("Waiting for %s" % (process))
            process.join()
            if process.exitcode != 0:
                memdam.log.warn("Unclean worker exit: " + str(process.exitcode))
        memdam.log.trace("Closing queues")
        #for queue in (self._master_queue, self._pool_queue):
        #    queue.close()
        #    queue.join_thread()
