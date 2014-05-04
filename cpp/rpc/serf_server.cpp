#include <cstdio>
#include <csignal>
#include <unistd.h>

#include <serf/reactor/reactor.h>
#include <serf/reactor/accept_reader.h>
#include <serf/rpc/connection_factory.h>
#include <serf/rpc/message_router.h>
#include <serf/rpc/message_handler.h>

#include <serf/debug.h>

using namespace serf;

static MessageRouter* router_;

void handle_sigint(int a)
{
    router_->shutdown();
    signal(SIGINT, SIG_DFL);
}

int main(int argc, char* argv[])
{
    unsigned short port = 6504;
    Reactor reactor;
    MessageHandler mh;
    MessageRouter r(&mh, &reactor);
    mh.setRouter(&r);

    ConnectionFactory* f = new ConnectionFactory(&r, &reactor);
    reactor.addReader(new AcceptReader(port, f));

    router_ = &r;
    if (signal(SIGINT, handle_sigint) == SIG_ERR) {
        SAY("failed to install a signal handler");
        return 1;
    }

    SAY("listening on " << port);

    reactor.run();

    return 0;
}
