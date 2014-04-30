#include <data_reader.h>
#include <accept_reader.h>
#include <data_handler.h>
#include <line_handler.h>
#include <reactor.h>
#include <debug.h>

namespace demo {
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
        Reader* makeReader(int fd) {
            SHOW(fd);
            write(fd, "hello", 5);
            close(fd);
            return NULL;
        }
    };

    class LinePrinter : public DataHandler {
    public:
        LinePrinter(int fd) : fd_(fd), count_(0) {}

        void handle(std::string const& line) {
            cout << count_ << "\t" << line;
            if (line.find("foo") != std::string::npos) {
                write(fd_, "you said foo!\n", 14);
            }
            ++count_;
        }
    private:
        int fd_;
        int count_;
    };

    class LinePrinterFactory : public ReaderFactory {
    public:
        Reader* makeReader(int fd) {
            LinePrinter* printer = new LinePrinter(fd);
            LineHandler* line_handler = new LineHandler(printer);
            return new DataReader(fd, line_handler);
        }
    };
}

using namespace demo;

int main(int argc, char* argv[])
{
    Reactor reactor;
    reactor.addReader(new AcceptReader(6666, new LinePrinterFactory));
    reactor.addReader(new DataReader(fileno(stdin), new Quitter(&reactor)));
    reactor.run();

    return 0;
}
