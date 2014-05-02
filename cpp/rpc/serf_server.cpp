#include <cstdio>
#include <unistd.h>

#include <serf/reactor/reactor.h>
#include <serf/reactor/accept_reader.h>
#include <serf/rpc/connection_factory.h>
#include <serf/rpc/message_router.h>
#include <serf/rpc/message_handler.h>

#include <serf/debug.h>

using namespace serf;

int main(int argc, char* argv[])
{
    Reactor reactor;
    MessageHandler mh;
    MessageRouter r(&mh, &reactor);
    mh.setRouter(&r);

    ConnectionFactory* f = new ConnectionFactory(&r, &reactor);
    reactor.addReader(new AcceptReader(6669, f));

    reactor.run();

    return 0;
}
