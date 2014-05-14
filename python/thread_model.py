"""A ThreadModel provides concurrency primitives."""

class ThreadModel(object):
    """A ThreadModel is a concurrency provider."""

    def start(self):
        """Initialize the thread model.

        Must be called before any other methods are called.
        """
        pass

    def stop(self):
        """Stop all running processes and return to uninitialized state.

        Signals all running threads / processes to stop and then waits
        for them to complete."""
        pass

    def call(self, func, *args):
        """Runs func, passing arguments *args in a thread.

        Must be called only by threads started by this container."""
        pass

    def callAfter(self, t_secs, func, *args):
        """Schedules func(*args) to run after t_secs seconds."""
        pass

    def callFromThread(self, func, *args):
        """Runs func(*args) in a thread. May be called from any thread."""
        pass

    def makeCallback(self):
        """Make an object for passing a result or exception between threads.

        The object has methods wait, success and failure. A call to wait
        from one thread blocks until another thread calls success or
        failure. The wait call accordingly either returns the success 
        argument or raises the failure argument."""
        pass
