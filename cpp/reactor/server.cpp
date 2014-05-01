#include <cstdio>
#include <unistd.h>
#include <serf/reactor/data_reader.h>
#include <serf/reactor/accept_reader.h>
#include <serf/reactor/connect_reader.h>
#include <serf/reactor/data_handler.h>
#include <serf/reactor/line_handler.h>
#include <serf/reactor/reactor.h>
#include <serf/debug.h>

namespace serf {
    class Quitter : public DataHandler {
    public:
        Quitter(Reactor* reactor) : reactor_(reactor) {}
        void handle(std::string const& data) {
            cout << "got input: " << data;
            reactor_->stop();
        }
    private:
        Reactor* reactor_;
    };

    class HelloWriter : public ReaderFactory {
    public:
        Reader* makeReader(std::string const& host, unsigned short port, int fd) {
            SHOW(fd);
            write(fd, "hello", 5);
            close(fd);
            return NULL;
        }
    };

    class LinePrinter : public DataHandler {
    public:
        LinePrinter(int fd, Reactor* reactor)
            : fd_(fd), count_(0), reactor_(reactor) {}
        ~LinePrinter() {
            SAY("LinePrinter deleted");
        }

        void handle(std::string const& line);

    private:
        int fd_;
        int count_;
        Reactor* reactor_;
    };

    class LinePrinterFactory : public ReaderFactory {
    public:
        LinePrinterFactory(Reactor* reactor) : reactor_(reactor) {}
        ~LinePrinterFactory() {
            SAY("LinePrinterFactory deleted");
        }

        Reader* makeReader(std::string const& host, unsigned short port, int fd) {
            LinePrinter* printer = new LinePrinter(fd, reactor_);
            LineHandler* line_handler = new LineHandler(printer);
            return new DataReader(fd, line_handler);
        }

    private:
        Reactor* reactor_;
    };

    void LinePrinter::handle(std::string const& line) {
        cout << count_ << "\t" << line;
        if (line.find("foo") != std::string::npos) {
            write(fd_, "you said foo!\n", 14);
        }
        if (line.find("connect") != std::string::npos) {
            reactor_->addReader(new ConnectReader("127.0.0.1", 6668, new LinePrinterFactory(reactor_)));
        }
        ++count_;
    }

}

using namespace serf;

int main(int argc, char* argv[])
{
    Reactor reactor;
    reactor.addReader(new AcceptReader(6667, new LinePrinterFactory(&reactor)));
    reactor.addReader(new DataReader(fileno(stdin), new Quitter(&reactor)));
    reactor.run();

    return 0;
}
