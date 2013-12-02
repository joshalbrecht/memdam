
import types
import multiprocessing

import memdam.common.error
import memdam.common.poisonpill
import memdam.common.parallel
import memdam.recorder.collector.collector

class UniqueIdCollector(memdam.recorder.collector.collector.Collector):
    """
    Collects events by watching sources that have a list of unique ids (which can be either strings
    or integers but probably NOT longs, since those will exceed the max length for json)

    Subclasses MUST call launch() before the first call to collect!

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

    def __init__(self, config, state_store):
        memdam.recorder.collector.collector.Collector.__init__(self, config, state_store)
        self._ids_already_generated = set(self._state_store.get_state()['finished'])
        self._new_id_queue = multiprocessing.Queue()
        self._id_queue = multiprocessing.Queue()
        self._event_queue = multiprocessing.Queue()
        self._control_strand = None
        self._finished_message_ids = set()
        self._worker_strands = []
        self._id_collector = None
        self._id_collector_kwargs = None
        self._id_processor = None
        self._id_processor_kwargs = None
        self._shutting_down = False
        #TODO: make these configurable
        self._num_workers = 4
        #note: the queue is not ACTUALLY limited in size, so that we can insert poison pills without
        #blocking, and this way is easier. It will NEVER be larger than:
        #self._max_event_queue_size + 2 * self._num_workers
        self._max_event_queue_size = 100

    def launch(self, id_collector, id_collector_kwargs, id_processor, id_processor_kwargs):
        """
        Subclasses MUST call this before the first call to collect()!

        Starts the control and worker threads.
        """
        self._id_collector = id_collector
        self._id_collector_kwargs = id_collector_kwargs
        self._id_processor = id_processor
        self._id_processor_kwargs = id_processor_kwargs

        self._control_strand = self._launch_id_collector_strand()
        for i in range(0, self._num_workers):
            #TODO: parameterize whether these are processes or strands
            strand = memdam.common.parallel.create_strand(
                "%s_worker_%s" % (str(self.__class__), i),
                _collect_unique_event,
                args=(
                    self._max_event_queue_size,
                    self._id_queue,
                    self._event_queue,
                    self._id_processor,
                    self._id_processor_kwargs
                    )
                )
            strand.start()
            self._worker_strands.append(strand)

    def collect(self, limit):
        assert self._id_collector != None, "Subclasses MUST call launch() before the first call to collect()! (%s failed this contract)" % (self)

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
        # pylint: disable=W0612
        for i in range(0, self._num_workers):
            message = memdam.common.poisonpill.PoisonPill()
            self._id_queue.put_nowait(message)
        for worker in self._worker_strands:
            worker.join()

        #after everything is done, deal with the queues
        self._id_queue.close()
        self._id_queue.join_thread()
        self._event_queue.close()
        self._event_queue.join_thread()

    #TODO: go be consistent about the usage and definition of strand
    def _launch_id_collector_strand(self):
        """
        Starts a strand to collect unique ids.
        Only one of these should be running at once.
        :returns: the strand, already started
        :rtype: strand
        """
        #pull all of the ids that were evaluated last time, and make sure we don't add them again
        new_ids = memdam.common.parallel.read_all_from_queue(self._new_id_queue)
        for new_id in new_ids:
            self._ids_already_generated.add(new_id)

        #TODO: parameterize whether these are processes or strands
        #start a controller strand with a reference to the queue into which ids should be inserted
        strand = memdam.common.parallel.create_strand(
            str(self.__class__) + "_main_strand",
            _collect_unique_ids,
            args=(self._ids_already_generated, self._new_id_queue, self._id_queue, self._id_collector, self._id_collector_kwargs),
        )
        strand.start()
        return strand

def _collect_unique_ids(ids_already_generated, new_id_queue, id_queue, collector, collector_kwargs):
    """
    Call the collector with the set of ids that were already generated.
    The collector will generate a list of ids that should be added to the queue.
    These should be merged with the previous set of ids and passed in on the next call, so we use
    another queue (new_id_queue) to remember which things were new for the next call
    """
    # pylint: disable=W0142
    new_ids = collector(ids_already_generated, **collector_kwargs)
    for new_id in new_ids:
        new_id_queue.put_nowait(new_id)
        id_queue.put_nowait(new_id)

def _collect_unique_event(max_event_queue_size, id_queue, event_queue, processor, processor_kwargs):
    """
    While the event queue is not full, collect events based on unique ids.
    Will run in its own strand.
    """
    while event_queue.size() < max_event_queue_size:
        unique_id = id_queue.get()
        try:
            # pylint: disable=W0142
            events = processor(unique_id, **processor_kwargs)
            for event in events:
                event_queue.put(event)
        # pylint: disable=W0703
        except Exception, e:
            memdam.common.error.report(e)
