#include <cstdio>
#include <unistd.h>
#include <serf/reactor/data_reader.h>
#include <serf/reactor/accept_reader.h>
#include <serf/reactor/connect_reader.h>
#include <serf/reactor/data_handler.h>
#include <serf/reactor/line_handler.h>
#include <serf/reactor/reactor.h>
#include <serf/util/debug.h>

namespace serf {

    /** \brief Example DataHandler.
     *
     * When this receives any data at all, it tells the reactor to stop.
     */
    class Quitter : public DataHandler {
    public:
        Quitter(Reactor* reactor) : reactor_(reactor) {}
        void handle(std::string const& data) {
            std::cout << "got input: " << data;
            reactor_->stop();
        }
    private:
        Reactor* reactor_;
    };

    /** \brief Example ReaderFactory.
     *
     * This responds to any connection by sending the string "hello\n"
     * and then closing it. There is no need to create any Reader if
     * nothing needs to be read.
     */
    class HelloWriter : public ReaderFactory {
    public:
        Reader* makeReader(std::string const& host, unsigned short port, int fd) {
            SHOW(fd);
            write(fd, "hello\n", 6);
            close(fd);
            return NULL;
        }
    };

    /** \brief Example DataHandler.
     *
     * This prints each string it is passed. It will be a child DataHandler
     * of the LineHandler which defragments its input into newline terminated
     * lines.
     *
     * It also scans each line for a couple of key words and carries out
     * extra actions to add a bit of interest.
     */
    class LinePrinter : public DataHandler {
    public:
        LinePrinter(int fd, Reactor* reactor)
            : fd_(fd), count_(0), reactor_(reactor) {}

        void handle(std::string const& line);

    private:
        int fd_;
        int count_;
        Reactor* reactor_;
    };

    /** \brief Example ReaderFactory.
     *
     * This hooks sets up a chain DataReader -> LineHandler -> LinePrinter.
     */
    class LinePrinterFactory : public ReaderFactory {
    public:
        LinePrinterFactory(Reactor* reactor) : reactor_(reactor) {}

        Reader* makeReader(std::string const& host, unsigned short port, int fd) {
            LinePrinter* printer = new LinePrinter(fd, reactor_);
            LineHandler* line_handler = new LineHandler(printer);
            return new DataReader(fd, line_handler);
        }

    private:
        Reactor* reactor_;
    };

    /** \brief Handles data from a LineHandler.
     *
     * In addition to printing the line it scans for the string "foo"
     * and the string "connect". If it finds "foo" it sends a message back.
     * If it finds "connect" it makes a new outgoing connection with
     * an attached LinePrinter.
     */
    void LinePrinter::handle(std::string const& line) {
        std::cout << count_ << "\t" << line;
        if (line.find("foo") != std::string::npos) {
            write(fd_, "you said foo!\n", 14);
        }
        if (line.find("connect") != std::string::npos) {
            LinePrinterFactory* f = new LinePrinterFactory(reactor_);
            reactor_->addReader(new ConnectReader("127.0.0.1", 6668, f));
        }
        ++count_;
    }

    class HeartBeat : public Task {
    public:
        HeartBeat(int64_t first) : due_(first) {
        }
        ~HeartBeat() {
            SAY("HeartBeat stopped");
        }

        int64_t due() const {
            return due_;
        }

        bool run(int64_t now, Reactor* reactor) {
            SAY("bip.");
            due_ = now + Clock::seconds(3);
            return true;
        }

    private:
        int64_t due_;
    };

}

using namespace serf;

int main(int argc, char* argv[])
{
    Reactor reactor;
    reactor.addReader(new AcceptReader(6667, new LinePrinterFactory(&reactor)));
    reactor.addReader(new AcceptReader(6668, new HelloWriter));
    reactor.addReader(new DataReader(fileno(stdin), new Quitter(&reactor)));
    reactor.addTask(new HeartBeat(reactor.time()));
    reactor.run();

    return 0;
}
