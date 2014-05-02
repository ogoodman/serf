#ifndef REACTOR_HPP_
#define REACTOR_HPP_

#include <map>
#include <vector>
#include <serf/reactor/task.h>

namespace serf {
    class Reader;
    class Task;

    typedef std::map<int, Reader*> ReaderMap;

    /** \brief Holds a set of Readers, running each one when its associated
     *  file descriptor becomes readable.
     */
    class Reactor {
    public:
        Reactor(Clock* clock = NULL);

        /** \brief Reactor cleanup.
         *
         * Deletes any remaining readers.
         */
        ~Reactor();

        /** \brief Runs any reader whose file descriptor becomes ready.
         */
        void run();
        /** \brief Makes run() return. Must be called in the reactor loop.
         */
        void stop();

        /** \brief Add a Reader to the reactor.
         *
         * May be called before the reactor is started or from within the
         * reactor loop once it is running.
         * The Reactor takes ownership of the reader. Any existing Reader
         * owning the same descriptor is deleted.
         */
        void addReader(Reader* reader);

        /** \brief Remove the associated Reader.
         *
         * The Reader is deleted. It is up to the Reader to close the
         * file descriptor.
         */
        void removeReader(int fd);

        /** \brief Time according to the Reactor.
         */
        int64_t time() const;

        /** \brief Adds a task, to be run as soon as possible after it is due.
         *
         * The task will be deleted after it has run.
         */
        void addTask(Task* task);

        /** \brief Remove a task.
         *
         * Returns true if the task was found. If found the task is deleted.
         */
        bool removeTask(Task* task);

    private:
        ReaderMap readers_; // Readers are owned.
        bool stop_;
        Clock* clock_; // not owned.
        std::vector<Task*> tasks_; // owned.
    };
}

#endif
