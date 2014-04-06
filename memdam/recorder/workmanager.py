
import Queue
import multiprocessing

import memdam.common.error
import memdam.common.parallel
import memdam.common.poisonpill

def _work_consumer_func(worker, queue):
    worker.run(queue)

def _work_generator_func(manager, kill_queue, work_queue):
    manager.run(kill_queue, work_queue)

class PollingWorkManager(object):
    """
    Has a main thread, a queue, and a bunch of workers
    """

    def __init__(self, manager, worker_generator, **kwargs):
        name = self.__class__.__name__
        self._manager = multiprocessing.Manager()
        self._pool_queue = self._manager.Queue()
        num_workers = kwargs.get('num_workers', 4)
        if 'num_workers' in kwargs:
            del kwargs['num_workers']
        self._pool = []
        for i in range(0, num_workers):
            kwargs['args'] = [worker_generator(), self._pool_queue]
            strand = memdam.common.parallel.create_strand(
                    name=name + "-worker-" + str(i), target=_work_consumer_func,
                    **kwargs)
            self._pool.append(strand)
        self._master_queue = self._manager.Queue()
        kwargs['args'] = [manager, self._master_queue, self._pool_queue]
        self._main_strand = memdam.common.parallel.create_strand(
                    name=name + "-master", target=_work_generator_func,
                    **kwargs)

    def start(self):
        for process in self._pool:
            process.start()
        self._main_strand.start()

    def stop(self):
        memdam.log().debug("Adding PoisonPills")
        for i in range(0, len(self._pool)):
            self._pool_queue.put(memdam.common.poisonpill.PoisonPill())
        self._master_queue.put(memdam.common.poisonpill.PoisonPill())
        for process in self._pool + [self._main_strand]:
            memdam.log().info("Waiting for %s" % (process))
            process.join()
            if process.exitcode != 0:
                memdam.log().warn("Unclean worker exit: " + str(process.exitcode))
        memdam.log().trace("Closing queues")

class Worker(object):
    def __init__(self):
        pass

    def run(self, queue):
        while True:
            try:
                records = memdam.common.parallel.read_next_from_queue(queue)
                if len(records) <= 0:
                    break
                self._process(records[0])
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, e:
                memdam.common.error.report(e)

    def _process(self, work_id):
        raise NotImplementedError()

class Manager(object):
    def __init__(self, timeout=1.0):
        self._timeout = timeout

    def run(self, kill_queue, work_queue):
        while True:
            try:
                record = None
                try:
                    record = kill_queue.get(timeout=self._timeout)
                except Queue.Empty:
                    pass
                except EOFError:
                    return
                if record != None and isinstance(record, memdam.common.poisonpill.PoisonPill):
                    return
                work_ids = self._generate_work_ids()
                for work_id in work_ids:
                    work_queue.put(work_id)

            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception, e:
                memdam.common.error.report(e)

    def _generate_work_ids(self):
        raise NotImplementedError()
