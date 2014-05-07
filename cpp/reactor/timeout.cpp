#include <sys/socket.h>
#undef dispose
#include <serf/reactor/task.h>
#include <serf/reactor/reactor.h>
#include <serf/reactor/data_reader.h>
#include <serf/reactor/data_handler.h>
#include <serf/reactor/system_clock.h>
#include <serf/debug.h>

namespace serf {
	class Timeout : public Task {
	public:
		Timeout(int64_t t) : t_(t), has_run(false) {}

		int64_t due() const {
			return t_;
		}

		bool run(int64_t now, Reactor* reactor) {
			reactor->stop();
			has_run = true;
			return false;
		}

		void dispose() {
		}

	private:
		int64_t t_;
	public:
		bool has_run;
	};

	class TestHandler : public DataHandler
	{
	public:
		TestHandler(std::string const& want, Reactor* reactor)
			: want_(want), reactor_(reactor) {}

		void handle(std::string const& data) {
			have_ += data;
			if (have_.size() >= want_.size()) reactor_->stop();
		}

		std::string const& have() {
			return have_;
		}
	private:
		std::string want_;
		std::string have_;
		Reactor* reactor_;
	};

}


using namespace serf;

int main(int argc, char* argv[]) {
	SystemClock clock;
	int sock[2];
	socketpair(AF_UNIX, SOCK_STREAM, 0, sock);

	Timeout t(clock.time() + Clock::seconds(1));
	Reactor r;
	TestHandler* th = new TestHandler("fred", &r);
	DataReader* d = new DataReader(sock[0], th);

	r.addTask(&t);
	r.addReader(d);
	send(sock[1], "fred", 4, 0);

	r.run();

	SHOW(th->have());

	return 0;
}
