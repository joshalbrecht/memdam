
import types
import multiprocessing

import memdam.common.poisonpill
import memdam.common.parallel
import memdam.recorder.collector.collector

class UniqueIdCollector(memdam.recorder.collector.collector.Collector):
    """
    Collects events by watching sources that have a list of unique ids (which can be either strings
    or integers but probably NOT longs, since those will exceed the max length for json)

    Runs on the same schedule as the regular collector (so that should probably be relatively
    infrequently for most services, to prevent being blocked for rate-limiting reasons)

    Runs a controller strand that periodically collects all unique ids, and some worker strands for
    working through those new ids to generate the correct events.

    The id_processor function will only be called when there is sufficient room in subsequent queues
    for the resulting event. This allows for backpressure in the system, so that downstream event
    queues are not overwhelmed.

    Subclasses are responsible for throttling requests to any external service appropriately.

    :attr _id_collector: a globally accessible (top level) function for collecting unique ids.
    must take kwargs for any configuration, and a single arg that is the id_queue
    :type _id_collector: function
    """

    def __init__(self, id_collector, id_collector_kwargs, id_processor, id_processor_kwargs, config, state_store):
        memdam.recorder.collector.collector.Collector.__init__(self, config, state_store)
        self._id_queue = multiprocessing.Queue()
        self._event_queue = multiprocessing.Queue()
        self._control_strand = None
        self._finished_message_ids = set()
        self._worker_strands = []
        self._id_collector = id_collector
        self._id_collector_kwargs = id_collector_kwargs
        self._id_processor = id_processor
        self._id_processor_kwargs = id_processor_kwargs
        #TODO: make configurable
        self._num_workers = 4
        self._shutting_down = False

    def start(self):
        self._control_strand = self._launch_id_collector_strand()
        for i in range(0, self._num_workers):
            strand = memdam.common.parallel.create_strand(
                "%s_worker_%s" % (str(self.__class__), i),
                self._id_processor,
                args=(self._id_queue, self._event_queue),
                kwargs=self._id_processor_kwargs)
            strand.start()
            self._worker_strands.append(strand)

    def collect(self, limit):
        #if the strand finished, start it up again
        if not self._control_strand.is_alive():
            self._control_strand.join()
            if not self._shutting_down:
                self._control_strand = self._launch_id_collector_strand()

        #empty the queue
        eventPairs = memdam.common.parallel.read_all_from_queue(self._event_queue, max_size=limit)

        #remember the unique ids to be persisted in our state_store when post_collect is called
        for pair in eventPairs:
            unique_id = pair[0]
            assert isinstance(unique_id , types.IntType) or isinstance(unique_id , types.StringType)
            self._finished_message_ids.add(unique_id)

        #simply return all of the events
        events = [x[1] for x in eventPairs]
        return events

    def post_collect(self):
        #when events are pulled out of the strand, those unique ids are remembered in
        #_finished_message_ids. The fact that those ids have been finished should be persisted only
        #after the events have been pulled out and persisted into the event queue and since this
        #function is called after the events are safely persisted somewhere else, this is the
        #appropriate place to do that :)
        current_state = self._state_store.get_state()
        previously_finished_messages = set(current_state['finished'])
        all_finished_messages = self._finished_message_ids.union(previously_finished_messages)
        current_state['finished'] = list(all_finished_messages)
        self._state_store.set_state(current_state)
        self._finished_message_ids.clear()

    def stop(self):
        #cleanly shutdown the main strand
        self._shutting_down = True
        self._control_strand.join()

        #shutdown workers with memdam.common.poisonpill.PoisonPill's
        for i in range(0, self._num_workers):
            message = memdam.common.poisonpill.PoisonPill()
            self._id_queue.put_nowait(message)
        for worker in self._worker_strands:
            worker.join()

        #TODO: after everything is done, deal with the queues
        #TODO: hmmm...  how to implement feedback and pushback, so that we don't have huge buffers?

    #TODO: go be consistent about the usage and definition of strand
    def _launch_id_collector_strand(self):
        """
        Starts a strand to collect unique ids.
        Only one of these should be running at once.
        :returns: the strand, already started
        :rtype: strand
        """
        #TODO: parameterize whether these are processes or strands
        #start a controller strand with a reference to the queue into which ids should be inserted
        strand = memdam.common.parallel.create_strand(
            str(self.__class__) + "_main_strand",
            self._id_collector,
            args=(self._id_queue,),
            kwargs=self._id_collector_kwargs)
        strand.start()
        #Value('i', initval)
        return strand
