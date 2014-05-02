#ifndef TASK_HGUARD_
#define TASK_HGUARD_

#include <stdint.h>

namespace serf {
    class Reactor;

    /** \brief Interface for the clock required by a Reactor for scheduling.
     */
    class Clock
    {
    public:
        virtual ~Clock();

        /** \brief Implementer's version of the time now.
         *
         * The SystemClock returns time now in microseconds
         * since Jan 1 1970, UTC. A mock time implementation can return
         * anything it likes though it will be expected that the value
         * never decreases on successive calls.
         */
        virtual int64_t time() const = 0;

    public:
        static int64_t days(int64_t n);
        static int64_t seconds(int64_t n);
        static int64_t milliseconds(int64_t n);
    };

    /** \brief Interface for an item of work which may be scheduled by a
     *  Reactor.
     */
    class Task
    {
    public:
        virtual ~Task();

        /** \brief Implementation should return the time at which to run.
         *
         * For a task to be executed immediately the implementation
         * can return a time of 0.
         */
        virtual int64_t due() const = 0;

        /** \brief Implementation does whatever the Task is supposed to do.
         *
         * The now argument is the time at which run() is being called.
         * Tasks added to a Reactor will also be passed the reactor.
         *
         * The implementation can return true to indicate that this
         * task should be retained and run again when it is next due.
         *
         * For a simple one-time Task, both arguments may be ignored
         * and the Task should return false.
         */
        virtual bool run(int64_t now, Reactor* reactor) = 0;

		/** \brief Deletes the task. Implementation may override.
		 *
		 * Rather than deleting its Tasks the reactor calls dispose
		 * on them. If not overridden, dispose calls delete this.
		 * In cases where it is useful to keep a task around after
		 * it has been run, dispose can be overridden to do nothing.
		 */
		virtual void dispose();
    };
}

#endif // TASK_HGUARD_
