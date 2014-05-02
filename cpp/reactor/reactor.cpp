#include <serf/reactor/reactor.h>

#include <cstddef>
#include <vector>
#include <sys/select.h>
#include <sys/time.h>
#include <serf/reactor/system_clock.h>
#include <serf/reactor/reader.h>

namespace serf {
    Reactor::Reactor(Clock* clock) : stop_(false), clock_(clock) {
    }
    Reactor::~Reactor() {
        ReaderMap::const_iterator i, e=readers_.end();
        for (i=readers_.begin(); i != e; ++i) {
            delete i->second;
        }
        size_t j, n = tasks_.size();
        for (j = 0; j < n; ++j) delete tasks_[j];
    }
    void Reactor::stop() {
        stop_ = true;
    }
    void Reactor::addReader(Reader* reader) {
        delete readers_[reader->fd()];
        readers_[reader->fd()] = reader;
    }
    void Reactor::removeReader(int fd) {
        delete readers_[fd];
        readers_.erase(fd);
    }
    int64_t Reactor::time() const {
        SystemClock system;
        return clock_ ? clock_->time() : system.time();
    }
    void Reactor::addTask(Task* task) {
        tasks_.push_back(task);
    }
    bool Reactor::removeTask(Task* task) {
        size_t j, n = tasks_.size();
        for (j = 0; j < n; ++j) {
            if (tasks_[j] == task) {
                delete task;
                tasks_[j] = NULL;
                return true;
            }
        }
        return false;
    }
    void Reactor::run() {
        while (!stop_) {
            fd_set desc_r, desc_w;
            FD_ZERO(&desc_r);
            FD_ZERO(&desc_w);
            ReaderMap::const_iterator i, e=readers_.end();
            int fd_max = 0;
            for (i=readers_.begin(); i != e; ++i) {
                int fd = i->first;
                FD_SET(fd, &desc_r);
                if (i->second->wantWrite()) FD_SET(fd, &desc_w);
                if (fd > fd_max) fd_max = fd;
            }

            // Find out when the next task is due.
            timeval timeout, *timeout_p = NULL;
            bool have_task = false;
            int64_t next = 0x7FFFFFFFFFFFFFFF;
            size_t j, n = tasks_.size();
            for (j = 0; j < n; ++j) {
                if (!tasks_[j]) continue;
                int64_t due = tasks_[j]->due();
                if (due < next) {
                    next = due;
                    have_task = true;
                }
            }
            if (have_task) {
                int64_t wait = next - time();
                if (wait < 0) wait = 0;
                timeout.tv_sec = wait / 1000000;
                timeout.tv_usec = wait % 1000000;
                timeout_p = &timeout;
            }

            select(fd_max + 1, &desc_r, &desc_w, NULL, timeout_p);

            // Make a list of ready descriptors. We don't want to be
            // iterating over readers_ while running them since they
            // might make changes to it.
            std::vector<int> ready;
            for (i=readers_.begin(); i != e; ++i) {
                int fd = i->first;
                if (FD_ISSET(fd, &desc_r) || FD_ISSET(fd, &desc_w)) {
                    ready.push_back(fd);
                }
            }

            for (size_t i=0, n=ready.size(); i < n && !stop_; ++i) {
                int fd = ready[i];
                ReaderMap::const_iterator p = readers_.find(fd);
                if (p != readers_.end()) {
                    p->second->run(this);
                }
            }

            // Execute each task and replace with NULL if one-time only.
            int64_t now = time();
            n = tasks_.size();
            for (j = 0; j < n; ++j) {
                Task* task = tasks_[j];
                if (!task) continue;
                if (task->due() <= now) {
                    bool keep = task->run(now, this);
                    if (!keep) {
                        delete task;
                        tasks_[j] = NULL;
                    }
                }
            }
            // Now get rid of all the NULLs from the task list.
            size_t k = 0;
            n = tasks_.size();
            for (j = 0; j < n; ++j) {
                if (tasks_[j]) {
                    tasks_[k] = tasks_[j];
                    ++k;
                }
            }
            tasks_.resize(k);
        }
    }

}
